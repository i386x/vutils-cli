#
# File:    ./tests/unit/test_errors.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2021-08-28 21:14:57 +0200
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""
Test :mod:`vutils.cli.errors` module.

.. |ApplicationError| replace:: :exc:`~vutils.cli.errors.ApplicationError`
.. |AppExitError| replace:: :exc:`~vutils.cli.errors.AppExitError`
.. |UnknownCommandError| replace::
   :exc:`~vutils.cli.errors.UnknownCommandError`
.. |OptParseError| replace:: :exc:`~vutils.cli.errors.OptParseError`
.. |UnknownOptionError| replace:: :exc:`~vutils.cli.errors.UnknownOptionError`
"""

from vutils.testing.testcase import TestCase

from vutils.cli.errors import (
    AppExitError,
    ApplicationError,
    OptParseError,
    UnknownCommandError,
    UnknownOptionError,
)


class ApplicationErrorTestCase(TestCase):
    """Test case for |ApplicationError|."""

    __slots__ = ()

    def test_application_error(self):
        """Test the |ApplicationError| basic usage."""
        with self.assertRaises(ApplicationError) as context_manager:
            raise ApplicationError()
        exception = context_manager.exception

        self.assertEqual(exception.detail(), "")
        self.assertEqual(repr(exception), "ApplicationError()")
        self.assertEqual(str(exception), repr(exception))


class AppExitErrorTestCase(TestCase):
    """Test case for |AppExitError|."""

    __slots__ = ()

    def test_app_exit_error(self):
        """Test the |AppExitError| basic usage."""
        ecode = 2
        self.do_test(1)
        self.do_test(ecode, ecode)

    def do_test(self, value, *args):
        """
        Do the |AppExitError| basic usage test.

        :param value: The expected value of exit code
        :param args: Positional arguments to be passed to the |AppExitError|
            constructor
        """
        with self.assertRaises(AppExitError) as context_manager:
            raise AppExitError(*args)
        exception = context_manager.exception

        self.assertEqual(exception.ecode, value)
        self.assertEqual(f"{exception}", f"AppExitError(exit_code={value})")


class UnknownCommandErrorTestCase(TestCase):
    """Test case for |UnknownCommandError|."""

    __slots__ = ()

    def test_unknown_command_error(self):
        """Test the |UnknownCommandError| basic usage."""
        name = "foo"

        with self.assertRaises(UnknownCommandError) as context_manager:
            raise UnknownCommandError(name)
        exception = context_manager.exception

        self.assertEqual(exception.name, name)
        self.assertEqual(
            repr(exception),
            f'UnknownCommandError(name="{name}")',
        )
        self.assertEqual(str(exception), f"Unknown (sub)command: {name}")


class OptParseErrorTestCase(TestCase):
    """Test case for |OptParseError|."""

    __slots__ = ()

    def test_opt_parse_error(self):
        """Test the |OptParseError| basic usage."""
        reason = "Bad option `--foo'"

        with self.assertRaises(OptParseError) as context_manager:
            raise OptParseError(reason)
        exception = context_manager.exception

        self.assertEqual(exception.reason, reason)
        self.assertEqual(repr(exception), f'OptParseError(reason="{reason}")')
        self.assertEqual(f"{exception}", reason)


class UnknownOptionErrorTestCase(TestCase):
    """Test case for |UnknownOptionError|."""

    __slots__ = ()

    def test_unknown_option_error(self):
        """Test the |UnknownOptionError| basic usage."""
        name = "--foo"

        with self.assertRaises(UnknownOptionError) as context_manager:
            raise UnknownOptionError(name)
        exception = context_manager.exception

        self.assertEqual(
            repr(exception),
            f"UnknownOptionError(reason=\"Unknown option '{name}'\")",
        )
        self.assertEqual(f"{exception}", f"Unknown option '{name}'")
