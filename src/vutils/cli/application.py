#
# File:    ./src/vutils/cli/application.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2021-07-07 02:34:26 +0200
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""Command-line interface application classes."""

import sys
from typing import TYPE_CHECKING

from vutils.cli.errors import AppExitError, ApplicationError

if TYPE_CHECKING:
    from typing import NoReturn

    from vutils.cli import (
        ApplicationMixinP,
        ExcType,
        ExitExcType,
        MainFuncType,
    )


class ApplicationMixin:
    """
    Mixin for creating CLI applications.

    :cvar EXIT_SUCCESS: The exit code signalizing success
    :cvar EXIT_FAILURE: The exit code signalizing failure
    :cvar EXIT_EXCEPTION: The exception raised by
        :meth:`~.ApplicationMixin.exit`

    :ivar __elist: The list of exceptions that should be caught by this
        instance

    Should be used together with :class:`~vutils.cli.logger.LoggerMixin` and
    :class:`~vutils.cli.io.StreamsProxyMixin`.
    """

    EXIT_SUCCESS: int = 0
    EXIT_FAILURE: int = 1
    EXIT_EXCEPTION: "ExitExcType" = AppExitError

    __elist: "list[ExcType]"

    def __init__(self: "ApplicationMixinP") -> None:
        """Initialize the mixin."""
        self.__elist = []
        self.catch(ApplicationError)

    def catch(self: "ApplicationMixinP", exc: "ExcType") -> None:
        """
        Register an exception to be caught.

        :param exc: The exception class

        Registered exceptions that are raised by
        :meth:`~.ApplicationMixin.main` are caught and passed to
        :meth:`~.ApplicationMixin.on_error` to be further processed.
        :exc:`~vutils.cli.errors.ApplicationError` is registered by default.
        """
        if exc not in self.__elist:
            self.__elist.append(exc)

    def error(
        self: "ApplicationMixinP", msg: str, ecode: int = 1
    ) -> "NoReturn":
        """
        Issue an error and exit.

        :param msg: The error message
        :param ecode: The exit code (default 1)
        :raises ~vutils.cli.errors.AppExitError: when invoked
        """
        self.lerror(msg)
        self.exit(ecode)

    def exit(self: "ApplicationMixinP", ecode: int) -> "NoReturn":
        """
        Exit the application by raising :exc:`~vutils.cli.errors.AppExitError`.

        :param ecode: The exit code
        :raises ~vutils.cli.errors.AppExitError: when invoked
        """
        raise type(self).EXIT_EXCEPTION(ecode)

    def main(self: "ApplicationMixinP", unused_argv: "list[str]") -> int:
        """
        Provide the application entry point.

        :param unused_argv: The list of application arguments
        :return: the exit code
        """
        return type(self).EXIT_SUCCESS

    def run(self: "ApplicationMixinP", argv: "list[str]") -> int:
        """
        Run the application.

        :param argv: The list of application arguments
        :return: the exit code
        :raises Exception: if the exception raised by
            :meth:`~.ApplicationMixin.main` is not handled

        Invoke :meth:`~.ApplicationMixin.main` with :arg:`argv` as its argument
        via :meth:`~.ApplicationMixin.epcall`.
        """
        return self.epcall(self.main, argv)

    def epcall(
        self: "ApplicationMixinP",
        epfunc: "MainFuncType",
        argv: "list[str]",
    ) -> int:
        """
        Call an application entry-point-specific function.

        :param epfunc: The application entry-point-specific function
        :param argv: The list of application arguments
        :return: the exit code
        :raises Exception: if the exception raised by :arg:`epfunc` is not
            handled

        Invoke :arg:`epfunc` with :arg:`argv` as its argument, handle the
        error, and either return the exit code returned by :arg:`epfunc` or the
        exit code returned by :meth:`~.ApplicationMixin.on_error` error
        handler.

        The purpose of this method is to allow to user to reuse the exception
        handling code.
        """
        try:
            retcode: int = epfunc(argv)
        except AppExitError as exc:
            retcode = exc.ecode
            self.on_exit(retcode)
        except tuple(self.__elist) as exc:
            retcode = self.on_error(exc)
        return retcode

    def on_exit(self: "ApplicationMixinP", ecode: int) -> None:
        """
        Specify what to do on :meth:`~.ApplicationMixin.exit`.

        :param ecode: The exit code

        By default, log the exit code if the verbosity level is set to 2 or
        higher.
        """
        self.linfo(f"Application exited with an exit code {ecode}\n", 2)

    def on_error(self: "ApplicationMixinP", exc: Exception) -> int:
        """
        Specify what to do on error.

        :param exc: The caught exception
        :return: the exit code

        Default implementation logs the error and returns 1.
        """
        self.lerror(f"Exception caught: {exc!r}\n")
        return type(self).EXIT_FAILURE

    @classmethod
    def start(
        cls: "type[ApplicationMixinP]", modname: str = "__main__"
    ) -> None:
        """
        Start the application.

        :param modname: The module name (default ``__main__``)

        If the module name is ``__main__``, run the application.
        """
        if modname == "__main__":
            sys.exit(cls().run(sys.argv))
