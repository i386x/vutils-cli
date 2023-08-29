#
# File:    ./src/vutils/cli/constants.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2023-01-30 22:22:59 +0100
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""
String and other constants.

:const SUBCOMMAND_SLOT: The name of the key in :attr:`CommandMixin.opts
    <vutils.cli.command.CommandMixin.opts>` under which the subcommand name is
    stored
:const DEFAULT_KW: The ``default`` keyword
:const INVERSE_KW: The ``inverse`` keyword
:const REQUIRED_KW: The ``required`` keyword
:const KEYNAME_KW: The ``keyname`` keyword
:const VALUE_KW: The ``value`` keyword
"""

SUBCOMMAND_SLOT: str = "COMMAND"

DEFAULT_KW: str = "default"
INVERSE_KW: str = "inverse"
KEYNAME_KW: str = "keyname"
REQUIRED_KW: str = "required"
VALUE_KW: str = "value"
