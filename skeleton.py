#!/usr/bin/env python
# vim ts=4,fileencoding=utf-8
'''A skeleton (= template) for a Python (2.x or 3.x) command line tool.

   The skeleton application is capable of parsing command line options and
   logging to the console and/or syslogd.
   
   Has been tested using:
       - Python 2.6.5 Linux (Ubuntu 10.04) and MS Windows (Cygwin).
       - Python 3.1.2 Linux (Ubuntu 10.04)
       - Python 3.2 Windows XP 32 bit.
   
   Known issues:
       - syslogd logging does not work on Python 3.1.2 on Ubuntu 10.04 LTS.

    AUTHOR
    Christian Dönges, Platypus Projects GmbH www.platypus-projects.de

    LICENSE
    This file is licensed under the BSD 3 Clause License <http://opensource.org/licenses/BSD-3-Clause>.
    Please contact the author to discuss other licensing options.


    Copyright (c) 2012, Christian Dönges, Platypus Projects GmbH
    All rights reserved.

    Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    Neither the name of Christian Dönges or Platypus Projects GmbH nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 
'''

import logging
import sys

def parseCommandLineArguments(argv):
    '''Parses the command line arguments specified in the argv array and
       returns an object containing all recognized options.
       
       Unrecognized options will be reported as an error.'''

    args = {}
    try:
        # argparse was introduced in Python 2.7. If it is not present,
        # an exception is raised.
        import argparse
        parser = argparse.ArgumentParser(description='Skeleton Python command line tool.')
        parser.add_argument('--debug', '-d', dest='debug', 
                default=False, action='store_true',
                help='Enable debug mode. Logging is set to DEBUG.')
        parser.add_argument('--loglevel', '-l', dest='loglevel',
                default='ERROR', action='store',
                choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'],
                help='The minimum level of messages that will be logged.')
        args = parse.parse_args()
    except ImportError:
        # The 'argparse' module could not be imported, so we're running
        # Python 2.6 or earlier, which use 'optparse'.
        from optparse import OptionParser
        parser = OptionParser('Skeleton Python command line tool.')
        parser.add_option('-d', '--debug', dest='debug',
                default=False, action='store_true',
                help='Enable debug mode. Logging is set to DEBUG.')
        parser.add_option('-l', '--loglevel', dest='loglevel',
                default='ERROR',
                help='The minimum level of messages that will be logged.')
        (args, spillover) = parser.parse_args()
        if len(spillover) > 0:
            print('Unknown argument.')
            parser.print_help()
            exit(1)

    if args.debug:
        print('Command line arguments:', args)
        args.loglevel = 'DEBUG'

    return args



def initializeLogging(args):
    '''Initializes the logging interface with the command line options
       passed through the object 'args'. An instance of a logger is
       returned to the caller.'''

    # args.loglevel contains the string value of the command line option
    # --loglevel.
    numeric_log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_log_level, int):
        raise ValueError('Invalid log level: %s' % args.loglevel)

    # Create a logger instance and configure it.
    logger = logging.getLogger(__name__)
    logger.setLevel(numeric_log_level)

    # Create file handler.
    appName = sys.argv[0]
    fh = logging.FileHandler(appName + '.log')

    # Create a console handler.
    ch = logging.StreamHandler()

    # Create a handler to log to syslogd. If a non-default address and port
    # are required, add an argument (address, port). It is also possible
    # to specify the facility and socket type.
    # See http://docs.python.org/library/logging.handlers.html#logging.handlers.SysLogHandler
    # Example:
    # sh = SysLogHandler(('localhost', 541), facility=LOG_AUTH, sockettype=socket.SOCK_DGRAM)
    # Many Unix systems are configured to accept syslogd input from a domain
    # socket instead of UDP port 541. Some known domain sockets are tried
    # before trying UDP. If this is not what you want, change it.
    # If you need a different domain socket, add it to the list.
    from logging.handlers import SysLogHandler
    sh = None
    syslogdConfig = ''
    # Try the domain sockets for Linux, Mac OS X.
    for domainSocket in ['/dev/log', '/var/run/syslog']:
        try:
            sh = SysLogHandler(domainSocket)
            syslogdConfig = domainSocket
            break
        except socket.error:
            pass
    if None == sh:
        # Unable to connect using a domain socket, so try localhost:541.
        sh = SysLogHandler()
        syslogdConfig = 'localhost:541 (UDP)'

    # Create a formatter and add it to the handlers.
    verboseFormatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    terseFormatter = logging.Formatter('%(levelname)-8s %(message)s')
    syslogFormatter = logging.Formatter(appName + ' %(levelname)-8s %(message)s')
    ch.setFormatter(terseFormatter)
    fh.setFormatter(verboseFormatter)
    sh.setFormatter(syslogFormatter)


    # Add the handlers to the logger.
    logger.addHandler(ch)
    logger.addHandler(fh)
    logger.addHandler(sh)

    logger.info('syslogd connection using \'' + syslogdConfig + '\'')
    logger.info('Logging initialized.')
    return logger



def performSkeleton():
    '''Do what the program is supposed to do.'''

    # 'application' code
    logger.debug('debug message')
    logger.info('info message')
    logger.warn('warn message')
    logger.error('error message')
    logger.critical('critical message')



def main(argv):
    '''The main function of this script is called with all command line
       parameters in the array 'argv'.'''

    # Handle command line arguments.
    args = parseCommandLineArguments(argv)

    # Set up logging.
    global logger
    logger = initializeLogging(args)

    performSkeleton()



# This code is executed if the file is called as a stand-alone command.
if __name__ == '__main__':
    main(sys.argv)


