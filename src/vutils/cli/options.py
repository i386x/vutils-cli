#
# File:    ./src/vutils/cli/options.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2023-01-22 10:38:49 +0100
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""Options and their actions."""

from typing import TYPE_CHECKING, cast

from vutils.python.objects import ensure_key, ensure_no_key

from vutils.cli.constants import (
    DEFAULT_KW,
    INVERSE_KW,
    KEYNAME_KW,
    SUBCOMMAND_SLOT,
    VALUE_KW,
)
from vutils.cli.errors import OptParseError
from vutils.cli.optparse import Option, PositionalOption

if TYPE_CHECKING:
    from typing import NoReturn

    from vutils.cli.optparse import State


class ConstOption(Option):
    """
    Base class for an option that sets a constant value.

    Allow to define CLI options that set a constant value of any type under the
    option name.
    """

    __slots__ = ()

    def __init__(
        self, name: str, aliases: str, usage: str, **spec: object
    ) -> None:
        """
        Initialize the option.

        :param name: The option name
        :param aliases: Option short names
        :param usage: The help text
        :param spec: Option parameters

        In addition to base parameters, :arg:`spec` also supports:

        * ``value``, which holds the value of the option set by the action (the
          default value which is set is :obj:`True`)
        """
        Option.__init__(self, name, aliases, usage, **spec)

    def __call__(
        self, state: "State", value: str, alias: "str | None" = None
    ) -> "str | None":
        """
        Set the value associated with this option.

        :param state: The option parser state
        :param value: The option value (if any)
        :param alias: The short option name that invoked this action (if any)
        :return: unprocessed shorts or :obj:`None` signaling the return value
            should be ignored
        :raises ~vutils.cli.errors.OptParseError: when the option is used as a
            key-value option
        """
        self.assert_not_keyval(value, alias)
        state.cmd.set_optval(self.keyname, self.spec.get(VALUE_KW, True))
        if alias:
            return value
        return None


class FlagOption(ConstOption):
    """
    Base class for flag options.

    A flag option records whether it has been set or not.
    """

    __slots__ = ()

    def __init__(
        self, name: str, aliases: str, usage: str, **spec: object
    ) -> None:
        """
        Initialize the option.

        :param name: The option name
        :param aliases: Option short names
        :param usage: The help text
        :param spec: Option parameters

        The constructor ensures that :arg:`spec` has ``default`` and ``value``
        set and they are of the :class:`bool` type. By default, ``default`` is
        set to :obj:`False` and ``value`` is set to :obj:`True`.
        """
        ensure_key(spec, DEFAULT_KW, False)
        ensure_key(spec, VALUE_KW, True)
        ConstOption.__init__(self, name, aliases, usage, **spec)


class CountOption(Option):
    """
    Base class for an option that counts occurrences of itself.

    A count option records how many times it was presented on CLI. A typical
    use case is an option increasing the verbosity level.
    """

    __slots__ = ()

    def __init__(
        self, name: str, aliases: str, usage: str, **spec: object
    ) -> None:
        """
        Initialize the option.

        :param name: The option name
        :param aliases: Option short names
        :param usage: The help text
        :param spec: Option parameters

        The constructor ensures that :arg:`spec` has ``default`` set and of a
        type :class:`int`. The default value of ``default`` is 0.
        """
        ensure_key(spec, DEFAULT_KW, 0)
        Option.__init__(self, name, aliases, usage, **spec)

    def __call__(
        self, state: "State", value: str, alias: "str | None" = None
    ) -> "str | None":
        """
        Increase the value associated with this option by one.

        :param state: The option parser state
        :param value: The option value (if any)
        :param alias: The short option name that invoked this action (if any)
        :return: unprocessed shorts or :obj:`None` signaling the return value
            should be ignored
        :raises ~vutils.cli.errors.OptParseError: when the option is used as a
            key-value option
        """
        self.assert_not_keyval(value, alias)
        optval: int = cast(int, state.cmd.get_optval(self.name, 0))
        state.cmd.set_optval(self.name, optval + 1)
        if alias:
            return value
        return None


class KVOption(Option):
    """
    Base class for key-value options.

    A key-value option stores the value under the key.
    """

    __slots__ = ()

    def __init__(
        self, name: str, aliases: str, usage: str, **spec: object
    ) -> None:
        """
        Initialize the option.

        :param name: The option name
        :param aliases: Option short names
        :param usage: The help text
        :param spec: Option parameters
        """
        Option.__init__(self, name, aliases, usage, **spec)

    def __call__(
        self, state: "State", value: str, alias: "str | None" = None
    ) -> "str | None":
        """
        Set the value under the key.

        :param state: The option parser state
        :param value: The option value (if any)
        :param alias: The short option name that invoked this action (if any)
        :return: unprocessed shorts or :obj:`None` signaling the return value
            should be ignored
        :raises ~vutils.cli.errors.OptParseError: when the value is missing
        """
        if not value:
            if not state.argv:
                optname: str = f"-{alias}" if alias else f"--{self.name}"
                raise OptParseError(f"Option {optname} requires a value")
            value = state.argv.pop(0)
        state.cmd.set_optval(self.name, value)
        if alias:
            return ""
        return None


class HelpOption(FlagOption):
    """Help option (``--help``, ``-h``)."""

    __slots__ = ()

    def __init__(
        self,
        name: str = "help",
        aliases: str = "h",
        usage: str = "print this screen and exit",
        **spec: object,
    ) -> None:
        """
        Initialize the option.

        :param name: The option name
        :param aliases: Option shorts
        :param usage: The help text
        :param spec: Option parameters
        """
        FlagOption.__init__(self, name, aliases, usage, **spec)

    def __call__(
        self, state: "State", value: str, alias: "str | None" = None
    ) -> "NoReturn":
        """
        Print the help and exit.

        :param state: The option parser state
        :param value: The option value (if any)
        :param alias: The short option name that invoked this action (if any)
        """
        FlagOption.__call__(self, state, value, alias)
        state.cmd.print_help()
        state.cmd.exit(type(state.cmd).EXIT_SUCCESS)


class VersionOption(FlagOption):
    """Version option (``--version``)."""

    __slots__ = ()

    def __init__(
        self,
        name: str = "version",
        aliases: str = "",
        usage: str = "print the version and exit",
        **spec: object,
    ) -> None:
        """
        Initialize the option.

        :param name: The option name
        :param aliases: Option shorts
        :param usage: The help text
        :param spec: Option parameters
        """
        FlagOption.__init__(self, name, aliases, usage, **spec)

    def __call__(
        self, state: "State", value: str, alias: "str | None" = None
    ) -> "NoReturn":
        """
        Print the version and exit.

        :param state: The option parser state
        :param value: The option value (if any)
        :param alias: The short option name that invoked this action (if any)
        """
        FlagOption.__call__(self, state, value, alias)
        state.cmd.print_version()
        state.cmd.exit(type(state.cmd).EXIT_SUCCESS)


class VerboseOption(CountOption):
    """Verbose option (``--verbose``, ``-v``)."""

    __slots__ = ()

    def __init__(
        self,
        name: str = "verbose",
        aliases: str = "v",
        usage: str = "set the verbosity level",
        **spec: object,
    ) -> None:
        """
        Initialize the option.

        :param name: The option name
        :param aliases: Option shorts
        :param usage: The help text
        :param spec: Option parameters
        """
        CountOption.__init__(self, name, aliases, usage, **spec)


def constant(
    name: str, aliases: str = "", usage: str = "", **spec: object
) -> Option:
    """
    Make a constant option.

    :param name: The option name
    :param aliases: Option shorts
    :param usage: The help text
    :param spec: Option parameters
    :return: the constant option
    """
    return ConstOption(name, aliases, usage, **spec)


def flag(
    name: str, aliases: str = "", usage: str = "", **spec: object
) -> Option:
    """
    Make a flag option.

    :param name: The option name
    :param aliases: Option shorts
    :param usage: The help text
    :param spec: Option parameters
    :return: the flag option
    """
    return FlagOption(name, aliases, usage, **spec)


def switch(
    name: str, usage: str = "", **spec: object
) -> "tuple[Option, Option]":
    """
    Make a pair of flag and inverse flag options.

    :param name: The option name
    :param usage: The help text
    :param spec: Option parameters
    :return: the pair of flag and inverse flag options

    These parameters from :arg:`spec` are reset by this function: ``value``,
    ``keyname``, and ``inverse``.

    The ``inverse`` parameter holds the name of inverse flag. It becomes handy
    while generating a help.
    """
    ensure_no_key(spec, VALUE_KW)
    ensure_no_key(spec, KEYNAME_KW)
    ensure_no_key(spec, INVERSE_KW)
    return (
        flag(name, "", usage, inverse=f"no-{name}", **spec),
        flag(f"no-{name}", "", "", keyname=name, value=False, **spec),
    )


def counter(
    name: str, aliases: str = "", usage: str = "", **spec: object
) -> Option:
    """
    Make a counter option.

    :param name: The option name
    :param aliases: Option shorts
    :param usage: The help text
    :param spec: Option parameters
    :return: the counter option
    """
    return CountOption(name, aliases, usage, **spec)


def keyval(
    name: str, aliases: str = "", usage: str = "", **spec: object
) -> Option:
    """
    Make a key-value option.

    :param name: The option name
    :param aliases: Option shorts
    :param usage: The help text
    :param spec: Option parameters
    :return: the key-value option
    """
    return KVOption(name, aliases, usage, **spec)


def positional(name: str, usage: str = "", **spec: object) -> Option:
    """
    Make a positional option.

    :param name: The option name
    :param usage: The help text
    :param spec: Option parameters
    :return: the positional option
    """
    return PositionalOption(name, usage, **spec)


def subcommand(name: str, usage: str = "", **spec: object) -> Option:
    """
    Make a subcommand option.

    :param name: The option name
    :param usage: The help text
    :param spec: Option parameters
    :return: the subcommand option

    ``keyname`` from :arg:`spec` is reset by this function.
    """
    ensure_no_key(spec, KEYNAME_KW)
    return positional(name, usage, keyname=SUBCOMMAND_SLOT, **spec)
