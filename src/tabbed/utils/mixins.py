"""Mixins for Tabbed's Classes"""

import inspect
import reprlib
from typing import List


class ReprMixin:
    """Model mixin for pretty echo & str representations.

    This Mixin's representations exclude protected and private attributes.
    """

    def _attributes(self) -> List[str]:
        """Returns a list of 'name: value' strings for each attribute."""

        attrs = {k: v for k, v in vars(self).items() if not k.startswith('_')}
        return [f'{k}: {reprlib.repr(v)}' for k, v in attrs.items()]

    def _properties(self) -> List[str]:
        """Returns a list of 'name: value' strings for each property."""

        def isprop(p):
            return isinstance(p, property)

        props = dict(inspect.getmembers(type(self), isprop))
        props = {k: getattr(self, k) for k in props}
        return [f'{k}: {reprlib.repr(v)}' for k, v in props.items()]

    def _methods(self) -> List[str]:
        """Returns a list of method string names."""

        methods = inspect.getmembers(self, inspect.ismethod)
        return [name for name, _ in methods if not name.startswith('_')]

    def __repr__(self) -> str:
        """Returns the __init__'s signature as the echo representation."""

        # build a signature and get its args and class name
        signature = inspect.signature(self.__init__)  # type: ignore[misc]
        args = str(signature)
        cls_name = type(self).__name__
        return f'{cls_name}{args}'

    def __str__(self) -> str:
        """Returns this instances print representation."""

        # fetch instance name, attrs and methods strings
        cls_name = type(self).__name__
        attrs = self._attributes()
        props = self._properties()
        methods = self._methods()

        # make a help msg
        help_msg = f'Type help({cls_name}) for full documentation'
        # construct print string
        msg = [
            f'{cls_name}',
            '--- Attributes ---',
            '\n'.join(attrs),
            '--- Properties ---',
            '\n'.join(props),
            '--- Methods ---',
            '\n'.join(methods),
            help_msg,
        ]

        return '\n'.join(msg)
