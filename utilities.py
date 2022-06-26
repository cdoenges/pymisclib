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
# PackageVersion: 1.2.1

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
import ctypes
import glob
import gzip
import locale
import logging
import os
import shutil
import sys
import traceback
from datetime import datetime
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


def get_language() -> str:
    """Determine the language the current user has set their OS to."""
    if os.name == 'posix':
        # BSD, Darwin, and Linux make it easy.
        lang = os.environ['LANG'].split('.')[0]
    elif os.name == 'nt':
        windll = ctypes.windll.kernel32
        lang = locale.windows_locale[windll.GetUserDefaultUILanguage()]
    else:
        raise RuntimeError(f'unknown OS: {os.name}')
    return lang


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


def logging_add_trace():
    """Add a loglevel TRACE.

        This function should be called only once.
    """
    if hasattr(logging_add_trace, "nr_calls"):
        logging_add_trace.nr_calls += 1
        logging.getLogger(__name__).warning(
            'logging_add_trace() called %d times.',
            logging_add_trace.nr_calls)
        return
    logging_add_trace.nr_calls = 1  # it doesn't exist yet, so initialize it

    if hasattr(logging, 'TRACE'):
        logging.getLogger(__name__).debug('TRACE logging already enabled.')

    # Perform function.
    logging.TRACE = 9
    logging.addLevelName(logging.TRACE, 'TRACE')

    def trace(self, message, *args, **kws):
        """Output message with level TRACE."""
        if self.isEnabledFor(logging.TRACE):
            # Logger takes its '*args' as 'args'.
            self._log(logging.TRACE, message, args, **kws)  # pylint: disable=protected-access

    logging.Logger.trace = trace


def logging_initialize(
        loglevel: int = logging.WARNING,
        log_dir_path: Path = Path('.'),
        log_file_name_format: str = '%P.log',
        log_rotation: int = 0,
        log_compression: int = 5,
        loglevel_console: int = logging.WARNING,
        loglevel_file: int = logging.DEBUG) -> logging.Logger:
    """Initialize the logging interface with the command line options
       passed through the object 'args'. An instance of the root logger is
       returned to the caller.

       If a sub-module uses logging.getLogger('somename'), the logger will
       be a child of the root logger and inherit the settings made here.

        :param int loglevel: Loglevel of the logger. Log messages not meeting
            the level requirement are not processed at all.
        :param Path log_dir_path: Path of the directory containing log files.
            None will prevent log file creation.
        :param str log_file_name_format: Format string for the log file name.
            None will prevent log file creation.
        :param int log_rotation: How many logfiles of the same name to keep.
            If set to 0, any existing log file is overwritten. If set to >0,
            that many old log file copies (named <name>.1, <name>.2, etc.)
            are retained.
        :param int loglevel_console: Loglevel filter of the console logger.
        :param int logfile_level: Loglevel filter of the file logger.
        :return: The root logger instance for the application.
        :rtype logging.logger:

        :note: If the log_file_name_format contains a timestamp, log_rotation
            will only work on other log file copies with the exact same timestamp.
    """
    # Configure the root logger instance.
    global logger   # # pylint: disable=global-statement
    logger = logging.getLogger()
    logger.setLevel(loglevel)

    # Configure the console handler.
    lc = locale.getpreferredencoding()
    if lc != 'utf-8':
        locale.setlocale(locale.LC_CTYPE, 'C')
    initialize_console()
    ch = logging.StreamHandler()
    ch.setLevel(loglevel_console)
    terseFormatter = logging.Formatter('%(levelname)-8s %(message)s')
    ch.setFormatter(terseFormatter)
    logger.addHandler(ch)
    logger.debug('Logging to console initialized.')

    if log_file_name_format is not None and log_dir_path is not None:
        log_file_name = string_from_format(log_file_name_format)
        log_file_path = log_dir_path / log_file_name
        rotate_file(log_file_name, log_dir_path, log_rotation, log_compression)

        fh = logging.FileHandler(log_file_path, encoding='utf-8', mode='w')
        fh.setLevel(loglevel_file)
        verboseFormatter = logging.Formatter('%(asctime)s %(name)-26s %(levelname)-8s %(message)s')
        fh.setFormatter(verboseFormatter)
        logger.addHandler(fh)
        logger.debug('Logging to file "%s" initialized.', log_file_path)

    if lc != 'utf-8':
        if locale.getpreferredencoding() == 'utf-8':
            logger.debug('Changed encoding from "%s" to "utf-8".', lc)
        elif lc == locale.getpreferredencoding():
            logger.debug('Failed to change encoding from "%s" to "utf-8".', lc)
        else:
            logger.warning('Failed to change encoding from "%s" to "utf-8", got "%s".',
                           lc, locale.getpreferredencoding())

    return logger


def initialize_logging(args: argparse.Namespace):
    """Initialize the logging interface with the command line options
       passed through the object 'args'. An instance of the root logger is
       returned to the caller.

       If a sub-module uses logging.getLogger('somename'), the logger will
       be a child of the root logger and inherit the settings made here.

       :return: The root logger instance for the application.
       :rtype logging.logger:
    """

    # Define a new log level 'trace'
    logging_add_trace()

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


