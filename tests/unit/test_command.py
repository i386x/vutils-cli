#
# File:    ./tests/unit/test_command.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2023-09-13 00:49:01 +0200
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""
Test :mod:`vutils.cli.command` module.

.. |CommandMixin| replace:: :class:`~vutils.cli.command.CommandMixin`
"""

import unittest.mock

from vutils.testing.testcase import TestCase

from .utils import (
    SampleApplication,
    make_io_mock,
    unknown_command_log,
    unknown_option_log,
)


class CommandMixinTestCase(TestCase):
    """Test case for |CommandMixin|."""

    __slots__ = ()

    def test_command(self):
        """Test |CommandMixin|."""
        self.run_and_verify(
            [],
            [
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: help: False"),
                unittest.mock.call("INFO: version: False"),
                unittest.mock.call("INFO: input: None"),
                unittest.mock.call("INFO: output: a.out"),
                unittest.mock.call("INFO: unprocessed arguments: []"),
            ],
        )
        self.run_and_verify(
            ["--"],
            [
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: help: False"),
                unittest.mock.call("INFO: version: False"),
                unittest.mock.call("INFO: input: None"),
                unittest.mock.call("INFO: output: a.out"),
                unittest.mock.call("INFO: unprocessed arguments: []"),
            ],
        )
        self.run_and_verify(
            ["--", "one", "-hy"],
            [
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: help: False"),
                unittest.mock.call("INFO: version: False"),
                unittest.mock.call("INFO: input: None"),
                unittest.mock.call("INFO: output: a.out"),
                unittest.mock.call(
                    "INFO: unprocessed arguments: ['one', '-hy']"
                ),
            ],
        )
        self.run_and_verify(
            ["-hv", "one", "-y", "--", "two"],
            [
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: application help"),
            ],
        )
        self.run_and_verify(
            ["--version"],
            [
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: application version"),
            ],
        )
        self.run_and_verify(
            ["-ia.in", "-ox.out", "one"],
            [
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: help: False"),
                unittest.mock.call("INFO: version: False"),
                unittest.mock.call("INFO: input: a.in"),
                unittest.mock.call("INFO: output: x.out"),
                unittest.mock.call("INFO: tty: False"),
                unittest.mock.call("INFO: yes: False"),
                unittest.mock.call("INFO: unprocessed arguments: []"),
            ],
        )
        self.run_and_verify(
            ["-ia.in", "-ox.out", "one", "--help"],
            [
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: application help"),
            ],
        )
        self.run_and_verify(
            ["-ia.in", "-ox.out", "one", "-ty"],
            [
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: help: False"),
                unittest.mock.call("INFO: version: False"),
                unittest.mock.call("INFO: input: a.in"),
                unittest.mock.call("INFO: output: x.out"),
                unittest.mock.call("INFO: tty: True"),
                unittest.mock.call("INFO: yes: True"),
                unittest.mock.call("INFO: unprocessed arguments: []"),
            ],
        )
        self.run_and_verify(
            ["-ia.in", "-ox.out", "one", "-ty", "--"],
            [
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: help: False"),
                unittest.mock.call("INFO: version: False"),
                unittest.mock.call("INFO: input: a.in"),
                unittest.mock.call("INFO: output: x.out"),
                unittest.mock.call("INFO: tty: True"),
                unittest.mock.call("INFO: yes: True"),
                unittest.mock.call("INFO: unprocessed arguments: []"),
            ],
        )
        self.run_and_verify(
            ["-ia.in", "-ox.out", "one", "-ty", "--", "--help"],
            [
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: help: False"),
                unittest.mock.call("INFO: version: False"),
                unittest.mock.call("INFO: input: a.in"),
                unittest.mock.call("INFO: output: x.out"),
                unittest.mock.call("INFO: tty: True"),
                unittest.mock.call("INFO: yes: True"),
                unittest.mock.call("INFO: unprocessed arguments: ['--help']"),
            ],
        )
        self.run_and_verify(
            ["two", "--name", "Name", "--", "one"],
            [
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: help: False"),
                unittest.mock.call("INFO: version: False"),
                unittest.mock.call("INFO: name: Name"),
                unittest.mock.call("INFO: quiet: False"),
                unittest.mock.call("INFO: unprocessed arguments: ['one']"),
            ],
        )
        self.run_and_verify(
            ["two", "--foo"],
            [
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call(unknown_option_log("--foo")),
            ],
            exitcode=1,
        )
        self.run_and_verify(
            ["three", "--foo"],
            [
                unittest.mock.call("INFO: initializing application"),
                unittest.mock.call(unknown_command_log("three")),
            ],
            exitcode=1,
        )

    def run_and_verify(self, argv, output, exitcode=0):
        """
        Run and verify custom command.

        :param argv: The list of arguments
        :param output: The expected output
        :param exitcode: The expected exit code (default is 0)
        """
        io_mock = make_io_mock()
        app = SampleApplication(stream=io_mock)

        self.assertEqual(app.run(argv), exitcode)
        self.assertEqual(io_mock.write.mock_calls, output)
