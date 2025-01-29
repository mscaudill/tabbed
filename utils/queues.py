"""A module for constructing a queue-like data structures."""

from collections import abc
from typing import Any, List


class ListFIFO:
    """A first-in-first out queue-like data structure that collects lists.

    Attributes:
        queue:
            A list of lists that have been collected via the 'put' method and
            may be returned by 'get' method.
        chunksize:
            The number of lists that are dequeued by each 'get' call.

    Example:
        >>> fifo = ListFIFO(chunksize=4)
        >>> # put some lists into fifo
        >>> _ = [fifo.put(list(range(i, 5+i))) for i in range(10)]
        >>> # ask if fifo is full
        >>> fifo.full()
        True
        >>> # iterate chunksize items from fifo
        >>> chunk = 0
        >>> while not fifo.empty():
        ...     print(chunk, fifo.get())
        ...     chunk += 1
        ... #doctest: +NORMALIZE_WHITESPACE
        0 [[0, 1, 2, 3, 4],
            [1, 2, 3, 4, 5],
            [2, 3, 4, 5, 6],
            [3, 4, 5, 6, 7]]
        1 [[4, 5, 6, 7, 8],
            [5, 6, 7, 8, 9],
            [6, 7, 8, 9, 10],
            [7, 8, 9, 10, 11]]
        2 [[8, 9, 10, 11, 12],
            [9, 10, 11, 12, 13]]
    """

    def __init__(self, chunksize: int) -> None:
        """Initialize this FIFO with and empty queue."""

        self.queue: List[List[Any]] = []
        self.chunksize = chunksize

    def qsize(self) -> int:
        """Returns the number of lists in the queue."""

        return len(self.queue)

    def full(self) -> bool:
        """Returns True if the number of list in queue is at least chunksize."""

        return self.qsize() >= self.chunksize

    def empty(self) -> bool:
        """Returns True if the number of list in queue is 0."""

        return self.qsize() == 0

    def put(self, x: List[Any] | List[List[Any]]) -> None:
        """Adds a list of list of lists to the queue.

        Args:
            A list or list of lists to append or extend to this FIFO's queue.

        Returns:
            None
        """

        addition = [x] if not isinstance(x[0], abc.Sequence) else x
        self.queue.extend(addition)

    def get(self) -> List[List[Any]]:
        """Returns a chunksize list of lists."""

        result = self.queue[: self.chunksize]
        self.queue = self.queue[self.chunksize :]

        return result


if __name__ == '__main__':

    import doctest

    doctest.testmod()