def rotate_file(file_name: str,
                file_dir: Path,
                rotation: int,
                compress_level: int = 9,
                fn_logger: logging.Logger = logging.getLogger(__name__)):
    """Rotate a (log-)file.

        The parameter rotation specifies the number of copies that will be
        retained.

        When rotating, file_name.rotation-1 is renamed to file_name.rotation
        for all values of rotation down to 1.

        The initial file (with no .rotation suffix) gains a suffix. If
        compress_level > 0, the initial file is also compressed.

        :note: Uses TRACE level logging.
    """
    fn_logger.debug('rotate_log(%s, %s, %d)', file_name, file_dir, rotation)
    if rotation == 0:
        fn_logger.trace('rotate_log(): nothing to rotate.')
        return

    max_rotation = rotation
    while rotation >= 0:
        if rotation == 0:
            candidate = file_dir / file_name
            if not candidate.exists():
                fn_logger.trace('rotate_log(): rotation 0 does not exists. Done.')
                return
        else:
            # Find previously rotated candidate.
            candidate = file_dir / f'{file_name}.{rotation}'
            candidate_is_compressed = False
            if not candidate.exists():
                candidate = file_dir / f'{file_name}.{rotation}.gz'
                candidate_is_compressed = True
                if not candidate.exists():
                    fn_logger.trace('rotate_log(): rotation %d does not exist.', rotation)
                    rotation -= 1
                    continue

        # We have found a match.
        fn_logger.trace('rotate_log(): found candidate %s.', candidate)
        if rotation == 0:
            # All other rotation copies have been renamed, now the last logfile
            # must be compressed (optional) and renamed.
            compress_path = file_dir / file_name
            if compress_level > 0:
                new_name = f'{file_name}.1.gz'
                new_path = file_dir / new_name
                fn_logger.trace('rotate_log(): compress %s -> %s.', compress_path, new_path)
                with open(compress_path, 'rb') as f_in:
                    # Get the modification time of the file we are rotating
                    # so it will be stored correctly in the gzip archive.
                    statinfo = os.stat(compress_path)
                    with open(new_path, 'wb') as f_out:
                        with gzip.GzipFile(file_name,
                                           'wb',
                                           compress_level,
                                           f_out,
                                           mtime=statinfo.st_mtime) as f_zip:
                            shutil.copyfileobj(f_in, f_zip)

                fn_logger.trace('rotate_log(): unlink %s.', compress_path)
                compress_path.unlink()
            else:
                new_path = file_dir / f'{file_name}.{rotation + 1}'
                fn_logger.trace('rotate_log(): rename %s -> %s', candidate, new_path)
                candidate.rename(new_path)
        elif rotation == max_rotation:
            # We have found the maximum rotation file. Delete it to make room.
            fn_logger.trace('rotate_log(): unlinking old %s.', candidate)
            candidate.unlink()
        elif rotation > 0:
            # Rename existing rotation to next higher.
            if candidate_is_compressed:
                new_path = file_dir / f'{file_name}.{rotation + 1}.gz'
            else:
                new_path = file_dir / f'{file_name}.{rotation + 1}'
            fn_logger.trace('rotate_log(): rename %s -> %s', candidate, new_path)
            candidate.rename(new_path)
        rotation -= 1


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
def std_open(filename: str = None, mode: str = 'w', encoding: str = 'utf-8'):
    """Open either a file or stdin/stdout for use with `with`.

        If the filename is None or '-' then stdin or stdout (depending on the
        mode) are used.
        Otherwise, the file is used. I is closed when the `with` block is done.

        :param str filename: A filename, '-', or None.
        :param str mode: The mode to use for open().
        :param str encoding: The encoding to pass to open(). Defaults to 'utf-8'.

        ## Example
        ```
            with std_open(fn, 'r') as f:
                c = f.read()
        ```
    """
    if filename and filename != '-':
        fh = open(filename, mode, encoding=encoding)
    else:
        if 'r' in mode:  # pylint: disable=else-if-used
            fh = sys.stdin
        else:  # 'w'
            fh = sys.stdout

    try:
        yield fh
    finally:
        if fh is not sys.stdin and fh is not sys.stdout:
            fh.close()


def string_from_format(fmt: str) -> str:
    """Given a strftime()-like format, expand into a string.

        Additional formats:
        - %P - name of the application

        :param str fmt: Format string to parse.
        :return: Resulting string.
    """
    fmt2 = ''
    if '%P' in fmt:
        start = 0
        pos = fmt.find('%P', start)
        while pos >= 0:
            length = pos - start
            fmt2 += fmt[start:length] + Path(sys.argv[0]).stem
            start = pos + 2
            pos = fmt.find('%P', start)
        fmt2 += fmt[start:]
    else:
        fmt2 = fmt

    now = datetime.now()
    return now.strftime(fmt2)


def true_stem(path: Path) -> str:
    """Return the true stem (e.g. the name without suffixes) of the Path."""
    ts = path.stem
    while path.suffixes:
        ts = path.stem
        path = Path(ts)
    return ts


if __name__ == '__main__':
    if sys.version_info < (3, 9):
        sys.stderr.write('FATAL ERROR: Python 3.9 or later is required.\n')
        sys.exit(1)
