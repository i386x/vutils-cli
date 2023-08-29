#
# File:    ./tests/unit/utils.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2021-09-12 10:54:19 +0200
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""
Unit tests utilities.

:const LOGFILE: The name of the log file
:const ERR_TEST: The test error code
:const MESSAGE: The test message
:const UKEY: The *unknown* key
:const CS_RESET_ALL: The reset all color style
:const CS_BRIGHT: The bright color style
:const CF_RESET: The reset foreground color style
:const CF_RED: The red foreground color style
:const CF_GREEN: The green foreground color style
:const CF_YELLOW: The yellow/brown foreground color style
:const CF_LIGHTYELLOW_EX: The yellow foreground color style
:const CF_BLUE: The blue foreground color style

.. |ApplicationMixin.on_exit| replace:: :meth:`ApplicationMixin.on_exit
   <vutils.cli.application.ApplicationMixin.on_exit>`
.. |ApplicationMixin.on_error| replace:: :meth:`ApplicationMixin.on_error
   <vutils.cli.application.ApplicationMixin.on_error>`
.. |LoggerMixin.linfo| replace:: :meth:`LoggerMixin.linfo
   <vutils.cli.logging.LoggerMixin.linfo>`
.. |LoggerMixin.lerror| replace:: :meth:`LoggerMixin.lerror
   <vutils.cli.logging.LoggerMixin.lerror>`
.. |ApplicationMixin.exit| replace:: :meth:`ApplicationMixin.exit
   <vutils.cli.application.ApplicationMixin.exit>`
.. |ApplicationMixin.error| replace:: :meth:`ApplicationMixin.error
   <vutils.cli.application.ApplicationMixin.error>`
.. |CommandMixin| replace:: :class:`~vutils.cli.optparse.CommandMixin`
.. |State| replace:: :class:`~vutils.cli.optparse.State`
.. |OptionParser.parse| replace::
   :meth:`OptionParser.parse <vutils.cli.optparse.OptionParser.parse>`
.. |CommandMixin.set_optval| replace::
   :meth:`CommandMixin.set_optval <vutils.cli.command.CommandMixin.set_optval>`
.. |Option| replace:: :class:`~vutils.cli.optparse.Option`
.. |CommandMixin.get_optval| replace::
   :meth:`CommandMixin.get_optval <vutils.cli.command.CommandMixin.get_optval>`
.. |CommandMixin.print_help| replace::
   :meth:`CommandMixin.print_help <vutils.cli.command.CommandMixin.print_help>`
.. |CommandMixin.print_version| replace::
   :meth:`CommandMixin.print_version
   <vutils.cli.command.CommandMixin.print_version>`
.. |CommandMixin.exit| replace::
   :meth:`CommandMixin.exit <vutils.cli.command.CommandMixin.exit>`
