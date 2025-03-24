import importlib
import pkgutil
from dataclasses import dataclass, field
from typing import (
    Dict,
    Type,
    Set,
    List,
    Callable,
    Optional,
    Any,
    TypeVar,
    get_type_hints,
)

_CONFIG_MODULE_PREFIX = "injecty_config"
T = TypeVar("T")


@dataclass
class InjectyContext:
    """
    Context for managing implementations of abstract base classes.
    
    The InjectyContext maintains a registry of implementation classes for base classes
    and provides methods to register, deregister, and retrieve implementations.
    """
    impls: Dict[Type[T], Set[Type[T]]] = field(default_factory=dict)

    def register_impl(
        self, base: Type[T], impl: Type[T], check_type: bool = True
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
            raise TypeError(impl)
        impls = self.impls.get(base)
        if not impls:
            impls = self.impls[base] = set()
        if impl in impls:
            return False
        impls.add(impl)
        return True

    def register_impls(
        self, base: Type[T], impls: List[Type[T]], check_type: bool = True
    ) -> bool:
        """
        Register multiple implementation classes for a base class.
        
        Args:
            base: The base class
            impls: List of implementation classes
            check_type: If True, verify that each impl is a subclass of base
            
        Returns:
            True if all implementations were newly registered, False if any were already registered
        """
        result = True
        for impl in impls:
            result &= self.register_impl(base, impl, check_type)
        return result

    def deregister_impl(self, base: Type[T], impl: Type[T]) -> bool:
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
                return True
        return False

    def get_impls(
        self,
        base: Type[T],
        sort_key: Optional[Callable[[Type[T]], Any]] = None,
        reverse: bool = False,
        permit_no_impl: bool = False,
    ) -> List[Type[T]]:
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
                return []
            raise ValueError(f"no_implementation_for:{base}")
        result = list(impls)
        if sort_key is None:
            priority = get_type_hints(base).get("priority", None)
            priority = getattr(priority, "__name__", priority)
            if priority == "int":
                sort_key = _priority_sort_key
                reverse = True
        if sort_key:
            # noinspection PyTypeChecker
            result.sort(key=sort_key, reverse=reverse)
        return result

    def get_default_impl(
        self,
        base: Type[T],
        sort_key: Optional[Callable[[Type[T]], Any]] = None,
        reverse: bool = False,
        permit_no_impl: bool = False,
    ) -> Optional[Type[T]]:
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
            return impls[0]
        return None

    # pylint: disable=R0913
    def get_instances(
        self,
        base: Type[T],
        sort_key: Optional[Callable[[Type[T]], Any]] = None,
        reverse: bool = False,
        kwargs: Optional[Dict] = None,
        permit_no_impl: bool = False,
    ) -> List[T]:
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
        result = [impl(**kwargs) for impl in impls]
        return result

    # pylint: disable=R0913
    def get_new_default_instance(
        self,
        base: Type[T],
        sort_key: Optional[Callable[[Type[T]], Any]] = None,
        reverse: bool = False,
        kwargs: Optional[Dict] = None,
        permit_no_impl: bool = False,
    ) -> Optional[T]:
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
            result = impls[0](**kwargs)
            return result
        return None


def get_config_modules(config_module_prefix: str = _CONFIG_MODULE_PREFIX) -> List:
    """
    Discover and load all configuration modules matching the specified prefix.
    
    Configuration modules are expected to have:
    1. A name starting with the specified prefix (default: 'injecty_config')
    2. A 'priority' attribute (integer)
    3. A 'configure' function that accepts an InjectyContext
    
    Returns:
        List of loaded configuration modules, sorted by priority (ascending)
    """
    module_info = (
        m for m in pkgutil.iter_modules() if m.name.startswith(config_module_prefix)
    )
    modules = [importlib.import_module(m.name) for m in module_info]
    
    # Validate modules have required attributes
    for module in modules:
        if not hasattr(module, "priority"):
            raise AttributeError(f"Configuration module {module.__name__} missing required 'priority' attribute")
        if not hasattr(module, "configure"):
            raise AttributeError(f"Configuration module {module.__name__} missing required 'configure' method")
    
    # Sort modules by priority (lower priority modules are processed first)
    modules.sort(key=lambda m: m.priority, reverse=False)
    return modules


def create_injecty_context(config_module_prefix: str = _CONFIG_MODULE_PREFIX):
    """
    Create and initialize a new InjectyContext with all discovered configuration modules.
    
    Args:
        config_module_prefix: Prefix for configuration module discovery
        
    Returns:
        Initialized InjectyContext
    """
    context = InjectyContext()
    modules = get_config_modules(config_module_prefix)
    
    for module in modules:
        module.configure(context)
    
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
