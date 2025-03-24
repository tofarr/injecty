import logging
from types import ModuleType
from typing import Any, Callable, TypeVar

T = TypeVar("T")

from injecty.injecty_context import (
    InjectyContext,
    create_injecty_context,
    get_config_modules,
    T,
)

from injecty.logging_config import configure_logging, get_logger

# Configure logger
logger = logging.getLogger(__name__)

_DEFAULT_CONTEXT = None


def get_default_injecty_context() -> InjectyContext:
    """
    Get or create the default InjectyContext.

    The default context is created lazily on first access and cached for subsequent calls.

    Returns:
        InjectyContext: The default context instance
    """
    # pylint: disable=W0603
    global _DEFAULT_CONTEXT
    if _DEFAULT_CONTEXT is None:
        logger.info("Initializing default InjectyContext")
        _DEFAULT_CONTEXT = create_injecty_context()
        logger.debug("Default InjectyContext initialized")
    else:
        logger.debug("Using existing default InjectyContext")
    return _DEFAULT_CONTEXT


def get_impls(
    base: type[T],
    sort_key: Callable[[type[T]], Any] | None = None,
    reverse: bool = False,
    permit_no_impl: bool = False,
) -> list[type[T]]:
    """
    Get all registered implementations of the specified base class.

    Args:
        base: The base class to find implementations for
        sort_key: Optional function to sort implementations
        reverse: Whether to reverse the sort order
        permit_no_impl: If True, returns empty list when no implementations found;
                        if False, raises ValueError

    Returns:
        List of implementation classes

    Raises:
        ValueError: If no implementations found and permit_no_impl is False
    """
    logger.debug("Getting implementations for %s", base.__name__)
    context = get_default_injecty_context()
    impls = context.get_impls(base, sort_key, reverse, permit_no_impl)
    logger.debug("Found %d implementations for %s", len(impls), base.__name__)
    return impls


def get_instances(
    base: type[T],
    sort_key: Callable[[type[T]], Any] | None = None,
    reverse: bool = False,
    kwargs: dict | None = None,
    permit_no_impl: bool = False,
) -> list[T]:
    """
    Get instances of all registered implementations of the specified base class.

    Args:
        base: The base class to find implementations for
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
    logger.debug("Getting instances for %s", base.__name__)
    context = get_default_injecty_context()
    instances = context.get_instances(base, sort_key, reverse, kwargs, permit_no_impl)
    logger.debug("Created %d instances for %s", len(instances), base.__name__)
    return instances


def get_default_impl(
    base: type[T],
    sort_key: Callable[[type[T]], Any] | None = None,
    reverse: bool = False,
    permit_no_impl: bool = False,
) -> type[T] | None:
    """
    Get the default implementation of the specified base class.

    The default implementation is the first one after sorting.

    Args:
        base: The base class to find implementations for
        sort_key: Optional function to sort implementations
        reverse: Whether to reverse the sort order
        permit_no_impl: If True, returns None when no implementations found;
                        if False, raises ValueError

    Returns:
        The default implementation class

    Raises:
        ValueError: If no implementations found and permit_no_impl is False
    """
    logger.debug("Getting default implementation for %s", base.__name__)
    context = get_default_injecty_context()
    impl_ = context.get_default_impl(base, sort_key, reverse, permit_no_impl)
    
    if impl_:
        logger.debug("Default implementation for %s is %s", base.__name__, impl_.__name__)
    else:
        logger.debug("No default implementation found for %s", base.__name__)
        
    return impl_


def get_new_default_instance(
    base: type[T],
    sort_key: Callable[[type[T]], Any] | None = None,
    reverse: bool = False,
    kwargs: dict | None = None,
    permit_no_impl: bool = False,
) -> T | None:
    """
    Create a new instance of the default implementation of the specified base class.

    Args:
        base: The base class to find implementations for
        sort_key: Optional function to sort implementations
        reverse: Whether to reverse the sort order
        kwargs: Optional dictionary of keyword arguments to pass to constructor
        permit_no_impl: If True, returns None when no implementations found;
                        if False, raises ValueError

    Returns:
        A new instance of the default implementation

    Raises:
        ValueError: If no implementations found and permit_no_impl is False
    """
    logger.debug("Creating new default instance for %s", base.__name__)
    context = get_default_injecty_context()
    
    try:
        instance = context.get_new_default_instance(
            base, sort_key, reverse, kwargs, permit_no_impl
        )
        
        if instance:
            logger.debug("Created new instance of %s (type: %s)", 
                       base.__name__, instance.__class__.__name__)
        else:
            logger.debug("No instance created for %s (no implementation available)", base.__name__)
            
        return instance
    except Exception as e:
        logger.error("Failed to create instance for %s: %s", base.__name__, str(e))
        raise