"""

import unittest.mock

from vutils.testing.mock import PatcherFactory, make_callable, make_mock
from vutils.testing.utils import AssertRaises

from vutils.cli.application import ApplicationMixin
from vutils.cli.command import CommandMixin
from vutils.cli.errors import ApplicationError
from vutils.cli.io import StreamsProxyMixin, nocolor
from vutils.cli.logging import LogFormatter, LoggerMixin
from vutils.cli.options import (
    HelpOption,
    VersionOption,
    flag,
    keyval,
    subcommand,
)
from vutils.cli.optparse import State, build_parser

LOGFILE = "log.txt"
ERR_TEST = 2
MESSAGE = "test message"
UKEY = "foo"
CS_RESET_ALL = "</color:all>"
CS_BRIGHT = "<color:bright>"
CF_RESET = "</color>"
CF_RED = "<color:red>"
CF_GREEN = "<color:green>"
CF_YELLOW = "<color:yellow>"
CF_LIGHTYELLOW_EX = "<color:light_yellow_ex>"
CF_BLUE = "<color:blue>"


def make_io_mock():
    """
    Make input/output mocking object.

    :return: the mocking object

    The returned mocking object accepts only calls to ``write`` method.
    """
    return make_mock(["write"])


def on_exit_log(ecode):
    """
    Make a log item issued by |ApplicationMixin.on_exit|.

    :param ecode: The exit code
    :return: the log item
    """
    return (f"Application exited with an exit code {ecode}\n", 2)


def on_error_log(exc):
    """
    Make a log item issued by |ApplicationMixin.on_error|.

    :param exc: The exception object
    :return: the log item
    """
    return (f"Exception caught: {exc}\n",)


def not_kv_option_msg(option):
    """
    Make a message about option not being a key-value option.

    :param option: The option
    :return: the message
    """
    return f"Option {option} is not a key-value option"


def value_required_msg(option):
    """
    Make a message about option requiring a value.

    :param option:
    :return: the message
    """
    return f"Option {option} requires a value"


def unknown_option_msg(option):
    """
    Make a message about unknown option.

    :param option: The option
    :return: the message
    """
    return f"Unknown option '{option}'"


def unknown_option_log(option):
    """
    Make a log message issued by unknown option check.

    :param option: The option
    :return: the log message
    """
    return (
        "ERROR: Exception caught: UnknownOptionError"
        f'(reason="{unknown_option_msg(option)}")\n'
    )


def unknown_command_log(command):
    """
    Make a log message issued by unknown command check.

    :param command: The command name
    :return: the log message
    """
    return f'ERROR: Exception caught: UnknownCommandError(name="{command}")\n'


class ModulePatcher(PatcherFactory):
    """
    Patcher for builtin, :mod:`sys` and :mod:`colorama` modules.

    :ivar mock_open: The :func:`open` mock
    :ivar sys_argv: The :data:`sys.argv` mock
    :ivar sys_exit: The :func:`sys.exit` mock
    :ivar sys_stdout: The :obj:`sys.stdout` mock
    :ivar sys_stderr: The :obj:`sys.stderr` mock
    :ivar colorama_style: The :obj:`colorama.Style` mock
    :ivar colorama_fore: The :obj:`colorama.Fore` mock
    """

    __slots__ = (
        "mock_open",
        "sys_argv",
        "sys_exit",
        "sys_stdout",
        "sys_stderr",
        "colorama_style",
        "colorama_fore",
    )

    @staticmethod
    def setup_colorama_style(style):
        """
        Set up :obj:`colorama.Style` mock.

        :param style: The :obj:`colorama.Style` mock
        """
        style.RESET_ALL = CS_RESET_ALL
        style.BRIGHT = CS_BRIGHT

    @staticmethod
    def setup_colorama_fore(fore):
        """
        Set up :obj:`colorama.Fore` mock.

        :param fore: The :obj:`colorama.Fore` mock
        """
        fore.RESET = CF_RESET
        fore.RED = CF_RED
        fore.GREEN = CF_GREEN
        fore.YELLOW = CF_YELLOW
        fore.LIGHTYELLOW_EX = CF_LIGHTYELLOW_EX
        fore.BLUE = CF_BLUE

    def setup(self):
        """Set up the patcher."""
        self.mock_open = unittest.mock.mock_open()
        self.sys_argv = make_mock()
        self.sys_exit = make_mock()
        self.sys_stdout = make_io_mock()
        self.sys_stderr = make_io_mock()
        self.colorama_style = make_mock(["RESET_ALL", "BRIGHT"])
        self.colorama_fore = make_mock(
            ["RESET", "RED", "GREEN", "YELLOW", "LIGHTYELLOW_EX", "BLUE"]
        )

        self.add_spec("builtins.open", new=self.mock_open)
        self.add_spec("sys.argv", new=self.sys_argv)
        self.add_spec("sys.exit", new=self.sys_exit)
        self.add_spec("sys.stdout", new=self.sys_stdout)
        self.add_spec("sys.stderr", new=self.sys_stderr)
        self.add_spec(
            "colorama.Style",
            self.setup_colorama_style,
            new=self.colorama_style,
        )
        self.add_spec(
            "colorama.Fore", self.setup_colorama_fore, new=self.colorama_fore
        )


class ErrorA(ApplicationError):
    """Test error."""

    __slots__ = ()

    def __init__(self):
        """Initialize the error."""
        ApplicationError.__init__(self)


class ErrorB(Exception):
    """Test error."""

    __slots__ = ()

    def __init__(self):
        """Initialize the error."""
        Exception.__init__(self)

    def __repr__(self):
        """
        Get the error representation.

        :return: the error representation
        """
        return f"{type(self).__name__}()"

    def __str__(self):
        """
        Get the error representation.

        :return: the error representation
        """
        return repr(self)


class LoggerA:
    """
    Test logger mixin.

    :ivar stream: The stream mock
    """

    __slots__ = ("stream",)

    def __init__(self):
        """Initialize the logger."""
        self.stream = []

    def linfo(self, *args):
        """
        Implement dummy |LoggerMixin.linfo| that records its arguments.

        :param args: Positional arguments
        """
        self.stream.append(args)

    def lerror(self, *args):
        """
        Implement dummy |LoggerMixin.lerror| that records its arguments.

        :param args: Positional arguments
        """
        self.stream.append(args)


class LoggerB(LoggerMixin, StreamsProxyMixin):
    """Test logger."""

    __slots__ = ()

    def __init__(self):
        """Initialize the logger."""
        LoggerMixin.__init__(self)
        StreamsProxyMixin.__init__(self)


class ApplicationA(ApplicationMixin, LoggerA):
    """
    Test application.

    :cvar CMD_EXIT: The exit command name
    :cvar CMD_ERROR: The error command name
    :cvar CMD_XERROR: The extra error command name
    :cvar CMD_RAISE_A: The ``raise ErrorA`` command name
    :cvar CMD_RAISE_B: The ``raise ErrorB`` command name
    """

    CMD_EXIT = "test-exit"
    CMD_ERROR = "test-error"
    CMD_XERROR = "test-error-extra"
    CMD_RAISE_A = "test-raise-a"
    CMD_RAISE_B = "test-raise-b"

    __slots__ = ()

    def __init__(self):
        """Initialize the application."""
        ApplicationMixin.__init__(self)
        LoggerA.__init__(self)

    def main(self, argv):
        """
        Provide the application entry point.

        :param argv: The list of arguments
        :return: the exit code
        :raises .ErrorA: when 0th argument is set to ``test-raise-a``
        :raises .ErrorB: when 0th argument is set to ``test-raise-b``

        The application behaves like follows:

        * with no argument return 0
        * with unknown argument return 1
        * with 0th argument set to ``test-exit`` calls |ApplicationMixin.exit|
          with :const:`.ERR_TEST`
        * with 0th argument set to ``test-error`` calls
          |ApplicationMixin.error| with :const:`.MESSAGE`
        * with 0th argument set to ``test-error-extra`` calls
          |ApplicationMixin.error| with :const:`.MESSAGE` and
          :const:`.ERR_TEST`
        * with 0th argument set to ``test-raise-a`` raises :exc:`.ErrorA`
        * with 0th argument set to ``test-raise-b`` raises :exc:`.ErrorB`
        """
        cls = type(self)

        if not argv:
            return cls.EXIT_SUCCESS
        cmd = argv[0]

        if cmd == cls.CMD_EXIT:
            self.exit(ERR_TEST)
        elif cmd == cls.CMD_ERROR:
            self.error(MESSAGE)
        elif cmd == cls.CMD_XERROR:
            self.error(MESSAGE, ERR_TEST)
        elif cmd == cls.CMD_RAISE_A:
            raise ErrorA()
        elif cmd == cls.CMD_RAISE_B:
            raise ErrorB()

        return cls.EXIT_FAILURE


def make_command_mock():
    """
    Make a mock of |CommandMixin|.

    :return: the mock object that mocks |CommandMixin|
    """
    slots = [
        "set_optval",
        "set_opts_defaults",
        "get_optval",
        "print_help",
        "print_version",
        "exit",
    ]
    mock = make_mock(slots)
    type(mock).EXIT_SUCCESS = 0
    mock.get_optval = make_callable(0)
    return mock


def make_state_mock():
    """
    Make a mock of |State|.

    :return: the mock object that mocks |State|
    """
    state = make_mock()
    state.cmd = make_command_mock()
    return state


class ParseAndVerifyMixin:
    """Extend class about :meth:`~.ParseAndVerifyMixin.parse_and_verify`."""

    __slots__ = ()

    def build_parser(self):
        """
        Build an option parser.

        :return: the option parser
        """
        raise NotImplementedError()

    def parse_and_verify(self, args, **result):
        """
        Run |OptionParse.parse| and verify the result.

        :param args: The list of arguments to be parsed
        :param result: Key-value arguments characterizing the expected result

        :arg:`result` supports following keys:

        * ``tail`` is an expected list of unprocessed arguments. If it is
          :obj:`None` (default), unprocessed arguments are not verified.
        * ``raises`` is an exception that is expected to be raised, otherwise
          it is :obj:`None`.
        * ``excstr`` is an expected value returned by :class:`str` when applied
          on caught exception. If it is :obj:`None` (default), the value is
          ignored.
        * ``mock_calls`` is a list of expected calls to
          |CommandMixin.set_optval|.
        """
        tail = result.get("tail")
        raises = result.get("raises")
        excstr = result.get("excstr")
        mock_calls = result.get("mock_calls", [])

        parser = self.build_parser()
        command = make_command_mock()
        state = State(command, args)

        parse = parser.parse
        if raises:
            parse = AssertRaises(self, parse, raises)

        parse(state)
        if raises and excstr:
            self.assertEqual(str(parse.get_exception()), excstr)
        if tail is not None:
            self.assertEqual(state.argv, tail)
        self.assert_called_with(command.set_opts_defaults, parser)
        self.assertEqual(command.set_optval.mock_calls, mock_calls)


class OptionTesterMixin:
    """Mixin for testing |Option| subclasses."""

    __slots__ = ()

    def run_and_verify(self, *args, **kwargs):
        """
        Build a parser, run it, and verify result.

        :param args: Positional arguments to the |Option| subclass
        :param kwargs: Key-value arguments

        Key-value arguments are also passed to the |Option| subclass, except
        these:

        * ``option`` (an |Option| subclass instance builder)
        * ``argv`` (a list of arguments to be parsed)
        * ``raises`` (an expected exception to be raised)
        * ``excstr`` (an expected :class:`str` value of caught exception)
        * ``set_optval_calls`` (a list of expected calls to
          |CommandMixin.set_optval|)
        * ``get_optval_calls`` (a list of expected calls to
          |CommandMixin.get_optval|)
        * ``print_help_calls`` (a list of expected calls to
          |CommandMixin.print_help|)
        * ``print_version_calls`` (a list of expected calls to
          |CommandMixin.print_version|)
        * ``exit_calls`` (a list of expected calls to |CommandMixin.exit|)
        """
        option = kwargs.pop("option")
        argv = kwargs.pop("argv", [])
        raises = kwargs.pop("raises", None)
        excstr = kwargs.pop("excstr", None)
        meths = (
            "set_optval",
            "get_optval",
            "print_help",
            "print_version",
            "exit",
        )
        calls = {meth: kwargs.pop(f"{meth}_calls", []) for meth in meths}

        parser = build_parser(option(*args, **kwargs))
        command = make_command_mock()
        state = State(command, argv)

        parse = parser.parse
        if raises:
            parse = AssertRaises(self, parse, raises)

        parse(state)
        if raises and excstr:
            self.assertEqual(str(parse.get_exception()), excstr)
        for meth in meths:
            self.assertEqual(getattr(command, meth).mock_calls, calls[meth])


class SampleCommandBase(CommandMixin, LoggerMixin, StreamsProxyMixin):
    """Sample command base class."""

    __slots__ = ()

    def __init__(self, parent=None, stream=None):
        """
        Initialize the sample command base.

        :param parent: The parent of the command
        :param stream: The stream log messages are written to
        """
        CommandMixin.__init__(self, parent)
        LoggerMixin.__init__(self)
        StreamsProxyMixin.__init__(self)
        self.set_log_style(LogFormatter.INFO, nocolor)
        self.set_log_style(LogFormatter.ERROR, nocolor)
        self.set_streams(stream, stream)

    def initialize(self):
        """Perform delayed initialization actions."""
        self.linfo("initializing application")
        CommandMixin.initialize(self)

    def print_help(self):
        """Print help."""
        self.linfo("application help")
        CommandMixin.print_help(self)

    def print_version(self):
        """Print version."""
        self.linfo("application version")
        CommandMixin.print_version(self)

    def print_options(self, options):
        """
        Print the given options.

        :param options: The list of options
        """
        for name in options:
            self.linfo(f"{name}: {self.get_optval(name)}")

    def main(self, argv):
        """
        Provide the command entry point.

        :param argv: The list of arguments
        :return: the exit code
        """
        self.linfo(f"unprocessed arguments: {argv!r}")
        return CommandMixin.main(self, argv)


def common_options():
    """
    Build help and version options.

    :return: the tuple with help and version options
    """
    return (HelpOption(), VersionOption())


class SampleApplication(SampleCommandBase):
    """
    Sample application.

    :ivar __stream: The stream log messages are written to
    """

    OPTSPEC = (
        common_options(),
        keyval("input", "i", "input file"),
        keyval("output", "o", "output file", default="a.out"),
        subcommand("COMMAND", "a command"),
    )

    __slots__ = ("__stream",)

    def __init__(self, stream):
        """
        Initialize the application.

        :param stream: The stream log messages are written to
        """
        self.__stream = stream
        SampleCommandBase.__init__(self, stream=stream)

    def load_subcommand(self, name):
        """
        Load a subcommand.

        :param name: The name of a subcommand
        """
        if name == "one":
            return OneCmd(self, self.__stream)
        if name == "two":
            return TwoCmd(self, self.__stream)
        return SampleCommandBase.load_subcommand(self, name)

    def main(self, argv):
        """
        Provide the application entry point.

        :param argv: The list of arguments
        :return: the exit code
        """
        self.print_options(["help", "version", "input", "output"])
        return SampleCommandBase.main(self, argv)


class OneCmd(SampleCommandBase):
    """Command ``one``."""

    OPTSPEC = (
        common_options(),
        flag("tty", "t", "allocate pseudo-terminal"),
        flag("yes", "y", "assume yes to all questions"),
    )

    __slots__ = ()

    def __init__(self, parent, stream):
        """
        Initialize the command.

        :param parent: The parent of the command
        :param stream: The stream log messages are written to
        """
        SampleCommandBase.__init__(self, parent, stream)

    def main(self, argv):
        """
        Provide the command entry point.

        :param argv: The list of arguments
        :return: the exit code
        """
        self.print_options(
            ["help", "version", "input", "output", "tty", "yes"],
        )
        return SampleCommandBase.main(self, argv)


class TwoCmd(SampleCommandBase):
    """Command ``two``."""

    OPTSPEC = (
        common_options(),
        keyval("name", "n", "a name of a subject"),
        flag("quiet", "q", "do not print anything"),
    )

    __slots__ = ()

    def __init__(self, parent, stream):
        """
        Initialize the command.

        :param parent: The parent of the command
        :param stream: The stream log messages are written to
        """
        SampleCommandBase.__init__(self, parent, stream)

    def main(self, argv):
        """
        Provide the command entry point.

        :param argv: The list of arguments
        :return: the exit code
        """
        self.print_options(["help", "version", "name", "quiet"])
        return SampleCommandBase.main(self, argv)
