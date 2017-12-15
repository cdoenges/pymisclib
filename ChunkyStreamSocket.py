#!/usr/bin/env python3
# vim ts=4,fileencoding=utf-8
# SPDX-License-Identifier: Apache-2.0
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

import attr
import logging
import socket


@attr.s
class ChunkyStreamSocket(object):
    logger = attr.ib(default=logging.getLogger(__name__))
    debug = attr.ib(default=False)

    host = attr.ib(default='127.0.0.1', type=str,
                   validator=attr.validators.instance_of(str))
    port = attr.ib(default=10000, type=int,
                   validator=attr.validators.instance_of(int))
    socket = attr.ib(init=False, type=socket.socket,
                     validator=attr.validators.instance_of(socket.socket))
    _backlog_bytes = attr.ib(default=None, type=bytes)

    def __attrs_post_init__(self, sock=None):
        """Custom initializer to set or create a socket.

        It appears that the attr.Factory does not support two arguments,
        which the socket initializer requires. So we need this.
        """
        if sock is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = sock

    def bind_and_listen(self, backlog: int=5, timeout: float=None):
        """Bind to the host and port to make a server socket.

        backlog -- The maximum number of queued connections.
        timeout -- The number of seconds after which socket operations will
        time out. Set to None for a blocking socket.
        """
        self.logger.debug('bind_and_listen({}:{})'.
                          format(self.host, self.port))
        # Set the timeout.
        self.socket.settimeout(timeout)
        # Allow the server socket to re-bind immediately.
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to the given address and port.
        self.socket.bind((self.host, self.port))
        # Start listening for a connection attempt.
        self.socket.listen(backlog)

    def accept(self):
        """Accept a client connection on the (server) socket.

           Returns the client socket and client address tuple.
        """
        client_sock, client_addr = self.socket.accept()
        self.logger.debug('accept({})'.format(client_addr))
        return (client_sock, client_addr)

    def close(self):
        """Close the socket."""
        self.socket.close()
        self.socket = None
        self.logger.debug('close()')

    def connect(self, timeout: float=None):
        """Connect client socket to the server at host:port.

        timeout -- The number of seconds after which socket operations will
        time out. Set to None for a blocking socket.
        """
        self.logger.debug('connect({}:{}, {})'.
                          format(self.host, self.port, timeout))
        # Set the timeout.
        self.socket.settimeout(timeout)
        # Allow server socket to re-bind immediately.
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.socket.connect((self.host, self.port))
        except OSError as e:
            self.logger.error('Connection attempt failed: {}'.format(e))
            raise e
        self.logger.debug('Connected to {}:{}'.format(self.host, self.port))

    def send(self, msg_bytes: bytes) -> int:
        """Send the bytes.

        :Parameters:
        msg_bytes -- The bytes to send. If the receiver is expecting a
        separator, it must be appended to the message by the caller.

        :Return:
        The number of bytes sent.

        :Raises:
        RuntimeError
        """
        total_nr_sent = 0
        while total_nr_sent < len(msg_bytes):
            current_nr_sent = self.socket.send(msg_bytes[total_nr_sent:])
            if current_nr_sent == 0:
                self.logger.debug('self.socket.send() failed.')
                raise RuntimeError("socket connection broken")
            total_nr_sent = total_nr_sent + current_nr_sent
        self.logger.debug('--> {}'.format(msg_bytes))
        return total_nr_sent

    def recv(self, length: int, timeout: float=None):
        """Receive length bytes from the socket.

        This function handles chunked data (i.e. the data to receive is split
        into multiple packets). If more data than expected is received, it is
        placed into a backlog buffer until the next call to a receive
        function.

        :Parameters:
        length -- The number of bytes to read.
        timeout -- Timeout in seconds or None to block.

        :Return:
        The received bytes.

        :Raises:
        RuntimeError
        TimeoutError
        """
        chunks = []
        nr_received = 0
        # Retrieve the backlog from the previous recv() call and use it as the
        # first chunk.
        if self._backlog_bytes is not None:
            chunks.append(self._backlog_bytes)
            nr_received = len(self._backlog_bytes)
            self._backlog_bytes = None

        # Set the timeout.
        self.socket.settimeout(timeout)

        # Receive bytes until we have enough to satisfy the length requirement.
        while nr_received < length:
            chunk = self.socket.recv(min(length - nr_received, 4096))
            self.debug('socket.recv(4096) := {}'.format(chunk))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            nr_received = nr_received + len(chunk)

        # Join all chunks into one message.
        msg_bytes = b''.join(chunks)
        # Cut off the part that is too long.
        if len(msg_bytes) > length:
            self._backlog_bytes = msg_bytes[length:]
            msg_bytes = msg_bytes[:length]

        self.logger.debug('<-- {}'.format(msg_bytes))
        return msg_bytes

    def recv_to_separator(self, separator: bytes):
        """Receive bytes until the given separator is found.

        This function handles chunked data (i.e. the data to receive is
        split into multiple packets). If more data than expected is
        received, it is placed into a backlog buffer until the next call
        to a receive function.

        :Parameters:
        separator -- One or more bytes that separate messages in the TCP
        stream.

        :Return:
        The received bytes.

        :Raises:
        RuntimeError
        TimeoutError
        """
        self.logger.debug('recv_to_separator({})'.format(separator))
        start_search_index = 0
        chunk = b''
        msg_bytes = b''
        while True:
            if self._backlog_bytes is not None and len(self._backlog_bytes) > 0:
                # The first time around, process the backlog.
                chunk = self._backlog_bytes
                self._backlog_bytes = None
                self.logger.debug('backlog chunk = {}'.format(chunk))
            else:
                chunk = self.socket.recv(4096)
                self.logger.debug('socket.recv(4096) := {}'.format(chunk))
            if chunk == b'':
                raise RuntimeError("socket connection broken")

            msg_bytes = msg_bytes + chunk
            start_separator_index = msg_bytes.find(separator, start_search_index)
            if start_separator_index > -1:
                # We found the separator at index start_separator_index.
                self._backlog_bytes = msg_bytes[start_separator_index + len(separator):]
                self.logger.debug('Backlog: {}'.format(self._backlog_bytes))
                msg_bytes = msg_bytes[:start_separator_index]
                break
            else:
                # The separator could have started in the current chunk but
                # finishes in the next chunk, so we need to search the
                # len(separator) - 1 last bytes of the separator again
                start_search_index = max(0, len(msg_bytes) - (len(separator) - 1))

        self.logger.debug('<-- {}'.format(msg_bytes))
        return msg_bytes


