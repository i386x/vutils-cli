#
# File:    ./src/vutils/cli/command.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2023-01-09 18:13:53 +0100
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""
CLI (sub)commands support.

.. |ApplicationMixin| replace::
   :class:`~vutils.cli.application.ApplicationMixin`
"""

from typing import TYPE_CHECKING, cast

from vutils.cli.application import ApplicationMixin
from vutils.cli.constants import SUBCOMMAND_SLOT
from vutils.cli.errors import UnknownCommandError
from vutils.cli.optparse import OptionSet, PosArg, State, build_parser

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import ClassVar

    from vutils.cli import BuildParserFuncType, CommandProtocol, OptSpecType
    from vutils.cli.optparse import Option, OptionParser


class CommandMixin(ApplicationMixin):
    """
    Add (sub)commands support to |ApplicationMixin|.

    :cvar OPTSPEC: The specification of options for this command
    :cvar STATE_CLS: The class used to create the option parser state
    :cvar BUILD_PARSER_FUNC: The function used to build the option parser from
        :attr:`~.CommandMixin.OPTSPEC`

    :ivar parent: The parent command
    :ivar opts: The mapping between option name and option value of processed
        options

    When this mixin is used instead of |ApplicationMixin|, a support for
    commands and subcommands is added to the command-line interface. The
    :class:`~vutils.cli.optparse.OptionParser`, used by default, is highly
    extensible and configurable and allows a user to add or remove options
    depending on the actual context.
    """

    OPTSPEC: "ClassVar[Iterable[OptSpecType]]" = ()
    STATE_CLS: "ClassVar[type[State]]" = State
    BUILD_PARSER_FUNC: "ClassVar[BuildParserFuncType]" = build_parser

    parent: "CommandProtocol | None"
    opts: "dict[str, object]"

    __slots__ = ("parent", "opts")

    def __init__(
        self: "CommandProtocol", parent: "CommandProtocol | None" = None
    ) -> None:
        """
        Initialize the mixin.

        :param parent: The parent of the command
        """
        ApplicationMixin.__init__(self)
        self.parent = parent
        self.opts = {}

    def set_opts_defaults(
        self: "CommandProtocol", parser: "OptionParser | None"
    ) -> None:
        """
        Set options defaults.

        :param parser: The option parser

        Gather options defaults from :arg:`parser` and set them in
        :attr:`~.CommandMixin.opts`.
        """
        while parser:
            if isinstance(parser, PosArg):
                action: "Option" = parser.action
                self.set_optval(action.name, action.get_default())
            elif isinstance(parser, OptionSet):
                for action in parser.long_opts.values():
                    self.set_optval(action.name, action.get_default())
            parser = parser.next

    def set_optval(self: "CommandProtocol", name: str, value: object) -> None:
        """
        Set :arg:`value` to the option.

        :param name: The option name
        :param value: The option value
        """
        self.opts[name] = value

    def get_optval(
        self: "CommandProtocol", name: str, default: object = None
    ) -> object:
        """
        Get the option value.

        :param name: The option name
        :param default: The default value
        :return: the option value or :arg:`default`

        If the option was not found, try the parent command. If the option was
        not found at all, return :arg:`default`.
        """
        cmd: "CommandProtocol" = self
        while name not in cmd.opts and cmd.parent:
            cmd = cmd.parent
        return cmd.opts.get(name, default)

    def initialize(self: "CommandProtocol") -> None:
        """
        Perform delayed initialization actions.

        Perform initialization actions that are planned to be executed on
        :meth:`~.CommandMixin.run`.
        """

    def print_help(self: "CommandProtocol") -> None:
        """Print the command help."""

    def print_version(self: "CommandProtocol") -> None:
        """Print the command version."""

    def parse_args(self: "CommandProtocol", argv: "list[str]") -> State:
        """
        Parse arguments.

        :param argv: The list of arguments
        :return: the option parser state
        """
        cls: "type[CommandProtocol]" = type(self)
        state: State = cls.STATE_CLS(self, argv)
        cls.BUILD_PARSER_FUNC(*cls.OPTSPEC).parse(state)
        return state

    def load_subcommand(
        self: "CommandProtocol", name: str
    ) -> "CommandProtocol":
        """
        Load a subcommand.

        :param name: The name of the subcommand
        :return: the subcommand
        :raises ~vutils.cli.errors.UnknownCommandError: when the subcommand
            does not exist

        Load a subcommand by :arg:`name` and return it. The implementation of
        subcommands loading is in user's hands.
        """
        raise UnknownCommandError(name)

    def get_subcommand(self: "CommandProtocol") -> "CommandProtocol | None":
        """
        Get the subcommand, if any.

        :return: the subcommand
        :raises ~vutils.cli.errors.UnknownCommandError: when the subcommand
            does not exist

        Get the subcommand name given on the command line and try to load it
        using :meth:`~.CommandMixin.load_subcommand`.
        """
        name: "str | None" = cast(
            "str | None", self.opts.get(SUBCOMMAND_SLOT, None)
        )
        if not name:
            return None
        return self.load_subcommand(name)

    def run(self: "CommandProtocol", argv: "list[str]") -> int:
        """
        Run this command.

        :param argv: The list of arguments
        :return: the exit code
        :raises Exception: when the exception is not handled

        If a subcommand is given, run the subcommand. Otherwise, run
        :meth:`ApplicationMixin.main
        <vutils.cli.application.ApplicationMixin.main>`.
        """

        def wrapper(argv: "list[str]") -> int:
            """
            Wrap the run logic code.

            :param argv: The list of arguments
            :return: the exit code
            :raises Exception: when the exception is propagated

            Wraps the run logic code so :meth:`ApplicationMixin.epcall
            <vutils.cli.application.ApplicationMixin.epcall>` can handle raised
            exceptions.
            """
            self.initialize()

            state: State = self.parse_args(argv)

            subcommand: "CommandProtocol | None" = self.get_subcommand()
            if subcommand:
                return subcommand.run(state.argv)

            return self.main(state.argv)

        return self.epcall(wrapper, argv)
