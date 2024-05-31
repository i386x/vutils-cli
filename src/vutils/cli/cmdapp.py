#
# File:    ./src/vutils/cli/cmdapp.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2023-10-12 01:05:30 +0200
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""Command-based application."""


class Command(CommandMixin, LoggerMixin, StreamsProxyMixin):
    """"""

    NAME = None
    SUBCOMMANDS = {}

    __slots__ = ()

    def __init__(self, parent):
        """"""
        CommandMixin.__init__(self, parent)
        LoggerMixin.__init__(self)
        StreamsProxyMixin.__init__(self)

    def print_help(self):
        """"""

    def load_subcommand(self, name):
        """"""
        loader = type(self).SUBCOMMANDS.get(name)
        if loader is None:
            raise UnknownCommandError(name)
        command = loader(self)
        command.inject_streams(self)
        command.inject_logger_props(self)
        return command


class Application(Command):
    """"""

    __slots__ = ()

    def __init__(self):
        """"""
        Command.__init__(self, None)

    def print_version(self):
        """"""
