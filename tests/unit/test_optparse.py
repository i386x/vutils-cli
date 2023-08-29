#
# File:    ./tests/unit/test_optparse.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2023-07-20 01:16:38 +0200
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""
Test :mod:`vutils.cli.optparse` module.

.. |Option| replace:: :class:`~vutils.cli.optparse.Option`
.. |Option.__call__| replace::
   :meth:`Option.__call__ <vutils.cli.optparse.Option.__call__>`
.. |PositionalOption| replace:: :class:`~vutils.cli.optparse.PositionalOption`
.. |PositionalOption.__call__| replace::
   :meth:`PositionalOption.__call__
   <vutils.cli.optparse.PositionalOption.__call__>`
.. |State| replace:: :class:`~vutils.cli.optparse.State`
.. |State.update| replace::
   :meth:`State.update <vutils.cli.optparse.State.update>`
.. |OptionParser| replace:: :class:`~vutils.cli.optparse.OptionParser`
.. |OptionParser.parse| replace::
   :meth:`OptionParser.parse <vutils.cli.optparse.OptionParser.parse>`
.. |PosArg| replace:: :class:`~vutils.cli.optparse.PosArg`
.. |PosArg.parse| replace::
   :meth:`PosArg.parse <vutils.cli.optparse.PosArg.parse>`
.. |CommandMixin.set_optval| replace::
   :meth:`CommandMixin.set_optval <vutils.cli.command.CommandMixin.set_optval>`
