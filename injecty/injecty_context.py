import importlib
import inspect
import logging
import pkgutil
from dataclasses import dataclass, field
from types import ModuleType
from typing import (
    Any,
    Callable,
    TypeVar,
    get_type_hints,
)

# Configure logger
logger = logging.getLogger(__name__)

_CONFIG_MODULE_PREFIX = "injecty_config"
T = TypeVar("T")


@dataclass
class InjectyContext:
    """
    Context for managing implementations of abstract base classes.

    The InjectyContext maintains a registry of implementation classes for base classes
    and provides methods to register, deregister, and retrieve implementations.
    """

    impls: dict[type[T], set[type[T]]] = field(default_factory=dict)

    def register_impl(
        self, base: type[T], impl: type[T], check_type: bool = True
    ) -> bool:
        """
        Register an implementation class for a base class.

        Args:
            base: The base class
            impl: The implementation class
            check_type: If True, verify that impl is a subclass of base

        Returns:
            True if the implementation was newly registered, False if it was already registered

        Raises:
            TypeError: If check_type is True and impl is not a subclass of base
        """
        if check_type and not issubclass(impl, base):
            logger.error("Type check failed: %s is not a subclass of %s", impl.__name__, base.__name__)
            raise TypeError(impl)
        
        impls = self.impls.get(base)
        if not impls:
            impls = self.impls[base] = set()
            logger.debug("Created new implementation set for base class %s", base.__name__)
            
        if impl in impls:
            logger.debug("Implementation %s already registered for %s", impl.__name__, base.__name__)
            return False
            
        impls.add(impl)
        logger.info("Registered implementation %s for base class %s", impl.__name__, base.__name__)
        return True

    def register_impls(
        self, base: type[T], impls: list[type[T]], check_type: bool = True
    ) -> bool:
        """
        Register multiple implementation classes for a base class.

        Args:
            base: The base class
            impls: list of implementation classes
            check_type: If True, verify that each impl is a subclass of base

        Returns:
            True if all implementations were newly registered, False if any were already registered
        """
        logger.debug("Registering %d implementations for base class %s", len(impls), base.__name__)
        result = True
        for impl in impls:
            result &= self.register_impl(base, impl, check_type)
        
        if result:
            logger.info("Successfully registered all %d implementations for %s", len(impls), base.__name__)
        else:
            logger.info("Some implementations for %s were already registered", base.__name__)
        return result

    def deregister_impl(self, base: type[T], impl: type[T]) -> bool:
        """
        Deregister an implementation class for a base class.

        Args:
            base: The base class
            impl: The implementation class to deregister

        Returns:
            True if the implementation was deregistered, False if it wasn't registered
        """
        impls = self.impls.get(base)
        if impls:
            if impl in impls:
                impls.remove(impl)
                logger.info("Deregistered implementation %s from base class %s", impl.__name__, base.__name__)
                return True
            else:
                logger.debug("Implementation %s not found for base class %s", impl.__name__, base.__name__)
        else:
            logger.debug("No implementations registered for base class %s", base.__name__)
        return False

    def get_impls(
        self,
        base: type[T],
        sort_key: Callable[[type[T]], Any] | None = None,
        reverse: bool = False,
        permit_no_impl: bool = False,
    ) -> list[type[T]]:
        """
        Get all registered implementations of a base class.

        If no explicit sort_key is provided and the base class has an integer 'priority' attribute,
        implementations will be sorted by priority in descending order.

        Args:
            base: The base class
            sort_key: Optional function to sort implementations
            reverse: Whether to reverse the sort order
            permit_no_impl: If True, returns empty list when no implementations found;
                            if False, raises ValueError

        Returns:
            List of implementation classes

        Raises:
            ValueError: If no implementations found and permit_no_impl is False
        """
        impls = self.impls.get(base)
        if not impls:
            if permit_no_impl:
                logger.debug("No implementations found for %s (permitted)", base.__name__)
                return []
            logger.warning("No implementations found for %s", base.__name__)
            raise ValueError(f"no_implementation_for:{base}")
            
        result = list(impls)
        logger.debug("Found %d implementations for %s", len(result), base.__name__)
        
        if sort_key is None:
            priority = get_type_hints(base).get("priority", None)
            priority = getattr(priority, "__name__", priority)
            if priority == "int":
                logger.debug("Using priority-based sorting for %s implementations", base.__name__)
                sort_key = _priority_sort_key
                reverse = True
                
        if sort_key:
            # noinspection PyTypeChecker
            result.sort(key=sort_key, reverse=reverse)
            logger.debug("Sorted %d implementations for %s", len(result), base.__name__)
            
        return result

    def get_default_impl(
        self,
        base: type[T],
        sort_key: Callable[[type[T]], Any] | None = None,
        reverse: bool = False,
        permit_no_impl: bool = False,
    ) -> type[T] | None:
        """
        Get the default implementation of a base class.

        The default implementation is the first one after sorting.

        Args:
            base: The base class
            sort_key: Optional function to sort implementations
            reverse: Whether to reverse the sort order
            permit_no_impl: If True, returns None when no implementations found;
                            if False, raises ValueError

        Returns:
            The default implementation class, or None if no implementations found and permit_no_impl is True

        Raises:
            ValueError: If no implementations found and permit_no_impl is False
        """
        impls = self.get_impls(base, sort_key, reverse, permit_no_impl)
        if impls:
            default_impl = impls[0]
            logger.debug("Selected default implementation %s for %s", default_impl.__name__, base.__name__)
            return default_impl
        logger.debug("No default implementation available for %s", base.__name__)
        return None

    # pylint: disable=R0913
    def get_instances(
        self,
        base: type[T],
        sort_key: Callable[[type[T]], Any] | None = None,
        reverse: bool = False,
        kwargs: dict | None = None,
        permit_no_impl: bool = False,
    ) -> list[T]:
        """
        Get instances of all registered implementations of a base class.

        Args:
            base: The base class
            sort_key: Optional function to sort implementations
            reverse: Whether to reverse the sort order
            kwargs: Optional dictionary of keyword arguments to pass to constructors
            permit_no_impl: If True, returns empty list when no implementations found;
                            if False, raises ValueError

        Returns:
            List of instances of the implementation classes

        Raises:
            ValueError: If no implementations found and permit_no_impl is False
        """
        if kwargs is None:
            kwargs = {}
        impls = self.get_impls(base, sort_key, reverse, permit_no_impl)
        
        logger.debug("Creating instances for %d implementations of %s", len(impls), base.__name__)
        result = []
        for impl in impls:
            try:
                instance = impl(**kwargs)
                result.append(instance)
                logger.debug("Created instance of %s", impl.__name__)
            except Exception as e:
                logger.error("Failed to create instance of %s: %s", impl.__name__, str(e))
                raise
                
        return result

    # pylint: disable=R0913
    def get_new_default_instance(
        self,
        base: type[T],
        sort_key: Callable[[type[T]], Any] | None = None,
        reverse: bool = False,
        kwargs: dict | None = None,
        permit_no_impl: bool = False,
    ) -> T | None:
        """
        Create a new instance of the default implementation of a base class.

        Args:
            base: The base class
            sort_key: Optional function to sort implementations
            reverse: Whether to reverse the sort order
            kwargs: Optional dictionary of keyword arguments to pass to constructor
            permit_no_impl: If True, returns None when no implementations found;
                            if False, raises ValueError

        Returns:
            A new instance of the default implementation, or None if no implementations found and permit_no_impl is True

        Raises:
            ValueError: If no implementations found and permit_no_impl is False
        """
        if kwargs is None:
            kwargs = {}
        impls = self.get_impls(base, sort_key, reverse, permit_no_impl)
        if impls:
            default_impl = impls[0]
            try:
                logger.debug("Creating instance of default implementation %s for %s", 
                           default_impl.__name__, base.__name__)
                result = default_impl(**kwargs)
                return result
            except Exception as e:
                logger.error("Failed to create instance of %s: %s", default_impl.__name__, str(e))
                raise
        logger.debug("No default instance available for %s", base.__name__)
        return None


