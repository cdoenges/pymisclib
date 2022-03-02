#!/usr/bin/env python
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
"""A skeleton (= template) for a Python 3.x command line tool.

   The skeleton application is capable of parsing command line options and
   logging to the console and/or syslogd.

   Has been tested under:
       - Python 3.7.2 Linux (Debian 9), macOS 10.13 & 10.14 (via macports),
                      Win 10 64bit

   Known issues:
       - None

    AUTHOR
    Christian Dönges, Platypus Projects GmbH www.platypus-projects.de

    :LICENSE:
    © Copyright 2012, 2017, 2022 by Christian Dönges <cd@platypus-projects.de>

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

import argparse
import logging
import sys


logger = None


def parseCommandLineArguments(argv: list) -> argparse.Namespace:
    """Parse command-line arguments.

        :param list argv: A list of strings that will be parsed.

        :return: A populated namespace containing the parsed arguments.
        :rtype: NamedTuple
    """
    parser = argparse.ArgumentParser(
        description='skeleton app.')
    parser.add_argument('--debug', '-d', dest='debug',
                        default=False, action='store_true',
                        help='Enable debug mode, which writes a TRACE log to a file.')
    parser.add_argument('--loglevel', '-l', dest='loglevel',
                        default='ERROR', action='store',
                        choices=['CRITICAL', 'ERROR',
                                 'WARNING', 'INFO', 'DEBUG'],
                        help='The minimum level of messages that will be logged.')
    parser.add_argument('--verbose', '-v', dest='verbose',
                        default=False, action='store_true',
                        help='Enable verbose mode, which write a lot more output to the console.')
    args = parser.parse_args(argv)

    if args.debug:
        print('Using arguments:', args)

    return args


def initializeLogging(args: argparse.Namespace):
    """Initializes the logging interface with the command line options
       passed through the object 'args'. An instance of the root logger is
       returned to the caller.

       If a sub-module uses logging.getLogger('somename'), the logger will
       be a child of the root logger and inherit the settings made here.

        :param namespace args: The parsed command-line arguments.
        :return: The root logger.
        :rtype: logging
    """

    # Define a new log level 'trace'
    logging.TRACE = 9
    logging.addLevelName(logging.TRACE, 'TRACE')

    def trace(self, message, *args, **kws):
        """Output message with level TRACE."""
        if self.isEnabledFor(logging.TRACE):
            # Logger takes its '*args' as 'args'.
            self._log(logging.TRACE, message, args, **kws)

    logging.Logger.trace = trace

    # args.loglevel contains the string value of the command line option
    # --loglevel.
    numeric_log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_log_level, int):
        raise ValueError('Invalid log level: %s', args.loglevel)

    # Configure the root logger instance.
    global logger
    logger = logging.getLogger()
    logger.setLevel(numeric_log_level)

    appName = sys.argv[0]

    fh = None
    if args.debug:
        # Create file handler.
        fh = logging.FileHandler(appName + '.log')
        fh.setLevel(logging.TRACE)

    # Create a console handler.
    ch = logging.StreamHandler()
    if args.verbose:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.WARNING)

    # Create a handler to log to syslogd. If a non-default address and port
    # are required, add an argument (address, port). It is also possible
    # to specify the facility and socket type.
    # See http://docs.python.org/library/logging.handlers.html#logging.handlers.SysLogHandler
    # Example:
    # sh = SysLogHandler(('localhost', 541), facility=LOG_AUTH,
    #                    sockettype=socket.SOCK_DGRAM)
    # Many Unix systems are configured to accept syslogd input from a domain
    # socket instead of UDP port 541. Some known domain sockets are tried
    # before trying UDP. If this is not what you want, change it.
    # If you need a different domain socket, add it to the list.
    from logging.handlers import SysLogHandler
    import socket
    sh = None
    syslogdConfig = ''
    # Try the domain sockets for Linux, Mac OS X.
    for domainSocket in ('/dev/log', '/var/run/syslog'):
        try:
            sh = SysLogHandler(domainSocket)
            syslogdConfig = domainSocket
            break
        except socket.error:
            pass
        except AttributeError:
            # MS Windows does not know socket.AF_UNIX, so trying domain
            # sockets will fail. In this case, we give up looping.
            break
    if not sh:
        # Unable to connect using a domain socket, so try localhost:541.
        sh = SysLogHandler()
        syslogdConfig = 'localhost:541 (UDP)'

    # Create a formatter and add it to the handlers.
    verboseFormatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    terseFormatter = logging.Formatter('%(levelname)-8s %(message)s')
    syslogFormatter = logging.Formatter(
        appName + ' %(levelname)-8s %(message)s')
    ch.setFormatter(terseFormatter)
    if fh:
        fh.setFormatter(verboseFormatter)
    if sh:
        sh.setFormatter(syslogFormatter)

    # Add the handlers to the logger.
    logger.addHandler(ch)
    if fh:
        logger.addHandler(fh)
    if sh:
        logger.addHandler(sh)
        logger.info('syslogd connection using %s.', syslogdConfig)
    logger.info('Logging initialized.')
    logger.debug(args)
    return logger


def performSkeleton():
    '''Do what the program is supposed to do.'''

    # 'application' code
    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warn message')
    logger.error('error message')
    logger.critical('critical message')


def main(argv: list):
    '''The main function of this script is called with all command line
       parameters in the array 'argv'.'''

    # Handle command line arguments.
    args = parseCommandLineArguments(argv[1:])

    # Set up logging.
    global logger
    logger = initializeLogging(args)

    performSkeleton()


# This code is executed if the file is called as a stand-alone command.
if __name__ == '__main__':
    main(sys.argv)
