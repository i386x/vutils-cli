#                                                         -*- coding: utf-8 -*-
# File:    ./tests/unit/test_version.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2021-07-06 21:32:16 +0200
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""Test `vutils.cli.version` module."""

import unittest

from vutils.cli.version import __version__


class VersionTestCase(unittest.TestCase):
    """Test case for version."""

    def test_version(self):
        """Test if version is defined properly."""
        self.assertIsInstance(__version__, str)