"""

import unittest.mock

from vutils.testing.mock import make_mock
from vutils.testing.testcase import TestCase
from vutils.testing.utils import AssertRaises

from vutils.cli.errors import OptParseError
from vutils.cli.optparse import (
    build_parser,
    Option,
    OptionParser,
    PosArg,
    PositionalOption,
    State,
)

from .utils import make_command_mock, make_state_mock


class OptionTestCase(TestCase):
    """Test case for |Option|."""

    __slots__ = ()

    def test_initialization(self):
        """Test that |Option| is properly initialized."""
        name = "foo"
        aliases = "-f"
        usage = "Foo"
        keyname = "bar"
        default = "baz"

        option_a = Option(name, aliases, usage)
        self.assertEqual(option_a.name, name)
        self.assertEqual(option_a.aliases, aliases)
        self.assertEqual(option_a.usage, usage)
        self.assertEqual(option_a.spec, {})
        self.assertEqual(option_a.keyname, name)
        self.assertIsNone(option_a.get_default())
        self.assertFalse(option_a.required())

        option_b = Option(
            name,
            aliases,
            usage,
            keyname=keyname,
            default=default,
            required=True,
        )
        self.assertEqual(option_b.name, name)
        self.assertEqual(option_b.aliases, aliases)
        self.assertEqual(option_b.usage, usage)
        self.assertEqual(
            option_b.spec,
            {"keyname": keyname, "default": default, "required": True},
        )
        self.assertEqual(option_b.keyname, keyname)
        self.assertEqual(option_b.get_default(), default)
        self.assertTrue(option_b.required())

    def test_action_not_implemented(self):
        """Test that |Option.__call__| is not implemented."""
        with self.assertRaises(NotImplementedError):
            Option("foo", "", "Foo")(make_state_mock(), "")


class PositionalOptionTestCase(TestCase):
    """Test case for |PositionalOption|."""

    __slots__ = ()

    def test_initialization(self):
        """Test that |PositionalOption| is properly initialized."""
        name = "FOO"
        usage = "Foo"
        keyname = "foo"

        option = PositionalOption(name, usage, keyname=keyname)
        self.assertEqual(option.name, name)
        self.assertEqual(option.aliases, "")
        self.assertEqual(option.usage, usage)
        self.assertEqual(option.spec, {"keyname": keyname})
        self.assertEqual(option.keyname, keyname)

    def test_action(self):
        """Test that |PositionalOption.__call__| works as expected."""
        state = make_state_mock()
        keyname = "foo"
        value = "bar"

        option = PositionalOption("FOO", "Foo", keyname=keyname)

        option(state, value)
        self.assert_called_with(state.cmd.set_optval, keyname, value)


class StateTestCase(TestCase):
    """Test case for |State|."""

    __slots__ = ()

    def test_initialization(self):
        """Test that |State| is properly initialized."""
        command = make_command_mock()
        argv = ["-a", "-bc", "--foo=bar"]

        state = State(command, argv)
        self.assertIs(state.cmd, command)
        self.assertIsNot(state.argv, argv)
        self.assertEqual(state.argv, argv)
        self.assertIsNone(state.pchain)
        self.assertIsNone(state.parser)

    def test_update(self):
        """Test that |State.update| updates the state."""
        command = make_command_mock()
        parser = make_mock()
        another_parser = make_mock()

        state = State(command, [])

        state.update(parser)
        self.assertIs(state.pchain, parser)
        self.assertIs(state.parser, parser)
        self.assert_called_with(command.set_opts_defaults, parser)

        state.update(another_parser)
        self.assertIs(state.pchain, parser)
        self.assertIs(state.parser, another_parser)
        self.assert_not_called(command.set_opts_defaults)


class OptionParserTestCase(TestCase):
    """Test case for |OptionParser|."""

    __slots__ = ()

    def test_initialization(self):
        """Test that |OptionParser| is properly initialized."""
        parser = OptionParser()
        self.assertIsNone(parser.next)

    def test_parse(self):
        """Test |OptionParser.parse|."""
        parser = OptionParser()
        sub_parser = OptionParser()
        sub_sub_parser = OptionParser()

        self.parse_and_verify(parser, parser)
        parser.chain(sub_parser)
        self.parse_and_verify(parser, sub_parser)
        sub_parser.chain(sub_sub_parser)
        self.parse_and_verify(parser, sub_sub_parser)

    def parse_and_verify(self, first, last):
        """
        Run |OptionParser.parse| and verify the result.

        :param first: The first parser in the parser chain
        :param last: The last parser in the parser chain
        """
        command = make_command_mock()
        state = State(command, [])

        first.parse(state)
        self.assertIsNone(last.next)
        self.assertIs(state.pchain, first)
        self.assertIs(state.parser, last)
        self.assert_called_with(command.set_opts_defaults, first)


class PosArgTestCase(TestCase):
    """Test case for |PosArg|."""

    __slots__ = ()

    def test_initialization(self):
        """Test that |PosArg| is properly initialized."""
        option = PositionalOption("FOO", "foo")
        parser = PosArg(option)

        self.assertIsNone(parser.next)
        self.assertIs(parser.action, option)

    def test_parse(self):
        """Test |PosArg.parse|."""
        spec = [("FOO", False), ("BAR", True)]

        self.parse_and_verify(spec, [], raises=OptParseError, mock_calls=[])
        self.parse_and_verify(
            spec,
            ["cmd"],
            raises=OptParseError,
            mock_calls=[unittest.mock.call(spec[0][0].lower(), "cmd")],
        )
        self.parse_and_verify(
            spec, ["--cmd"], raises=OptParseError, mock_calls=[],
        )
        self.parse_and_verify(
            spec,
            ["cmd", "subcmd"],
            mock_calls=[
                unittest.mock.call(spec[0][0].lower(), "cmd"),
                unittest.mock.call(spec[1][0].lower(), "subcmd"),
            ],
        )
        self.parse_and_verify(
            spec, ["--cmd", "subcmd"], raises=OptParseError, mock_calls=[],
        )
        self.parse_and_verify(
            spec,
            ["cmd", "--subcmd"],
            raises=OptParseError,
            mock_calls=[unittest.mock.call(spec[0][0].lower(), "cmd")],
        )
        self.parse_and_verify(
            spec, ["--cmd", "--subcmd"], raises=OptParseError, mock_calls=[],
        )

    def parse_and_verify(self, spec, args, **result):
        """
        Run |PosArg.parse| and verify the result.

        :param spec: The parser specification
        :param args: The list of arguments to be parsed
        :param result: Key-value arguments characterizing the expected result

        :arg:`spec` is a list of pairs ``(NAME, required)``, where ``NAME`` is
        the name of the argument and ``required`` is either :obj:`True` or
        :obj:`False`, depending on whether the argument is required or not.

        :arg:`result` supports following keys:

        * ``raises`` is an exception that is expected to be raised, otherwise
          it is :obj:`None`.
        * ``mock_calls`` is a list of expected calls to
          |CommandMixin.set_optval|.
        """
        raises = result.get("raises")
        mock_calls = result.get("mock_calls", [])

        spec = [
            PositionalOption(
                x[0].upper(),
                x[0].lower(),
                keyname=x[0].lower(),
                required=x[1],
            )
            for x in spec
        ]
        parser = build_parser(spec)

        command = make_command_mock()
        state = State(command, args)

        parse = parser.parse
        if raises:
            parse = AssertRaises(self, parse, raises)

        parse(state)
        self.assert_called_with(command.set_opts_defaults, parser)
        self.assertEqual(command.set_optval.mock_calls, mock_calls)
