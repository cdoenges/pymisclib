#!/usr/bin/env python3
# vim: fileencoding=utf8
#
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
"""An interactive text console menu.

    # Example
    (pending)

    AUTHOR
    Christian Dönges, Platypus Projects GmbH www.platypus-projects.de

    The master repository for this file is located at
    https://github.com/cdoenges/pymisclib.


    LICENSE
    This file is licensed under the Apache License, Version 2.0
    <https://spdx.org/licenses/Apache-2.0.html>.
    Please contact the author to discuss other licensing options.


    © Copyright 2019, 2021 Christian Dönges <cd@platypus-projects.de>

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import logging
import readline


class CommandItem:
    """An item for a command menu."""
    def __init__(self, name: str,
                 default: bool = False):
        self.name = name
        self.default = default

    def __str__(self):
        """A human-readable description of the instance."""
        s = f'CommandItem<"{self.name}"'
        if self.default:
            s += ', default>'
        else:
            s += '>'
        return s


class CommandMenu:
    """Interactive text console menu."""
    # https://pymotw.com/2/readline/
    def __init__(self,
                 vocabulary: dict = {'quit': []},
                 prompt: str = '> '):
        # Configuration members.
        self.prompt = prompt
        self.vocabulary = vocabulary

        # Dynamic members.
        self.current_candidates = []

    def __str__(self):
        """A human-readable description of the instance."""
        s = 'CommandMenu<'
        first = True
        for key, item in self.vocabulary.items():
            if first:
                s += str(item)
                first = False
            else:
                s += f', {item:!s}'
        s += '>'
        return s

    def complete(self, text, state):
        """Command-line completion of the user text in the given state."""
        response = None
        if state == 0:
            # This is the first time for this text, so build a match list.
            origline = readline.get_line_buffer()
            begin = readline.get_begidx()
            end = readline.get_endidx()
            being_completed = origline[begin:end]
            words = origline.split()

            logging.debug('origline=%s', repr(origline))
            logging.debug('begin=%s', begin)
            logging.debug('end=%s', end)
            logging.debug('being_completed=%s', being_completed)
            logging.debug('words=%s', words)

            if not words:
                self.current_candidates = sorted(self.vocabulary.keys())
            else:
                try:
                    if begin == 0:
                        # first word
                        candidates = self.vocabulary.keys()
                    else:
                        # later word
                        first = words[0]
                        candidates = self.vocabulary[first]

                    if being_completed:
                        # match vocabulary with portion of input
                        # being completed
                        self.current_candidates = \
                            [w for w in candidates if w.startswith(being_completed)]
                    else:
                        # matching empty string so use all candidates
                        self.current_candidates = candidates

                    logging.debug('candidates=%s', self.current_candidates)

                except (KeyError, IndexError) as err:
                    logging.error('completion error: %s', err)
                    self.current_candidates = []

        try:
            response = self.current_candidates[state]
        except IndexError:
            response = None
        logging.debug('complete(%s, %s) => %s', repr(text), state, response)
        return response

    def input_loop(self):
        """Loop to get input."""
        line = ''
        while line != 'quit':
            line = input(self.prompt)
            print(f'Dispatch {line}')


if __name__ == '__main__':
    # Register our completer function
    cm = CommandMenu({
        'list': ['files', 'directories'],
        'print': ['byname', 'bysize'],
        'stop': [],
    })
    readline.set_completer(cm.complete)

    # Use the tab key for completion
    readline.parse_and_bind('tab: complete')        # Works on Linux
    readline.parse_and_bind('bind ^I rl_complete')  # Works on macOS
    readline.parse_and_bind('set editing-mode vi')

    # Prompt the user for text
    cm.input_loop()
