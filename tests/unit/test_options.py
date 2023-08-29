#
# File:    ./tests/unit/test_options.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2023-09-09 20:58:53 +0200
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""
Test :mod:`vutils.cli.options` module.

.. |ConstOption| replace:: :class:`~vutils.cli.options.ConstOption`
.. |FlagOption| replace:: :class:`~vutils.cli.options.FlagOption`
.. |CountOption| replace:: :class:`~vutils.cli.options.CountOption`
.. |KVOption| replace:: :class:`~vutils.cli.options.KVOption`
.. |help| replace:: :class:`~vutils.cli.options.HelpOption`
.. |version| replace:: :class:`~vutils.cli.options.VersionOption`
.. |verbose| replace:: :class:`~vutils.cli.options.VerboseOption`
.. |subcommand| replace:: :func:`~vutils.cli.options.subcommand`
"""

import unittest.mock

from vutils.testing.testcase import TestCase

from vutils.cli.constants import SUBCOMMAND_SLOT
from vutils.cli.errors import OptParseError, UnknownOptionError
from vutils.cli.options import (
    HelpOption,
    VerboseOption,
    VersionOption,
    constant,
    counter,
    flag,
    keyval,
    subcommand,
    switch,
)
from vutils.cli.optparse import build_parser

from .utils import (
    OptionTesterMixin,
    not_kv_option_msg,
    unknown_option_msg,
    value_required_msg,
)


class ConstOptionTestCase(TestCase, OptionTesterMixin):
    """Test case for |ConstOption|."""

    __slots__ = ()

    def test_option(self):
        """Test |ConstOption|."""
        self.run_and_verify(
            "true",
            "t",
            "set true",
            option=constant,
            argv=["-t"],
            set_optval_calls=[unittest.mock.call("true", True)],
        )
        self.run_and_verify(
            "false",
            "f",
            "set false",
            keyname="falopt",
            value=False,
            option=constant,
            argv=["-f"],
            set_optval_calls=[unittest.mock.call("falopt", False)],
        )
        self.run_and_verify(
            "fail",
            "f",
            "just fail",
            value="failed",
            option=constant,
            argv=["-fx"],
            raises=UnknownOptionError,
            excstr=unknown_option_msg("-x"),
            set_optval_calls=[unittest.mock.call("fail", "failed")],
        )
        self.run_and_verify(
            "fail",
            "f",
            "just fail",
            value="failed",
            option=constant,
            argv=["--fail=ok"],
            raises=OptParseError,
            excstr=not_kv_option_msg("--fail"),
        )


class FlagOptionTestCase(TestCase, OptionTesterMixin):
    """Test case for |FlagOption|."""

    __slots__ = ()

    def test_option(self):
        """Test |FlagOption|."""
        self.run_and_verify(
            "zlib",
            "enable/disable zlib",
            option=switch,
            argv=["--zlib", "--no-zlib"],
            set_optval_calls=[
                unittest.mock.call("zlib", True),
                unittest.mock.call("zlib", False),
            ],
        )

        parser = build_parser(switch("zlib", "zlib on/off"))
        self.assertEqual(parser.long_opts["zlib"].name, "zlib")
        self.assertEqual(parser.long_opts["zlib"].aliases, "")
        self.assertEqual(parser.long_opts["zlib"].usage, "zlib on/off")
        self.assertEqual(
            parser.long_opts["zlib"].spec,
            {"inverse": "no-zlib", "default": False, "value": True},
        )
        self.assertEqual(parser.long_opts["no-zlib"].name, "no-zlib")
        self.assertEqual(parser.long_opts["no-zlib"].aliases, "")
        self.assertEqual(parser.long_opts["no-zlib"].usage, "")
        self.assertEqual(
            parser.long_opts["no-zlib"].spec,
            {"keyname": "zlib", "default": False, "value": False},
        )


class CountOptionTestCase(TestCase, OptionTesterMixin):
    """Test case for |CountOption|."""

    __slots__ = ()

    def test_option(self):
        """Test |CountOption|."""
        self.run_and_verify(
            "debug",
            "d",
            "increase debug level",
            option=counter,
            argv=["-d"],
            get_optval_calls=[unittest.mock.call("debug", 0)],
            set_optval_calls=[unittest.mock.call("debug", 1)],
        )
        self.run_and_verify(
            "debug",
            "d",
            "increase debug level",
            option=counter,
            argv=["--debug"],
            get_optval_calls=[unittest.mock.call("debug", 0)],
            set_optval_calls=[unittest.mock.call("debug", 1)],
        )
        self.run_and_verify(
            "debug",
            "d",
            "increase debug level",
            option=counter,
            argv=["--debug=3"],
            raises=OptParseError,
            excstr=not_kv_option_msg("--debug"),
        )

        parser = build_parser(counter("debug", "d", "increase debug level"))
        self.assertEqual(parser.long_opts["debug"].spec, {"default": 0})


class KVOptionTestCase(TestCase, OptionTesterMixin):
    """Test case for |KVOption|."""

    __slots__ = ()

    @staticmethod
    def make_optspec():
        """
        Make the option parser specification.

        :return: the option parser specification
        """
        return (
            flag("force", "f", "do not ask for permission"),
            keyval("input", "i", "input file"),
        )

    def test_option(self):
        """Test |KVOption|."""
        self.run_and_verify(
            option=self.make_optspec,
            argv=["--force", "-fiab", "--input=bc", "--input", "cd", "-ifg"],
            set_optval_calls=[
                unittest.mock.call("force", True),
                unittest.mock.call("force", True),
                unittest.mock.call("input", "ab"),
                unittest.mock.call("input", "bc"),
                unittest.mock.call("input", "cd"),
                unittest.mock.call("input", "fg"),
            ],
        )
        self.run_and_verify(
            option=self.make_optspec,
            argv=["--input"],
            raises=OptParseError,
            excstr=value_required_msg("--input"),
        )
        self.run_and_verify(
            option=self.make_optspec,
            argv=["--input="],
            raises=OptParseError,
            excstr=value_required_msg("--input"),
        )
        self.run_and_verify(
            option=self.make_optspec,
            argv=["-i"],
            raises=OptParseError,
            excstr=value_required_msg("-i"),
        )
        self.run_and_verify(
            option=self.make_optspec,
            argv=["-fi"],
            raises=OptParseError,
            excstr=value_required_msg("-i"),
            set_optval_calls=[unittest.mock.call("force", True)],
        )
        self.run_and_verify(
            option=self.make_optspec,
            argv=["--input", "--"],
            set_optval_calls=[unittest.mock.call("input", "--")],
        )


class CommonOptionsTestCase(TestCase, OptionTesterMixin):
    """Test case for |help|, |version|, and |verbose|."""

    __slots__ = ()

    def test_options(self):
        """Test |help|, |version|, and |verbose|."""
        self.run_and_verify(
            option=HelpOption,
            argv=["--help", "-h"],
            set_optval_calls=[
                unittest.mock.call("help", True),
                unittest.mock.call("help", True),
            ],
            print_help_calls=[unittest.mock.call(), unittest.mock.call()],
            exit_calls=[unittest.mock.call(0), unittest.mock.call(0)],
        )
        self.run_and_verify(
            option=VersionOption,
            argv=["--version"],
            set_optval_calls=[unittest.mock.call("version", True)],
            print_version_calls=[unittest.mock.call()],
            exit_calls=[unittest.mock.call(0)],
        )
        self.run_and_verify(
            option=VerboseOption,
            argv=["--verbose", "-v"],
            get_optval_calls=[
                unittest.mock.call("verbose", 0),
                unittest.mock.call("verbose", 0),
            ],
            set_optval_calls=[
                unittest.mock.call("verbose", 1),
                unittest.mock.call("verbose", 1),
            ],
        )


class SubcommandTestCase(TestCase, OptionTesterMixin):
    """Test case for |subcommand|."""

    __slots__ = ()

    def test_option(self):
        """Test |subcommand|."""
        self.run_and_verify(
            "COMMAND",
            "command",
            option=subcommand,
            argv=["create"],
            set_optval_calls=[unittest.mock.call(SUBCOMMAND_SLOT, "create")],
        )
