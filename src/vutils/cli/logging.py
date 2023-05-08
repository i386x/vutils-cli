#
# File:    ./src/vutils/cli/logging.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2021-07-09 16:31:58 +0200
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""Logging support."""

from typing import TYPE_CHECKING

from vutils.cli.io import blue, brown, red, yellow

if TYPE_CHECKING:
    import pathlib
    from typing import ClassVar

    from vutils.cli import ColorFuncType, LoggerMixinP


class LogFormatter:
    """
    Define how to format log messages.

    :cvar INFO: The info message type
    :cvar WARNING: The warning message type
    :cvar ERROR: The error message type
    :cvar DEBUG: The debug message type
    :cvar FORMAT: The log item format

    :ivar __colormap: The mapping between message types and their colors
    """

    INFO: "ClassVar[str]" = "info"
    WARNING: "ClassVar[str]" = "warning"
    ERROR: "ClassVar[str]" = "error"
    DEBUG: "ClassVar[str]" = "debug"
    FORMAT: "ClassVar[str]" = "{label}: {message}"

    __colormap: "dict[str, ColorFuncType]"

    __slots__ = ("__colormap",)

    def __init__(self) -> None:
        """Initialize the formatter."""
        self.__colormap = {}
        cls: "type[LogFormatter]" = type(self)
        self.set_style(cls.INFO, blue)
        self.set_style(cls.WARNING, yellow)
        self.set_style(cls.ERROR, red)
        self.set_style(cls.DEBUG, brown)

    def set_style(self, name: str, color: "ColorFuncType") -> None:
        """
        Set the style for a given type of log messages.

        :param name: The name of the message type
        :param color: The message color

        The supported types of log messages are:

        * :attr:`~.LogFormatter.INFO` for info messages
        * :attr:`~.LogFormatter.WARNING` for warning messages
        * :attr:`~.LogFormatter.ERROR` for error messages
        * :attr:`~.LogFormatter.DEBUG` for debug messages
        """
        self.__colormap[name] = color

    def colorize(self, name: str, msg: str, nocolor: bool = False) -> str:
        """
        Colorize the log message.

        :param name: The name of the message type
        :param msg: The message to be colorized
        :param nocolor: The no color flag (default :obj:`False`)
        :return: the colorized message

        The color of a given log message type is set by
        :meth:`~.LogFormatter.set_style`. When :arg:`nocolor` is :obj:`True`,
        the message is not colorized.
        """
        if nocolor:
            return msg
        color: "ColorFuncType | None" = self.__colormap.get(name, None)
        if color is None:
            return msg
        return color(msg)

    def format(self, name: str, msg: str) -> str:
        """
        Format the log message.

        :param name: The name of the message type
        :param msg: The message to be formatted
        :return: the formatted message
        """
        return type(self).FORMAT.format(label=name.upper(), message=msg)


class LoggerMixin:
    """
    Logging facility mixin.

    :ivar __logpath: The path to the log file
    :ivar __formatter: The log formatter
    :ivar __vlevel: The verbosity level
    :ivar __dlevel: The debug level

    Should be used together with
    :class:`~vutils.cli.application.ApplicationMixin` and
    :class:`~vutils.cli.io.StreamsProxyMixin`.
    """

    __logpath: "pathlib.Path | None"
    __formatter: LogFormatter
    __vlevel: int
    __dlevel: int

    def __init__(self: "LoggerMixinP") -> None:
        """
        Initialize the logger.

        The default formatter is an instance of :class:`.LogFormatter`, the
        default verbosity level is 1, and the default debug level is 0.
        """
        self.__logpath = None
        self.__formatter = LogFormatter()
        self.__vlevel = 1
        self.__dlevel = 0

    def set_logger_props(
        self: "LoggerMixinP",
        logpath: "pathlib.Path | None" = None,
        formatter: "LogFormatter | None" = None,
        vlevel: "int | None" = None,
        dlevel: "int | None" = None,
    ) -> None:
        """
        Set logger properties.

        :param logpath: The path to the log file
        :param formatter: The log formatter
        :param vlevel: The verbosity level
        :param dlevel: The debug level

        The property is set only if it is not :obj:`None`.
        """
        if logpath is not None:
            self.__logpath = logpath
        if formatter is not None:
            self.__formatter = formatter
        if vlevel is not None:
            self.__vlevel = vlevel
        if dlevel is not None:
            self.__dlevel = dlevel

    def set_log_style(
        self: "LoggerMixinP", name: str, color: "ColorFuncType"
    ) -> None:
        """
        Set the style of log messages.

        :param name: The name of the message type
        :param color: The message color

        This method changes the formatter object's state set by
        :meth:`~.LoggerMixin.set_logger_props`. Therefore, it is recommended to
        use this method after :meth:`~.LoggerMixin.set_logger_props`.
        """
        self.__formatter.set_style(name, color)

    def wlog(self: "LoggerMixinP", msg: str) -> None:
        """
        Write the message to the log file.

        :param msg: The message
        """
        if self.__logpath is not None:
            with open(
                self.__logpath,
                mode="a",
                encoding="utf-8",
                errors="backslashreplace",
            ) as log:
                log.write(msg)

    def linfo(self: "LoggerMixinP", msg: str, vlevel: int = 1) -> None:
        """
        Issue the info message.

        :param msg: The message
        :param vlevel: The verbosity level (default 1)

        The message is issued when the verbosity level is less or equal to the
        verbosity level treshold set by :meth:`~.LoggerMixin.set_logger_props`
        (default 1).
        """
        if vlevel <= self.__vlevel:
            self.__do_log(LogFormatter.INFO, msg)

    def lwarn(self: "LoggerMixinP", msg: str) -> None:
        """
        Issue the warning message.

        :param msg: The message
        """
        self.__do_log(LogFormatter.WARNING, msg)

    def lerror(self: "LoggerMixinP", msg: str) -> None:
        """
        Issue the error message.

        :param msg: The message
        """
        self.__do_log(LogFormatter.ERROR, msg)

    def ldebug(self: "LoggerMixinP", msg: str, dlevel: int = 1) -> None:
        """
        Issue the debug message.

        :param msg: The message
        :param dlevel: The debug level (default 1)

        The message is issued when the debug level is less or equal to the
        debug level treshold set by :meth:`~.LoggerMixin.set_logger_props`
        (default 0).
        """
        if dlevel <= self.__dlevel:
            self.__do_log(LogFormatter.DEBUG, msg)

    def __do_log(self: "LoggerMixinP", name: str, msg: str) -> None:
        """
        Write the message to both the log file and the error output stream.

        :param name: The name of message type
        :param msg: The message

        Format the message and write it to the log file (non-colorized) and to
        the error output stream (colorized).
        """
        msg = self.__formatter.format(name, msg)
        self.wlog(msg)
        self.werr(self.__formatter.colorize(name, msg))
