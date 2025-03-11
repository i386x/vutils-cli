#
# File:    ./src/vutils/cli/base/context.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2023-12-11 22:30:27 +0100
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""Application context."""

import sys


class Factory:
    """"""

    __slots__ = ()

    @staticmethod
    def build_config(unused_context):
        """
        """
        return Config()

    @staticmethod
    def build_streams(unused_context):
        """
        """
        return Streams(sys.stdin, sys.stdout, sys.stderr)

    @staticmethod
    def build_logger(context):
        """
        """
        return Logger.create(context, context.get_streams().get_error())


class Context:
    """Application context."""

    __progname: str
    __config: "BaseConfig"
    __streams: "Streams"
    __logger: "Logger"

    __slots__ = ("__progname", "__config", "__streams", "__logger")

    def __init__(self, progname, factory):
        """"""
        self.__progname = progname
        self.__config = factory.build_config(self)
        self.__streams = factory.build_streams(self)
        self.__logger = factory.build_logger(self)

    def get_progname(self):
        """"""
        return self.__progname

    def get_config(self):
        """"""
        return self.__config

    def get_streams(self):
        """"""
        return self.__streams

    def get_logger(self):
        """"""
        return self.__logger