def get_config_modules(
    config_module_prefix: str = _CONFIG_MODULE_PREFIX,
) -> list[ModuleType]:
    """
    Discover and load all configuration modules matching the specified prefix.

    Configuration modules are expected to have:
    1. A name starting with the specified prefix (default: 'injecty_config')
    2. A 'priority' attribute (integer)
    3. A 'configure' function that accepts an InjectyContext

    Returns:
        List of loaded configuration modules, sorted by priority (ascending)
    """
    logger.debug("Discovering configuration modules with prefix '%s'", config_module_prefix)
    
    module_info = (
        m for m in pkgutil.iter_modules() if m.name.startswith(config_module_prefix)
    )
    
    modules = []
    for m in module_info:
        try:
            logger.debug("Loading configuration module '%s'", m.name)
            module = importlib.import_module(m.name)
            modules.append(module)
        except ImportError as e:
            logger.error("Failed to import module '%s': %s", m.name, str(e))
            raise

    logger.info("Discovered %d configuration modules", len(modules))

    # Validate all modules
    for module in modules:
        try:
            logger.debug("Validating configuration module '%s'", module.__name__)
            validate_config_module(module)
        except (AttributeError, TypeError, ValueError) as e:
            logger.error("Validation failed for module '%s': %s", module.__name__, str(e))
            raise

    # Sort modules by priority (lower priority modules are processed first)
    modules.sort(key=lambda m: m.priority, reverse=False)
    logger.debug("Sorted %d configuration modules by priority", len(modules))
    
    return modules


