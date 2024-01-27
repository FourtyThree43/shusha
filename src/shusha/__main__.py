# SPDX-FileCopyrightText: 2023-present FourtyThree43 <shaqmwa@outlook.com>
#
# SPDX-License-Identifier: MIT


import sys

if __package__ is None and not hasattr(sys, 'frozen'):
    # direct call of __main__.py
    from pathlib import Path

    script_path = Path(__file__).resolve()
    sys.path.insert(0, str(script_path.parent.parent))

from shusha import ShushaDM

if __name__ == '__main__':
    ShushaDM.main(argv=sys.argv)
