#
# File:    ./src/vutils/cli/base/logging.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2021-07-09 16:31:58 +0200
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""Logging support."""

import logging
from typing import TYPE_CHECKING

from vutils.cli.base.config import (
    COLOR_KEY,
    DLEVEL_KEY,
    LOG_FORMAT_KEY,
    LOG_LABEL_COLOR_KEY,
    LOG_MESSAGE_COLOR_KEY,
    VLEVEL_KEY,
    BaseConfig,
)
from vutils.cli.base.io import ColorFactory, maybe_strip_colors

if TYPE_CHECKING:
    from logging import LogRecord
    from typing import TextIO

#: The ``logging_config`` extra log record attribute
LOGGING_CONFIG_ATTR: str = "logging_config"
#: The ``color_reset`` keyword
KW_COLOR_RESET: str = "color_reset"
#: The ``label_color`` keyword
KW_LABEL_COLOR: str = "label_color"
#: The ``message_color`` keyword
KW_MESSAGE_COLOR: str = "message_color"


class LogFilter(logging.Filter):
    """Custom logging filter."""

    __slots__ = ()

    def filter(self, record: "LogRecord") -> bool:
        """
        Filter log records.

        :param record: The log record
        :return: :obj:`True` if the log record can pass through

        Warnings and errors are already allowed to pass. If the log record is
        an info message, it passes if its verbosity level is not above the
        verbosity level set by the application. If it is a debug message, it
        passes if its debug level is not above the debug level set by the
        application. If the debug level set by the application is greater than
        zero, all info messages are allowed to pass despite their verbosity
        level.

        The default verbosity level of info messages is 0 and the default debug
        level of debug messages is 1.
        """
        if record.levelno > logging.INFO:
            return True
        config = getattr(record, LOGGING_CONFIG_ATTR)
        # The default ``vlevel`` of ``Logger.info`` is 0, i.e. basic info
        # messages are displayed even there is no ``-v`` flag set
        level = getattr(record, VLEVEL_KEY, 0)
        if (
            record.levelno > logging.DEBUG
            and (
                level <= config.getval(VLEVEL_KEY)
                or config.getval(DLEVEL_KEY) > 0
            )
        ):
            return True
        # The default ``dlevel`` of ``Logger.debug`` is 1, i.e. basic debug
        # messages are displayed only if ``-d`` or higher flag is set
        level = getattr(record, DLEVEL_KEY, 1)
        if record.levelno > 0 and level <= config.getval(DLEVEL_KEY):
            return True
        return False


class LogRecordFormatter(logging.Formatter):
    """Custom formatter for log records."""

    #: The set of styles used to format a log record
    styles: "dict[str, dict[str, str]]"

    __slots__ = ("styles",)

    def __init__(self, config: "BaseConfig", colored: bool = True) -> None:
        """
        Initialize the formatter.

        :param config: The configuration manager
        :param colored: The flag indicating whether the log record should be
            colored
        """
        logging.Formatter.__init__(
            self, config.getval(LOG_FORMAT_KEY), style="{"
        )
        color_factory = ColorFactory(colored)
        self.styles = {}
        for style in logging.getLevelNamesMapping().keys():
            self.add_style(config, style.lower(), color_factory)

    def add_style(
        self, config: "BaseConfig", style: str, color_factory: ColorFactory
    ) -> None:
        """
        Add a style to the set of styles.

        :param config: The configuration manager
        :param style: The name of the style
        :param color_factory: The color factory

        :arg:`style` coincides with :attr:`LogRecord.levelname
        <logging.LogRecord.levelname>` in lower-case. If :arg:`config` has no
        color configuration for :arg:`style`, no colors are used during the log
        record formatting.
        """
        color_reset = color_factory.reset_all()
        label_color = color_factory.color(
            config.trygetval(
                LOG_LABEL_COLOR_KEY.format(level=style), default=""
            )
        )
        message_color = color_factory.color(
            config.trygetval(
                LOG_MESSAGE_COLOR_KEY.format(level=style), default=""
            )
        )
        if (
            label_color == color_reset
            and message_color == color_reset
            and color_reset != ""
        ):
            color_reset = ""
            label_color = ""
            message_color = ""
        self.styles[style] = {
            KW_COLOR_RESET: color_reset,
            KW_LABEL_COLOR: label_color,
            KW_MESSAGE_COLOR: message_color,
        }

    def format(self, record: "LogRecord") -> str:
        """
        Format the log record.

        :param record: The log record
        :return: the formatted message based upon the log record
        """
        style = record.levelname.lower()
        record.__dict__.update(self.styles[style])
        return logging.Formatter.format(self, record)


class LogStreamHandler(logging.StreamHandler):
    """Custom log stream handler."""

    __slots__ = ()

    def format(self, record: "LogRecord") -> str:
        """
        Format the log record.

        :param record: The log record
        :return: the final message to be logged based upon the log record

        Build the final log record message from the log record by applying
        formatters on it. Strip colors from the final message when needed.
        """
        config = getattr(record, LOGGING_CONFIG_ATTR)
        message = logging.StreamHandler.format(self, record)
        return maybe_strip_colors(
            message, self.stream, config.getval(COLOR_KEY)
        )


class LogFileHandler(logging.FileHandler):
    """Custom log file handler."""

    __slots__ = ()

    def __init__(self, filename: str) -> None:
        """
        Initialize the file handler.

        :param filename: The path to the log file

        The log file is opened in the text mode for appending with the content
        encoded in UTF-8.
        """
        logging.FileHandler.__init__(self, filename, "a", encoding="utf-8")

    def _open(self) -> "TextIO":
        """
        Open the log file.

        :return: the stream associated with the log file ready for writing

        By overriding this method it is ensured that encoding errors are
        handled using ``backslashreplace`` strategy also in older versions of
        :mod:`logging`.
        """
        openfunc = getattr(self, "_builtin_open", open)
        return openfunc(
            self.baseFilename,
            self.mode,
            encoding=self.encoding,
            errors="backslashreplace",
        )


class Logger(logging.LoggerAdapter):
    """Custom logger."""

    __slots__ = ()

    def log_path(context: "Context") -> str:
        """
        """
        now = time.localtime()
        return context.get_config().getval(LOG_PATH_KEY).format(
            progname=context.get_progname(),
            today=time.strftime("%Y%m%d", now),
            now=time.strftime("%H%M%S", now),
        )

    @classmethod
    def create(cls, config: "BaseConfig", stream: "TextIO") -> "Logger":
        """
        Create and initialize an instance of the custom logger.

        :param config: The configuration manager
        :param stream: The stream log messages should be send to in addition to
            writing them to the log file
        :return: the instance of the custom logger
        """
        logger = logging.getLogger()
        logger.filters.clear()
        logger.handlers.clear()
        logger.propagate = False
        logger.setLevel(logging.DEBUG)
        logger.addFilter(LogFilter())

        sh = LogStreamHandler(stream)
        sh.setLevel(logging.DEBUG)
        sh.setFormatter(LogRecordFormatter(config, True))
        logger.addHandler(sh)

        filename = Logger.log_path(context)
        ensure_directory(dirname(filename))
        fh = LogFileHandler(filename)
        fh.setLevel(logging.DEBUG)
        fh.setFromatter(LogRecordFormatter(config, False))
        logger.addHandler(fh)

        return cls(logger, config)

    def __init__(self, logger, config):
        """"""
        logging.LoggerAdapter.__init__(
            self, logger, {LOGGING_CONFIG_KEY: config}
        )