def create_injecty_context(
    config_module_prefix: str = _CONFIG_MODULE_PREFIX,
) -> InjectyContext:
    """
    Create and initialize a new InjectyContext with all discovered configuration modules.

    Args:
        config_module_prefix: Prefix for configuration module discovery

    Returns:
        Initialized InjectyContext
    """
    logger.info("Creating new InjectyContext with prefix '%s'", config_module_prefix)
    context = InjectyContext()
    
    modules = get_config_modules(config_module_prefix)
    logger.debug("Configuring InjectyContext with %d modules", len(modules))

    for module in modules:
        try:
            logger.debug("Configuring context with module '%s' (priority: %d)", 
                       module.__name__, module.priority)
            
            # Validate the module again before configuring (in case it was modified)
            validate_config_module(module)
            
            # Call the configure method
            result = module.configure(context)
            
            # Validate the result of configure (should be None)
            if result is not None:
                logger.warning(
                    "Module '%s' 'configure' method returned a value (%s) when None was expected",
                    module.__name__, type(result).__name__
                )
                
        except Exception as e:
            logger.error("Error configuring context with module '%s': %s", 
                        module.__name__, str(e))
            raise

    logger.info("Successfully initialized InjectyContext with %d modules", len(modules))
    return context


def validate_config_module(module: ModuleType) -> None:
    """
    Validate that a module meets the requirements to be a configuration module.
    
    Configuration modules must have:
    1. A 'priority' attribute that is an integer
    2. A 'configure' function that accepts an InjectyContext parameter
    
    Args:
        module: The module to validate
        
    Raises:
        AttributeError: If the module is missing required attributes
        TypeError: If the attributes are of the wrong type
        ValueError: If the attributes have invalid values
    """
    module_name = module.__name__
    
    # Check for priority attribute
    if not hasattr(module, "priority"):
        logger.error("Module '%s' missing required 'priority' attribute", module_name)
        raise AttributeError(
            f"Configuration module {module_name} missing required 'priority' attribute"
        )
    
    # Validate priority is an integer
    if not isinstance(module.priority, int):
        logger.error(
            "Module '%s' has invalid 'priority' attribute: expected int, got %s",
            module_name, type(module.priority).__name__
        )
        raise TypeError(
            f"Configuration module {module_name} has invalid 'priority' attribute: "
            f"expected int, got {type(module.priority).__name__}"
        )
    
    # Check for configure function
    if not hasattr(module, "configure"):
        logger.error("Module '%s' missing required 'configure' method", module_name)
        raise AttributeError(
            f"Configuration module {module_name} missing required 'configure' method"
        )
    
    # Validate configure is callable
    if not callable(module.configure):
        logger.error(
            "Module '%s' has invalid 'configure' attribute: expected callable, got %s",
            module_name, type(module.configure).__name__
        )
        raise TypeError(
            f"Configuration module {module_name} has invalid 'configure' attribute: "
            f"expected callable, got {type(module.configure).__name__}"
        )
    
    # Validate configure function signature
    sig = inspect.signature(module.configure)
    parameters = list(sig.parameters.values())
    
    # Configure should have at least one parameter (for the context)
    if len(parameters) < 1:
        logger.error(
            "Module '%s' has invalid 'configure' method: expected at least 1 parameter, got %d",
            module_name, len(parameters)
        )
        raise ValueError(
            f"Configuration module {module_name} has invalid 'configure' method: "
            f"expected at least 1 parameter, got {len(parameters)}"
        )
    
    # First parameter should accept InjectyContext
    # We can't strictly type check here due to potential circular imports,
    # but we can check if the parameter name suggests it's a context
    first_param = parameters[0]
    if first_param.name not in ('context', 'ctx', 'injecty_context'):
        logger.warning(
            "Module '%s' 'configure' method's first parameter name '%s' doesn't suggest it's a context",
            module_name, first_param.name
        )


def _priority_sort_key(n):
    """
    Sort key function that returns the priority of an object.

    Args:
        n: Object with a priority attribute

    Returns:
        The priority value
    """
    return n.priority
