#
# File:    ./src/vutils/cli/optparse.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2023-01-21 20:49:49 +0100
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""Low level command line parsing."""

from typing import TYPE_CHECKING, cast

from vutils.python.objects import flatten

from vutils.cli.constants import DEFAULT_KW, KEYNAME_KW, REQUIRED_KW
from vutils.cli.errors import OptParseError, UnknownOptionError

if TYPE_CHECKING:
    from vutils.cli import CommandProtocol, OptSpecType


class Option:
    """
    Base class for an option with action.

    :ivar name: The option name
    :ivar aliases: Option short names
    :ivar usage: The help text
    :ivar spec: Option parameters
    :ivar keyname: The name of a key under which the option is stored
    """

    name: str
    aliases: str
    usage: str
    spec: "dict[str, object]"
    keyname: str

    __slots__ = ("name", "aliases", "usage", "spec", "keyname")

    def __init__(
        self, name: str, aliases: str, usage: str, **spec: object
    ) -> None:
        """
        Initialize the option.

        :param name: The option name
        :param aliases: Option short names
        :param usage: The help text
        :param spec: Option parameters

        :arg:`name` is the name of the long version of the option which a user
        types to the command line as ``--name``. :arg:`aliases` is a string of
        short names of :arg:`name`. For example, ``"h?"`` means that a user can
        type ``-h`` or ``-?`` as shortcuts for :arg:`name`. ``""`` means there
        are no aliases.

        :arg:`usage` holds a description of the option meaning. A user can see
        it when a help screen is shown.

        :arg:`spec` contains additional parameters associated with the option.
        There are three basic parameters supported:

        * ``keyname``, which specify the name under which the option's value is
          accessible to application. The default value of ``keyname`` is
          :arg:`name`.
        * ``default``, which specify the default value of the option. The
          default value of ``default`` is :obj:`None`.
        * ``required``, which specify whether the option is required or not.
          The default is :obj:`False`.

        Another :arg:`spec` parameters can be specified by a user.
        """
        self.name = name
        self.aliases = aliases
        self.usage = usage
        self.spec = spec
        self.keyname = cast(str, spec.get(KEYNAME_KW, name))

    def get_default(self) -> object:
        """
        Get the default value of the option.

        :return: the default value of the option

        :obj:`None` means the option has no default value.
        """
        return self.spec.get(DEFAULT_KW, None)

    def required(self) -> bool:
        """
        Tell whether the option is required of not.

        :return: :obj:`True` if the option is required
        """
        return cast(bool, self.spec.get(REQUIRED_KW, False))

    def __call__(
        self, state: "State", value: str, alias: "str | None" = None
    ) -> "str | None":
        """
        Do the action associated with the option.

        :param state: The option parser state
        :param value: The option value (if any)
        :param alias: The short option name that invoked this action (if any)
        :return: unprocessed shorts or :obj:`None` signaling the return value
            should be ignored
        :raises ~vutils.cli.errors.OptParseError: when error is encountered

        This method is called by :class:`.OptionParser` immediately after
        option is parsed. There are three flavors:

        #. *Positional argument is parsed*. When the option parser hits a
           positional argument, it is passed in :arg:`value` during the call.
           :arg:`alias` is set to :obj:`None`. The return value of the call is
           not used, so it should be :obj:`None`.
        #. *Long option is parsed*, e.g. ``--foo=bar`` or ``--baz``. In the
           first example, :arg:`value` is ``"bar"``. In the second example,
           :arg:`value` is ``""`` (the empty string). :arg:`alias` stays
           :obj:`None`. The return value is ignored.
        #. *Short options are parsed*, e.g. ``-abc`` or ``-a``. Using the list
           terminology, :arg:`alias` holds the head (``"a"``) and :arg:`value`
           holds the tail (``"bc"`` or ``""``) of the list of shorts. The
           return value is the string of unprocessed short options. Thus, if
           ``-a`` is a key-value option, the :arg:`value` becomes its value and
           the action returns the empty string to signal that all shorts are
           processed.
        """
        raise NotImplementedError("Option.__call__ is not implemented")


class PositionalOption(Option):
    """
    Base class for a positional option.

    A positional option determines which argument on the command line is its
    value.
    """

    __slots__ = ()

    def __init__(self, name: str, usage: str, **spec: object) -> None:
        """
        Initialize the option.

        :param name: The option name
        :param usage: The help text
        :param spec: Option parameters
        """
        Option.__init__(self, name, "", usage, **spec)

    def __call__(
        self, state: "State", value: str, alias: "str | None" = None
    ) -> None:
        """
        Set the value.

        :param state: The option parser state
        :param value: The option value (if any)
        :param alias: The short option name that invoked this action (if any)
        :return: unprocessed shorts or :obj:`None` signaling the return value
            should be ignored
        """
        state.cmd.set_optval(self.keyname, value)


class State:
    """
    Base class for option parser state.

    :ivar cmd: The instance of command or application owning the option parser
    :ivar argv: The copy of arguments. The option parser will work with the
        copy, leaving the original list of arguments intact
    :ivar pchain: The chain of option parser instances
    :ivar parser: The recently used option parser from the chain
    """

    cmd: "CommandProtocol"
    argv: "list[str]"
    pchain: "OptionParser | None"
    parser: "OptionParser | None"

    __slots__ = ("cmd", "argv", "pchain", "parser")

    def __init__(self, cmd: "CommandProtocol", argv: "list[str]") -> None:
        """
        Initialize the option parser state.

        :param cmd: The application or command that drives argument parsing
        :param argv: The list of arguments to be parsed
        """
        self.cmd = cmd
        self.argv = argv[:]
        self.pchain = None
        self.parser = None

    def update(self, parser: "OptionParser") -> None:
        """
        Update the state.

        :param parser: The recently used option parser

        Update the state information, actually the recently used option parser.
        When called for the first time, set the chain to be the :arg:`parser`
        and set option defaults on the application side by calling
        :meth:`CommandMixin.set_opts_defaults
        <vutils.cli.command.CommandMixin.set_opts_defaults>`.
        """
        if not self.pchain:
            self.pchain = parser
            self.cmd.set_opts_defaults(parser)
        self.parser = parser


class OptionParser:
    """
    Base class for option parser basic building blocks.

    :ivar next: The next option parser in the chain
    """

    next: "OptionParser | None"

    __slots__ = ("next",)

    def __init__(self) -> None:
        """Initialize the option parser."""
        self.next = None

    def parse(self, state: State) -> None:
        """
        Parse one option.

        :param state: The parser state

        First, update :arg:`state`. Then, parse the recent command line
        argument and call the appropriate action. Finally, pass the control to
        the next parser in the chain.
        """
        state.update(self)

        if self.next:
            self.next.parse(state)

    def chain(self, other: "OptionParser | None") -> None:
        """
        Chain this parser with the :arg:`other`.

        :param other: The parser to be added to the chain
        """
        self.next = other


class PosArg(OptionParser):
    """
    Option parser for positional argument.

    :ivar action: The action to be taken after the parsing of positional
        argument
    """

    action: Option

    __slots__ = ("action",)

    def __init__(self, action: Option) -> None:
        """
        Initialize the option parser.

        :param action: The action to be taken after the positional argument has
            been parsed
        """
        OptionParser.__init__(self)
        self.action = action

    def parse(self, state: State) -> None:
        """
        Parse the positional argument.

        :param state: The parser state

        Update :arg:`state`, parse the positional argument, invoke the
        appropriate action, and pass the control to the next parser in the
        chain.
        """
        state.update(self)

        if state.argv and not state.argv[0].startswith("-"):
            self.action(state, state.argv.pop(0))
        elif self.action.required():
            raise OptParseError(
                f"Positional option '{self.action.name}' is required"
            )

        if self.next:
            self.next.parse(state)


class OptionSet(OptionParser):
    """
    Option parser for a set of options.

    :ivar long_opts: The mapping between option names and options
    :ivar short_opts: The mapping between option aliases and options
    """

    long_opts: "dict[str, Option]"
    short_opts: "dict[str, Option]"

    __slots__ = ("long_opts", "short_opts")

    def __init__(self, *options: "OptionSet | Option") -> None:
        """
        Initialize the option parser.

        :param options: Options that will be recognized by this option parser
        """
        OptionParser.__init__(self)
        self.long_opts = {}
        self.short_opts = {}
        self.add_options(*options)

    def add_options(self, *options: "OptionSet | Option") -> None:
        """
        Add options to be recognized by this option parser.

        :param options: Options to be added

        If any option from :arg`options` is :class:`.OptionSet`, merge its
        options with this option parser.
        """
        for option in options:
            if isinstance(option, OptionSet):
                self.merge(option)
                continue
            self.long_opts[option.name] = option
            for alias in option.aliases:
                self.short_opts[alias] = option

    def merge(self, other: "OptionSet") -> None:
        """
        Merge options from :arg:`other` into this option parser.

        :param other: The other option parser
        """
        self.long_opts.update(other.long_opts)
        self.short_opts.update(other.short_opts)

    def parse(self, state: State) -> None:
        """
        Parse an argument that matches the option set.

        :param state: The parser state

        Update :arg:`state`, parse an argument that matches an option from the
        option set, invoke appropriate action, and pass the control to the next
        option parser in the chain.
        """
        state.update(self)

        while state.argv:
            arg: str = state.argv.pop(0)
            if arg == "--":
                break
            if arg.startswith("--"):
                nameval: "list[str]" = arg[2:].split("=", 1)
                name: str = nameval[0]
                value: str = nameval[1] if len(nameval) > 1 else ""
                self.dispatch_long_option(state, name, value)
            elif arg.startswith("-"):
                shorts: str = arg[1:]
                while shorts:
                    shorts = self.dispatch_short_option(
                        state, shorts[0], shorts[1:]
                    )
            else:
                state.argv.insert(0, arg)
                break

        if self.next:
            self.next.parse(state)

    def dispatch_long_option(
        self, state: State, name: str, value: str
    ) -> None:
        """
        Dispatch long option.

        :param state: The parser state
        :param name: The name of the option
        :param value: The value of the option
        :raises ~vutils.cli.errors.UnknownOptionError: when the option to be
            dispatched is unknown
        """
        action: "Option | None" = self.long_opts.get(name)
        if action is None:
            raise UnknownOptionError(f"--{name}")
        action(state, value)

    def dispatch_short_option(
        self, state: State, sname: str, value: str
    ) -> str:
        """
        Dispatch short option.

        :param state: The parser state
        :param sname: The name of the short option
        :param value: The value of the short option
        :return: the sequence of unprocessed short options as a string
        :raises ~vutils.cli.errors.UnknownOptionError: when the short option to
            be dispatched is unknown
        """
        action: "Option | None" = self.short_opts.get(sname)
        if action is None:
            raise UnknownOptionError(f"-{sname}")
        return cast(str, action(state, value, sname))


def add_to_parser(parser: "OptionParser | None", opt: Option) -> OptionParser:
    """
    Add option to the option parser.

    :param parser: The option parser
    :param opt: The option
    :return: the last (recent) option parser in the chain

    Add :arg:`opt` to :arg:`parser`, eventually extend the parser chain. The
    process is driven by these rules:

    * if :arg:`parser` is not build yet, built it;
    * otherwise, if a positional option is about to be added, build a parser
      for that option and append it to the parser chain;
    * otherwise, if :arg:`parser` is a positional option parser, build a parser
      for :arg:`opt` and append it to the parser chain;
    * otherwise, add :arg:`opt` to :arg:`parser` (the case when an option set
      is extended about non-positional option).
    """
    if parser is None:
        return (
            PosArg(opt)
            if isinstance(opt, PositionalOption)
            else OptionSet(opt)
        )
    if isinstance(opt, PositionalOption):
        parser.chain(PosArg(opt))
    elif isinstance(parser, PosArg):
        parser.chain(OptionSet(opt))
    else:
        cast(OptionSet, parser).add_options(opt)
    return parser.next if parser.next else parser


def build_parser(*optspec: "OptSpecType") -> OptionParser:
    """
    Build the option parser from its specification.

    :param optspec: The option parser specification
    :return: the option parser from the option parser chain start
    """
    head: "OptionParser | None" = None
    tail: "OptionParser | None" = None
    for opt in flatten(optspec):
        tail = add_to_parser(tail, cast(Option, opt))
        if not head:
            head = tail
    return head if head else OptionParser()
