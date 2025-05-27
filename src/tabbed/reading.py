"""

"""
from __future__ import annotations
from typing import Dict, IO, List, Optional

from tabbed.sniffing import Header, Sniffer
from tabbed.utils.mixins import ReprMixin


class _HeaderDescriptor:
    """ """

    def __init__(self, storage_name: str = '_header'):
        """ """

        self.storage_name = storage_name

    def _from_integer(self, instance: Reader, value: int):
        """Creates a Header instance from an integer index value."""

        sniff = Sniffer(instance.infile, start=value, amount=1)
        string = sniff.sample[0]

        return Header(value, sniff.rows[0], string)

    def _from_list(self, instance: Reader, value: List[str]):
        """Creates a Header instance from a list of string names."""

        expected = len(instance.sniffer.rows[-1])
        if len(value) != expected:
            msg = (
                    f'Length of provided header names = {len(value)} does '
                    f'not match the number of sniffed columns = {expected}'
                )
            raise ValueError(msg)

        return Header(None, value, None)

    def _from_kwargs(self, instance: Reader, value: Dict[str, int]):
        """Creates a Header instance by Sniffer's header method."""

        return instance.sniffer.header(**value)

    def __get__(self, instance, owner):
        """Returns the header from the Reader instance."""

        return getattr(instance, self.storage_name)

    def __set__(self, instance, value):
        """ """

        if not isinstance(value, (int, list, dict)):
            msg = (
                    "A header may be set by integer line number, list of "
                    "header names or a dict of kwargs for sniffer's header "
                    f"method but not type {type(value)}."
                    )
            raise ValueError(msg)

        if isinstance(value, int):
            header = self._from_integer(instance, value)
        if isinstance(value, list):
            header = self._from_list(instance, value)
        if isinstance(value, dict):
            header = self._from_kwargs(instance, value)

        setattr(instance, self.storage_name, header)



class Reader(ReprMixin):
    """

    """

    header = _HeaderDescriptor()

    def __init__(self, infile:IO[str], **sniffing_kwargs):
        """ """

        self.infile = infile
        self._sniffer = Sniffer(infile, **sniffing_kwargs)
        self._header = self._sniffer.header()
        self._tabs = []
        self.errors = None


    @property
    def sniffer(self):
        """Intercept any change to the sniffer and update the header if needed.

        This applies to sniffer attr access or set so its overkill but it avoids
        monkey patching
        """

        if self._header.line is not None:
            print('updating header')
            self._header = self._sniffer.header()
        return self._sniffer


if __name__ == '__main__':

    fp = '/home/matt/python/nri/tabbed/__data__/mouse_annotations.txt'

    infile = open(fp, 'r')
    reader = Reader(infile)

    # header changing
    #
    # does changing sniffer change this instances sniffer

