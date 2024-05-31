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

    @staticmethod
    def build_config(unused_context):
        """
        """
        return Config()

    def build_streams(unused_context):
        """
        """
        return Streams(sys.stdin, sys.stdout, sys.stderr)

class Context:
    """Application context."""

    config: "BaseConfig"
    istream: "TextIO"
    ostream: "TextIO"
    estream: "TextIO"
    lstream: "LogStream"
    logger: "Logger"

    __slots__ = ("streams", "logger")

    @staticmethod
    def create_config():
        return Config()

    @staticmethod
    def create_streams(config):
        istream = StreamProxy(sys.stdin, config)
        ostream = StreamProxy(sys.stdout, config)
        estream = StreamProxy(sys.stderr, config)
        lstream = LogStream(estream, config)
        return {
            INPUT_STREAM: istream,
            OUTPUT_STREAM: ostream,
            ERROR_STREAM: estream,
            LOG_STREAM: lstream,
        }

    @staticmethod
    def create_logger(config, streams):
        return LoggerAdapter.create(config, streams)

    @classmethod
    def create(cls):
        """"""
        config = cls.create_config()
        streams = cls.create_streams(config)
        logger = cls.create_logger(config, streams)
        return cls(config, streams, logger)

    def __init__(self, factory):
        """"""
        self.__config = factory.build_config(self)
        self.__streams = factory.build_streams(self)
        self.__logger = factory.build_logger(self)

    def get_config(self):
        """"""
        return self.__config

    def get_streams(self):
        """"""
        return self.__streams

    def get_logger(self):
        """"""
        return self.__logger
