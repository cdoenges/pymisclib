#!/usr/bin/env python3
# vim: fileencoding=utf8
#
# SPDX-License-Identifier: Apache-2.0
"""Print multiple progress bars to the console.

    The configuration of the bars is handled through a list of dictionaries.
    Each dictionary contains the parameters for a single progress bar.

    Before the bars are shown, prepare_bars() must be called to make room for
    the bars on the console.

    Each time a bar is updated, print_bars() is called to update the console
    output.

    # Bar example
    ```
    Total |------------------------------| 0% Writing
          |███████████████---------------| 50.9% /tmp3muil9sc/0000000000000000.tmp
    ```

    from multiprogressbar import prepare_bars, print_bars

    config = [
        { 'current_iteration': 0, 'total_iterations': 5, 'prefix': 'Total', suffix': 'Writing', 'decimals': 0, bar_length': 30},
        { 'current_iteration': 509, 'total_iterations': 1000, 'prefix': '     ', suffix': '/tmp3muil9sc/0000000000000000.tmp', 'decimals': 1, 'bar_length': 30},
    ]
    prepare_bars(config)
    print_bars(config)

    AUTHOR
    Christian Dönges, Platypus Projects GmbH www.platypus-projects.de

    The master repository for this file is located at
    https://github.com/cdoenges/pymisclib.


    LICENSE
    This file is licensed under the Apache License, Version 2.0
    <https://spdx.org/licenses/Apache-2.0.html>.
    Please contact the author to discuss other licensing options.


    © Copyright 2019 Christian Dönges <cd@platypus-projects.de>

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

# pylint: disable=C0103,R0903,E501

import enum
import sys
from time import sleep


@enum.unique
class BAR_COLORS(enum.Enum):
    Black = '\033[30m'
    Red = '\033[31m'
    Green = '\033[32m'
    Yellow = '\033[33m'
    Blue = '\033[34m'
    Magenta = '\033[35m'
    Cyan = '\033[36m'
    White = '\033[37m'
    BrightBlack = '\033[1;30m'
    BrightRed = '\033[1;31m'
    BrightGreen = '\033[1;32m'
    BrightYellow = '\033[1;33m'
    BrightBlue = '\033[1;34m'
    BrightMagenta = '\033[1;35m'
    BrightCyan = '\033[1;36m'
    BrightWhite = '\033[1;37m'


def print_single_bar(
        current_iteration: int,
        total_iterations: int,
        prefix: str = '',
        suffix: str = '',
        decimals: int = 1,
        bar_length: int = 80,
        bar_color: str = '\033[30m'):
    """Output a single progress bar to stdout.

    :param int current_iteration: the current iteration
    ;param int total_iterations: the total number of iterations
    :param str prefix: a string that will be output before the bar
    :param str suffix: a string that will be output after the bar
    :param int bar_length: the length of the bar in characters
    """
    if current_iteration > total_iterations:
        current_iteration = total_iterations

    percents = f'{100 * (current_iteration / float(total_iterations)):.{decimals}f}'
    filled_length = int(round(bar_length * current_iteration / float(total_iterations)))
    bar = f'{"█" * filled_length}{"-" * (bar_length - filled_length)}'

    sys.stdout.write(f'\x1b[2K\r{prefix} |{bar_color.value}{bar}{BAR_COLORS.Black.value}| {percents}% {suffix}')


def prepare_bars(configs: list):
    for c in configs:
        sys.stdout.write('\n')


def print_bars(configs: list):
    # Move the cursor up to the start of the line of the first bar.
    for n in range(len(configs)):
        sys.stdout.write('\033[F')  # up

    for config in configs:
        ci = config['current_iteration']
        ti = config['total_iterations']
        prefix = config.get('prefix', '')
        suffix = config.get('suffix', '') + '\033[K\n'
        decimals = config.get('decimals', 1)
        bar_length = config.get('bar_length', 80)
        bar_color = config.get('bar_color', BAR_COLORS.Black)
        print_single_bar(ci, ti, prefix, suffix, decimals, bar_length,
                         bar_color)
    sys.stdout.flush()


def main():
    configs = [
        {
            'current_iteration': 0,
            'total_iterations': 5,
            'prefix': 'Total',
            'suffix': 'Writing',
            'decimals': 0,
            'bar_length': 30,
            'bar_color': BAR_COLORS.Green,
        },
        {
            'current_iteration': 509,
            'total_iterations': 1000,
            'prefix': '     ',
            'suffix': '/tmp3muil9sc/0000000000000000.tmp',
            'decimals': 1,
            'bar_length': 30
        },
        {
            'current_iteration': 1,
            'total_iterations': 10,
            'bar_length': 15,
            'bar_color': BAR_COLORS.BrightRed,
        },
        {
            'current_iteration': 0,
            'total_iterations': 100,
            'prefix': 'Jolly'
        },
    ]
    prepare_bars(configs)
    for i in range(100):
        print_bars(configs)
        for config in configs:
            config['current_iteration'] += 1
        sleep(.1)


if __name__ == '__main__':
    main()
