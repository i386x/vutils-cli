#
# File:    ./src/vutils/cli/base/constants.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2023-01-30 22:22:59 +0100
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""String and other constants."""

#: The application or command exit code signaling success
EXIT_SUCCESS: int = 0
#: The application or command exit code signaling failure
EXIT_FAILURE: int = 1

#: The name of the key in :attr:`CommandMixin.opts
#: <vutils.cli.command.CommandMixin.opts>` under which the subcommand name is
#: stored
SUBCOMMAND_SLOT: str = "COMMAND"

#: The ``default`` keyword
DEFAULT_KW: str = "default"
#: The ``inverse`` keyword
INVERSE_KW: str = "inverse"
#: The ``required`` keyword
KEYNAME_KW: str = "keyname"
#: The ``keyname`` keyword
REQUIRED_KW: str = "required"
#: The ``value`` keyword
VALUE_KW: str = "value"
