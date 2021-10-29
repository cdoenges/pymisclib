#!/usr/bin/env python3
# vim ts=4,fileencoding=utf-8
# SPDX-License-Identifier: Apache-2.0
"""Output an ASCII table in various formats.

    :LICENSE:
    © Copyright 2019 by Christian Dönges <cd@platypus-projects.de>

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

# pylint: disable=consider-using-assignment-expr

import argparse


ascii_names = {
    0: 'NUL',
    1: 'SOH',
    2: 'STX',
    3: 'ETX',
    4: 'EOT',
    5: 'ENQ',
    6: 'ACK',
    7: 'BEL',
    8: 'BS',
    9: 'HT',
    10: 'LF',
    11: 'VT',
    12: 'FF',
    13: 'CR',
    14: 'SO',
    15: 'SI',
    16: 'DC0',
    17: 'DC1',
    18: 'DC2',
    19: 'DC3',
    20: 'DC4',
    21: 'NAK',
    22: 'SYN',
    23: 'ETB',
    24: 'CAN',
    25: 'EM',
    26: 'SUB',
    27: 'ESC',
    28: 'FS',
    29: 'GS',
    30: 'RS',
    31: 'US',
    127: 'DEL',
}


def text_list():
    """Output ASCII table as Python list."""
    print('ascii_list = [')
    for i in range(256):
        if i in ascii_names:
            c = ascii_names[i]
        else:
            c = str(chr(i))
            if not c.isprintable():
                c = '_'
        if c == "'":
            print(f'    "{c}",  # {i} / 0x{i:02x} / {c}')
        elif c == '\\':
            print(f"    '\\',  # {i} / 0x{i:02x} / BACKSLASH")
        else:
            print(f"    '{c}',  # {i} / 0x{i:02x} / {c}")
    print(']')


def text_table():
    """Output ASCII table as text."""
    h1 = '     |'
    h2 = '=====+'
    for lower_nibble in range(0, 16):
        h1 += f'| {lower_nibble:04b} '
        h2 += '+======'
    body = []
    for upper_nibble in range(0, 16):
        s1 = '     |'
        s2 = f'{upper_nibble:04b} |'
        s3 = '     |'
        s4 = '-----+'
        for lower_nibble in range(0, 16):
            i = (upper_nibble << 4) + lower_nibble
            if i in ascii_names:
                c = ascii_names[i]
            else:
                c = str(chr(i))
                if not c.isprintable():
                    c = '???'
            s1 += f'| {i:#04x} '
            s2 += f'|  {i:3d} '
            s3 += f'| {c:4s} '
            s4 += '+------'
        body.append(s1)
        body.append(s2)
        body.append(s3)
        if upper_nibble < 15:
            body.append(s4)

    print(h1)
    print(h2)
    for line in body:
        print(line)


def html_list():
    """Print an ASCII Python 'list' in HTML format."""
    h1 = '<tr>'
    for lower_nibble in range(0, 16):
        h1 += f'<th>{lower_nibble:04b}</th>'
    h1 += '</tr>'
    body = []
    for upper_nibble in range(0, 16):
        s = f'<tr><th>{upper_nibble:04b}</th>'
        for lower_nibble in range(0, 16):
            i = (upper_nibble << 4) + lower_nibble
            c = ascii_names.get(i, f'&#x{i:02x};')
            s += f'<td>{i:#04x}</br>{i:3d}</br>{c}</td>'
        s += '</tr>'
        body.append(s)

    print('''<!DOCTYPE html>
<html>
<head>
    <title>ASCII Table</title>
</head>
<style>
table {
  border-collapse: collapse;
}
table, th, td {
    border: 1px solid black;
    padding: 8px;
    text-align: center;
}
th {
    border: 2px solid;
    vertical-align: middle;
}
tr {
    vertical-align: top;
}
</style>
<body>
    <h1>ASCII Table</h1>
    <pre>
''')
    print('ascii_list = [')
    for i in range(256):
        if i in ascii_names:
            c = ascii_names[i]
        else:
            c = str(chr(i))
            if not c.isprintable():
                c = f'&#x{i:02x};'
        if c == "'":
            print(f'    "{c}",  # {i} / 0x{i:02x} / {c}\r')
        elif c == '\\':
            print(f"    '\\',  # {i} / 0x{i:02x} / BACKSLASH\r")
        else:
            print(f"    '{c}',  # {i} / 0x{i:02x} / {c}\r")
    print(']')

    print('''
    </pre>
</body>
</html>
''')


def html_table():
    """Print an ASCII table in HTML format."""
    h1 = '<tr>'
    for lower_nibble in range(0, 16):
        h1 += f'<th>{lower_nibble:04b}</th>'
    h1 += '</tr>'
    body = []
    for upper_nibble in range(0, 16):
        s = f'<tr><th>{upper_nibble:04b}</th>'
        for lower_nibble in range(0, 16):
            i = (upper_nibble << 4) + lower_nibble
            c = ascii_names.get(i, f'&#x{i:02x};')
            s += f'<td>{i:#04x}</br>{i:3d}</br>{c}</td>'
        s += '</tr>'
        body.append(s)

    print('''<!DOCTYPE html>
<html>
<head>
    <title>ASCII Table</title>
</head>
<style>
table {
  border-collapse: collapse;
}
table, th, td {
    border: 1px solid black;
    padding: 8px;
    text-align: center;
}
th {
    border: 2px solid;
    vertical-align: middle;
}
tr {
    vertical-align: top;
}
</style>
<body>
    <h1>ASCII Table</h1>
    <table>
    <tr><th rowspan="2">Upper Nibble</th><th colspan="16">Lower Nibble</th></tr>
''')
    print(h1)
    for line in body:
        print(line)
    print('</table>')
    print('''
</body>
</html>
''')


def main():
    """It all happens here."""
    parser = argparse.ArgumentParser(description='Output an ASCII table.')
    parser.add_argument(
        '-f', '--format', default='text', type=str,
        choices=['html', 'list', 'python', 'text'],
        help='Output format for the table.')
    args = parser.parse_args()

    if args.format == 'html':
        html_table()
    elif args.format == 'list':
        html_list()
    elif args.format == 'python':
        text_list()
    else:
        text_table()


# This code is executed if the file is called as a stand-alone command.
if __name__ == '__main__':
    main()
