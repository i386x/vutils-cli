#
# File:    ./src/vutils/cli/formatter.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2023-10-12 01:06:19 +0200
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""Help screen formatter."""

import click.formatting


class Formatter(click.formatting.HelpFormatter):
    """"""

    __slots__ = ()

    def __init__(self, *args, **kwargs):
        """"""
        click.formatting.HelpFormatter.__init__(self, *args, **kwargs)

    def help_screen(self, cmd):
        """"""
        self.format_banner(cmd)
        self.format_usage(cmd)
        self.format_options(cmd)
        self.format_positionals(cmd)
        self.format_commands(cmd)
        self.format_footer(cmd)
        return ''.join(self.buffer)
