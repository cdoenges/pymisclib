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

"""Collection of various utility functions.

    This file is part of pymisclib which lives at
    https://github.com/cdoenges/pymisclib.

    :LICENSE:
    © Copyright 2020, 2021, 2022 by Christian Dönges <cd@platypus-projects.de>

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

# pylint: disable=invalid-name

import argparse
import codecs
import contextlib
import glob
import locale
import logging
import os
import sys
import traceback
from pathlib import Path


# Globals (use sparingly)
logger = logging.getLogger(__name__)


def dir_path(path: str) -> Path:
    """Convert the string to a path and return it if it is a directory.

        This function is intended to be used as the ``type`` argument to
        ``Argparser.add_argument()``.

        :param str path: String containing path to check.
        :return: Path to a directory.
        :rtype: Path
        :raise argparse.ArgumentTypeError:
    """
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError(
            f'"{path}" is not a valid path to a directory')
    return Path(path)


def exit_hard(returncode: int = 0):
    """Terminate the running application.

        :param int returncode: Exit code to return to spawning shell.
    """
    os._exit(returncode)  # pylint: disable=protected-access


def file_path(path: str) -> Path:
    """Convert the string to a path and return it if it is a file.

        :param str path: String containing path to check.
        :return: Path to a file.
        :rtype: Path
        :raise argparse.ArgumentTypeError:
    """
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(
            f'"{path}" is not a valid path to a file')
    return Path(path)


def initialize_console():
    """Initialize the console to work with UTF-8 encoded strings.

        On windows, the console is strange and if output is redirected to a
        file, it gets even stranger. This confuses Python and even though
        PEP 528 solves the problem for interactive consoles, this does not
        help for non-interactive (which redirected streams are).

        The solution for now is to reconfigure the codecs for stdout and
        stderr to always use UTF-8 and replace unmappable characters.
    """
    if os.name == 'nt':
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
            print('Reconfigured stdout to use utf-8 encoding.')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')
            print('Reconfigured stderr to use utf-8 encoding.')


def initialize_logging(args):
    """Initialize the logging interface with the command line options
       passed through the object 'args'. An instance of the root logger is
       returned to the caller.

       If a sub-module uses logging.getLogger('somename'), the logger will
       be a child of the root logger and inherit the settings made here.

       :return: The root logger instance for the application.
       :rtype logging.logger:
    """

    # Define a new log level 'trace'
    logging.TRACE = 9
    logging.addLevelName(logging.TRACE, 'TRACE')

    def trace(self, message, *args, **kws):
        """Output message with level TRACE."""
        if self.isEnabledFor(logging.TRACE):
            # Logger takes its '*args' as 'args'.
            self._log(logging.TRACE, message, args, **kws)  # pylint: disable=protected-access

    logging.Logger.trace = trace

    # args.loglevel contains the string value of the command line option
    # --loglevel.
    numeric_log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_log_level, int):
        raise ValueError(f'Invalid log level: {args.loglevel}')

    # Configure the root logger instance.
    global logger   # # pylint: disable=global-statement
    logger = logging.getLogger()
    if args.debug:
        logger.setLevel(logging.TRACE)
    else:
        logger.setLevel(numeric_log_level)

    # Create file handler only if debug mode is active.
    if args.debug:
        app_name = sys.argv[0]
        fh = logging.FileHandler(app_name + '.log', encoding='utf-8', mode='w')
        fh.setLevel(logging.TRACE)

    lc = locale.getpreferredencoding()
    if lc != 'utf-8':
        locale.setlocale(locale.LC_CTYPE, 'C')

    # Create a console handler.
    initialize_console()
    ch = logging.StreamHandler()
    ch.setLevel(numeric_log_level)

    # Create a formatter and add it to the handlers.
    terseFormatter = logging.Formatter('%(levelname)-8s %(message)s')
    ch.setFormatter(terseFormatter)
    if args.debug:
        verboseFormatter = logging.Formatter(
            '%(asctime)s %(name)-26s %(levelname)-8s %(message)s')
        fh.setFormatter(verboseFormatter)

    # Add the handlers to the logger.
    logger.addHandler(ch)
    if args.debug:
        logger.addHandler(fh)

    if args.verbose:
        logger.info('Logging initialized.')

    if lc != 'utf-8':
        if locale.getpreferredencoding() == 'utf-8':
            logger.debug('Changed encoding from "%s" to "utf-8".', lc)
        elif lc == locale.getpreferredencoding():
            logger.debug('Failed to change encoding from "%s" to "utf-8".', lc)
        else:
            logger.warning('Failed to change encoding from "%s" to "utf-8", got "%s".',
                           lc, locale.getpreferredencoding())

    logger.debug('Parsed args are: %s', args)
    return logger


def is_power_of_two(n: int) -> bool:
    """Return True if the given number *n* is a power of two.

        :param int n: number to check
        :return: True if *n* is a power of two, False otherwise.
        :rtype: bool
    """
    return (n != 0) and ((n & (n - 1)) == 0)


def log_hexdump(fn_logger: logging.Logger,
                b: bytes,
                bytes_per_line: int = 16,
                level: int = logging.DEBUG,
                start_offset: int = 0,
                first_prefix: str = '',
                always_prefix: str = '',
                show_ascii: bool = True):
    """Log a pretty representation of the given bytes to the logger.

        ```
        first_prefix   00000000  64 65 66 67 68 69 6A 6B  @ABCDEFG
        always_prefix  00000000  64 65 66 67 68 69 6A 6B  @ABCDEFG
        ```

        :param logging.Logger fn_logger: The logger to log to.
        :param bytes b: The bytes to print.
        :param int bytes_per_line: The number of bytes per line.
        :param int level: Level for logging (e.g. CRITICAL, ERROR, .. DEBUG)
        :param int start_offset: The starting offset for the first byte.
        :param str first_prefix: A string before the offset on the first line.
        :param str always_prefix: A string that will be printed before every
            line (except the first if first_prefix was specified).
        :param bool show_ascii: Print ASCII characters after the hex dump if True.
    """
    if len(first_prefix) == 0:
        first_prefix = always_prefix
    elif len(first_prefix) > len(always_prefix):
        always_prefix += ' ' * (len(first_prefix) - len(always_prefix))
    elif len(always_prefix) > len(first_prefix):
        first_prefix += ' ' * (len(always_prefix) - len(first_prefix))
    length = len(b)
    offset = 0
    first = True
    if length <= bytes_per_line:
        show_offset = False
    else:
        show_offset = True
    while length > 0:
        if length < bytes_per_line:
            bytes_per_line = length
        b_slice = b[offset:offset + bytes_per_line]
        hs = b_slice.hex(' ')
        if first:
            s = f'{first_prefix}  '
            first = False
        else:
            s = f'{always_prefix}  '
        if show_offset:
            s += f'{offset + start_offset:08x}  {hs}  '
        else:
            s += f'{hs}  '
        if show_ascii:
            for c in b_slice:
                c = chr(c)
                if c.isprintable():
                    s += c
                else:
                    s += '.'
        fn_logger.log(level, s)
        length -= bytes_per_line
        offset += bytes_per_line


def log_stacktrace(fn_logger: logging.Logger,
                   level: int = logging.DEBUG):
    """Log the current stack trace inside or outside an exception.

        :param logging.Logger fn_logger: The logger to log to.
        :param int level: Level for logging (e.g. CRITICAL, ERROR, .. DEBUG)
    """
    # Get the current exception.
    ex = sys.exc_info()[0]
    # Remove this method from the call stack.
    stack = traceback.extract_stack()[:-1]
    if ex is not None:
        # Exception is present, so remove the call of this method.
        del stack[-1]
    fn_logger.log(level, 'Traceback (most recent call last):')
    for s in traceback.format_list(stack):
        fn_logger.log(level, s)
    if ex is not None:
        fn_logger.log(level, traceback.format_exc())


def resolve_wildcards(filenames: list[str]) -> list[Path]:
    """Resolve unique Paths from a list containing wildcards.

        :param list[str] filenames: A list of filenames that may contain
             wildcards.
        :return: A list of unique Paths.
        :rtype list[Path]:
    """
    # Resolve wildcards.
    names = []
    for n in filenames:
        i = glob.glob(n)
        if i:
            names.extend(i)
    # Remove duplicates
    names = list(set(names))

    # Convert strings to paths.
    paths = [Path(n) for n in names]
    return paths


def round_down(n: int, m: int) -> int:
    """Round the given number *n* down to the nearest multiple of *m*.

        :param int n: number to round
        :param int m: multiple to round to
        :return: n rounded down to a multiple of m.
        :rtype int:
    """
    return n & ~(m - 1)


def round_up(n: int, m: int) -> int:
    """Round the given number *n* up to the nearest multiple of *m*.

        :param int n: number to round
        :param int m: multiple to round to
        :return: n rounded up to a multiple of m.
        :rtype int:
    """
    return (n + m - 1) & ~(m - 1)


@contextlib.contextmanager
def std_open(filename: str = None, mode: str = 'w'):
    """Open either a file or stdin/stdout for use with `with`.

        If the filename is None or '-' then stdin or stdout (depending on the
        mode) are used.
        Otherwise, the file is used. I is closed when the `with` block is done.

        :param str filename: A filename, '-', or None.
        :param str mode: The mode to use for open().

        ## Example
        ```
            with std_open(fn, 'r') as f:
                c = f.read()
        ```
    """
    if filename and filename != '-':
        fh = open(filename, mode)   # pylint: disable=consider-using-with
    else:
        if 'r' in mode:
            fh = sys.stdin
        else:  # 'w'
            fh = sys.stdout

    try:
        yield fh
    finally:
        if fh is not sys.stdin and fh is not sys.stdout:
            fh.close()


if __name__ == '__main__':
    if sys.version_info < (3, 9):
        sys.stderr.write('FATAL ERROR: Python 3.9 or later is required.\n')
        sys.exit(1)