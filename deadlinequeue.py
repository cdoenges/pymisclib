#!/usr/bin/env python3
# vim ts=4,fileencoding=utf-8
# SPDX-License-Identifier: Apache-2.0
# SPDXID: pymisclib-1
# PackageCopyrightText: © Copyright 2012-2022 by Christian Dönges <cd@platypus-projects.de>
# PackageDownloadLocation: None
# PackageHomePage: https://github.com/cdoenges/pymisclib
# PackageName: pymisclib
# PackageOriginator: Originator: Platypus Projects GmbH
# PackageSourceInfo: <text>uses pymisclib from https://github.com/cdoenges/pymisclib.</text>
# PackageSupplier: Christian Dönges (cd@platypus-projects.de)
# PackageVersion: 1.0.0
"""A socket used to send and receive  message chunks over a TCP connection.


    :LICENSE:
    © Copyright 2017 by Christian Dönges <cd@platypus-projects.de>

    Licensed under the Apache License, Version 2.0 (the "License"); you may
    not use this file except in compliance with the License. You may obtain a
    copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.


    If you need another license, contact the author to discuss terms.
"""

import heapq
import logging
import sys
import threading
import time


class DeadlineQueue:
    """A queue of items sorted by the time they are due.

    An item is due when the deadline expires.

    To add an element that will expire immediately, use timedue==0.

    The queue consists of tuples of the form (deadline, idx, item). The
    lowest deadline is sorted to the front of the queue.

    The deadline is based on time.perf_counter().

    The role of the idx variable is to properly order items with the same
    priority level. By keeping a constantly increasing idx, the items
    will be sorted according to the order in which they were inserted.
    """

    def __init__(self, logger=None):
        """Initialize the instance.

        :Parameters:
        logger -- The logger used by the instance. If no logger is specified,
        a default logger will be used.
        """
        # A counter used to create unique idx numbers used for sorting."""
        self._count = 0
        # A condition used to lock access to the queue.
        self._cv = threading.Condition()
        # The logger used to output information.
        if logger is None:
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = logger
        # A list of items.
        self._queue = []

    def __repr__(self):
        """Return a human-readable string representation of the instance."""
        s = '['
        not_first = False
        with self._cv:
            for item in self._queue:
                if not_first:
                    s = s + f', {item[2]} @ {item[0]}'
                else:
                    not_first = True
                    s = s + f'{item[2]} @ {item[0]}'
        s = s + ']'
        return s

    def put(self, item_tuple):
        """Place a tuple in the queue.

        The item tuple is (deadline, item). A lower deadline is sorted earlier
        in the queue.
        """
        deadline = item_tuple[0]
        item = item_tuple[1]
        # Lock access to the queue by grabbing the condition.
        with self._cv:
            heapq.heappush(self._queue, (deadline, self._count, item))
            self._logger.debug(
                'put(#%u - %s @ %.6f s at %.6f s',
                self._count, item, deadline, time.perf_counter())
            self._count += 1
            # Notify anyone waiting on the condition that the queue has
            # changed.
            self._cv.notify()

    def get(self):
        """Return the first element in the queue and remove it.

        The element will be tuple (deadline, count, item).
        """
        with self._cv:
            # Wait until there is at least one element in the queue.
            while len(self._queue) == 0:
                self._cv.wait()
            element = heapq.heappop(self._queue)
        self._logger.debug(
            'get(#%u - %s @ %.6f s at %.6f s',
            element[1], element[2], element[0], time.perf_counter())
        return element

    def peek(self):
        """Returns the first element in the queue without removing it.

        The element will be tuple (deadline, count, item).
        """
        with self._cv:
            # Wait until there is at least one element in the queue.
            while len(self._queue) == 0:
                self._cv.wait()
            element = self._queue[0]
        self._logger.debug(
            'peek(#%u - %s @ %.6f s',
            element[1], element[2], element[0])
        return element

    def qsize(self):
        """Return the number of elements in the queue."""
        with self._cv:
            return len(self._queue)


if __name__ == '__main__':
    from threading import Barrier, BrokenBarrierError, Event, Thread

    start_barrier = Barrier(2, timeout=1)   # Start running producer and consumer.
    end_barrier = Barrier(3, timeout=60)    # Wait to terminate.
    terminate_event = Event()

    # Object that signals shutdown
    _sentinel = object()

    # The time offsets (in microseconds) when an event will be fired.
    event_times = [0, 0.5, 0.2, 0.1, 0, 0.01, 0.02, 0, 0.099]

    def producer(dq_out):
        """Place a new data item into the queue every interval seconds for number items."""
        start_barrier.wait()
        index = 0
        start_micros = time.perf_counter() + 0.010
        for et in event_times:
            if et != 0:
                et = start_micros + et
            # Produce some data
            data = f'Some value {index}'
            dq_out.put((et, data))
            print(f'Put: {data} @ {et:.6f} s')
            index = index + 1
        dq_out.put((0, 'abc'))
        print('Put: sentinel')
        dq_out.put((sys.float_info.max, _sentinel))
        print(f'Queue: {dq_out}')
        print(f'Producer is done, created {index} elements (plus sentinel).')
        try:
            end_barrier.wait()
        except BrokenBarrierError:
            print('producer() end_barrier broken')

    def consumer(dq_in):
        """Get data items from the queue and process them."""
        start_barrier.wait()
        items = 0
        while True:
            # Peek at the data.
            (deadline, idx, data) = dq_in.peek()
            current_s = time.perf_counter()
            if deadline > current_s:
                if terminate_event.is_set():
                    break
                continue

            # Get the first element in the queue.
            (deadline, idx, data) = dq_in.get()
            items = items + 1

            if data is _sentinel:
                print('Get: sentinel')
                break
            print(f'Get: {data} @ {deadline:.6f} s (qsize {dq_in.qsize()})'
                  f' delta_s {current_s - deadline:.6f}')

        # Indicate completion
        print(f'Consumer is done, qsize {dq_in.qsize()}.')
        print(f'Queue: {dq_in}')
        try:
            end_barrier.wait()
        except BrokenBarrierError:
            print('consumer() end_barrier broken')

    def demo():
        """Demonstration of the DeadlineQueue and how to use it."""
        # Create the shared queue and launch both threads
        q = DeadlineQueue()
        t1 = Thread(target=consumer, args=(q,))
        t2 = Thread(target=producer, args=(q,))
        t1.start()
        t2.start()
        # Wait for all produced items to be consumed
        try:
            end_barrier.wait(timeout=5)
        except BrokenBarrierError:
            print('demo() end_barrier broken')
            terminate_event.set()
        print('Both threads are done. Terminating')
        sys.exit(0)

    # Perform demonstration.
    demo()
