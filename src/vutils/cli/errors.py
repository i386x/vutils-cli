#
# File:    ./src/vutils/cli/errors.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2021-07-09 22:37:01 +0200
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""Definitions of errors."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import ClassVar


class ApplicationError(Exception):
    """
    Base class for all application errors.

    :cvar DETAIL: The detail about the error
    """

    DETAIL: "ClassVar[str]" = ""

    __slots__ = ()

    def __init__(self) -> None:
        """Initialize the error object."""
        Exception.__init__(self)

    def detail(self) -> str:
        """
        Get the error detail.

        :return: the error detail
        """
        return type(self).DETAIL

    def __repr__(self) -> str:
        """
        Get the error representation.

        :return: the error representation
        """
        return f"{type(self).__name__}({self.detail()})"

    def __str__(self) -> str:
        """
        Get the error representation (:class:`str` alias).

        :return: the error representation
        """
        return repr(self)


class AppExitError(ApplicationError):
    """
    Used to signal the exit.

    :ivar ecode: The exit code
    """

    ecode: int

    __slots__ = ("ecode",)

    def __init__(self, ecode: int = 1) -> None:
        """
        Initialize the error object.

        :param ecode: The exit code (default 1)
        """
        ApplicationError.__init__(self)
        self.ecode = ecode

    def detail(self) -> str:
        """
        Get the error detail.

        :return: the error detail
        """
        return f"exit_code={self.ecode}"


class UnknownCommandError(ApplicationError):
    """
    Raised when a command given on CLI is not known.

    :ivar name: The command name
    """

    name: str

    __slots__ = ("name",)

    def __init__(self, name: str) -> None:
        """
        Initialize the error object.

        :param name: The command name
        """
        ApplicationError.__init__(self)
        self.name = name

    def detail(self) -> str:
        """
        Get the error detail.

        :return: the error detail
        """
        return f'name="{self.name}"'

    def __str__(self) -> str:
        """
        Generate the error message.

        :return: the error message
        """
        return f"Unknown (sub)command: {self.name}"


class OptParseError(ApplicationError):
    """
    Raised when option parsing goes wrong.

    :ivar reason: The reason of error
    """

    reason: str

    __slots__ = ("reason",)

    def __init__(self, reason: str) -> None:
        """
        Initialize the error object.

        :param reason: The reason of error
        """
        ApplicationError.__init__(self)
        self.reason = reason

    def detail(self) -> str:
        """
        Get the error detail.

        :return: the error detail
        """
        return f'reason="{self.reason}"'

    def __str__(self) -> str:
        """
        Generate the error message.

        :return: the error message
        """
        return self.reason


class UnknownOptionError(OptParseError):
    """Used for unknown option reporting."""

    __slots__ = ()

    def __init__(self, option: str) -> None:
        """
        Initialize the error object.

        :param option: The option
        """
        OptParseError.__init__(self, f"Unknown option '{option}'")
