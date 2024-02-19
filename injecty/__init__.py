from typing import Type, Optional, Callable, Any, List

from injecty.injecty_context import InjectyContext, create_injecty_context, T

_DEFAULT_CONTEXT = None


def get_default_context():
    global _DEFAULT_CONTEXT
    if _DEFAULT_CONTEXT is None:
        _DEFAULT_CONTEXT = create_injecty_context()
    return _DEFAULT_CONTEXT


def get_impls(
    base: Type[T],
    sort_key: Optional[Callable[[Type[T]], Any]] = None,
    reverse: bool = False,
) -> List[Type]:
    context = get_default_context()
    impls = context.get_impls(base, sort_key, reverse)
    return impls


def get_instances(base: Type[T]) -> List[T]:
    context = get_default_context()
    impls = context.get_instances(base)
    return impls


def get_default_impl(
    base: Type[T],
    sort_key: Optional[Callable[[Type[T]], Any]] = None,
    reverse: bool = False,
) -> Type:
    context = get_default_context()
    impl = context.get_default_impl(base, sort_key, reverse)
    return impl


def get_default_instance(
    base: Type[T],
    sort_key: Optional[Callable[[Type[T]], Any]] = None,
    reverse: bool = False,
) -> Type:
    context = get_default_context()
    impl = context.get_default_impl(base, sort_key, reverse)
    return impl
