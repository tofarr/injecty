from types import ModuleType
from typing import Any, Callable, TypeVar

T = TypeVar("T")

from injecty.injecty_context import (
    InjectyContext,
    create_injecty_context,
    get_config_modules,
    T,
)

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
        _DEFAULT_CONTEXT = create_injecty_context()
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
    context = get_default_injecty_context()
    impls = context.get_impls(base, sort_key, reverse, permit_no_impl)
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
    context = get_default_injecty_context()
    instances = context.get_instances(base, sort_key, reverse, kwargs, permit_no_impl)
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
    context = get_default_injecty_context()
    impl_ = context.get_default_impl(base, sort_key, reverse, permit_no_impl)
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
    context = get_default_injecty_context()
    instance = context.get_new_default_instance(
        base, sort_key, reverse, kwargs, permit_no_impl
    )
    return instance