if __name__ == '__main__':
    import sys
    from threading import Barrier, BrokenBarrierError, Thread

    start_barrier = Barrier(2, timeout=5)
    end_barrier = Barrier(3, timeout=60)
    separator = b'\0\1\2\1\0'

    messages = [
        b'abcdef',
        b'1234',
        b'a', b'bc', b'de\0', b'\1\2\1\0fghi',
        b'xyzZYX',
        b'',
        b'+++',
    ]

    def server():
        logger = logging.getLogger('server')
        logger.info('server starting')
        server_socket = ChunkyStreamSocket(logging.getLogger('server.socket'))
        server_socket.bind_and_listen(timeout=60)
        logger.debug('server_socket = {}'.format(server_socket.socket))
        start_barrier.wait()

        logger.info('server running')
        (client_socket, client_addr) = server_socket.accept()
        cs = ChunkyStreamSocket(logging.getLogger('server.cs'))
        cs.socket = client_socket
        while True:
            msg = cs.recv_to_separator(separator)
            logger.info('MSG: {}'.format(msg))
            if msg == b'+++':
                logger.debug('EOF received')
                break

        logger.info('server closing connection')
        cs.close()
        server_socket.close()
        try:
            end_barrier.wait()
        except BrokenBarrierError:
            logger.error('server() end_barrier broken')

    def client():
        logger = logging.getLogger('client')
        logger.info('client starting')
        client_socket = ChunkyStreamSocket(logging.getLogger('client.socket'))
        logger.debug('client_socket = {}'.format(client_socket.socket))
        start_barrier.wait()
        logger.info('client running')
        client_socket.connect()
        for message in messages:
            try:
                client_socket.send(message + separator)
            except RuntimeError as e:
                logger.critical(e)
                logger.critical('client terminating')
                break
        try:
            end_barrier.wait()
        except BrokenBarrierError:
            logger.error('client() end_barrier broken')
        finally:
            client_socket.close()

    # Log everything to the console.
    logger = logging.getLogger()
    logger.setLevel(logging.NOTSET)
    ch = logging.StreamHandler()
    ch.setLevel(logging.NOTSET)
    formatter = logging.Formatter('%(asctime)s - %(name)20s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    t1 = Thread(target=server, args=())
    t2 = Thread(target=client, args=())
    t1.start()
    t2.start()
    logger.info('Client and server running.')
    try:
        end_barrier.wait(timeout=5)
    except BrokenBarrierError:
        logger.error('Barrier broken. Terminating')
    sys.exit(0)
