import importlib
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

    # Validate modules have required attributes
    for module in modules:
        if not hasattr(module, "priority"):
            logger.error("Module '%s' missing required 'priority' attribute", module.__name__)
            raise AttributeError(
                f"Configuration module {module.__name__} missing required 'priority' attribute"
            )
        if not hasattr(module, "configure"):
            logger.error("Module '%s' missing required 'configure' method", module.__name__)
            raise AttributeError(
                f"Configuration module {module.__name__} missing required 'configure' method"
            )

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
            module.configure(context)
        except Exception as e:
            logger.error("Error configuring context with module '%s': %s", 
                        module.__name__, str(e))
            raise

    logger.info("Successfully initialized InjectyContext with %d modules", len(modules))
    return context


def _priority_sort_key(n):
    """
    Sort key function that returns the priority of an object.

    Args:
        n: Object with a priority attribute

    Returns:
        The priority value
    """
    return n.priority
