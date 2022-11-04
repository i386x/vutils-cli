#
# File:    ./src/vutils/cli/__init__.pyi
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2022-02-17 19:49:22 +0100
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#

import pathlib
from collections.abc import Callable
from typing import NoReturn, Protocol, TextIO

from typing_extensions import TypeAlias

from vutils.cli.errors import AppExitError
from vutils.cli.logging import LogFormatter

ExcType: TypeAlias = type[Exception]

ExitExcType: TypeAlias = type[AppExitError]
ColorFuncType: TypeAlias = Callable[[str], str]

class ApplicationProtocol(Protocol):
    EXIT_SUCCESS: int
    EXIT_FAILURE: int
    EXIT_EXCEPTION: ExitExcType

    def catch(self, exc: ExcType) -> None: ...
    def error(self, msg: str, ecode: int) -> NoReturn: ...
    def exit(self, ecode: int) -> NoReturn: ...
    def main(self, argv: list[str]) -> int: ...
    def run(self, argv: list[str]) -> int: ...
    def on_exit(self, ecode: int) -> None: ...
    def on_error(self, exc: Exception) -> int: ...

    # StreamsProxyMixin interface:
    def set_streams(
        self, ostream: TextIO | None, estream: TextIO | None
    ) -> None: ...
    def wout(self, text: str) -> None: ...
    def werr(self, text: str) -> None: ...

    # LoggerMixin interface:
    def set_logger_props(
        self,
        logpath: pathlib.Path | None,
        formatter: LogFormatter | None,
        vlevel: int | None,
        dlevel: int | None,
    ) -> None: ...
    def set_log_style(self, name: str, color: ColorFuncType) -> None: ...
    def wlog(self, msg: str) -> None: ...
    def linfo(self, msg: str, vlevel: int) -> None: ...
    def lwarn(self, msg: str) -> None: ...
    def lerror(self, msg: str) -> None: ...
    def ldebug(self, msg: str, dlevel: int) -> None: ...

class StreamsProxyProtocolP(Protocol, ApplicationProtocol):
    __output: TextIO
    __errout: TextIO

class LoggerProtocolP(Protocol, ApplicationProtocol):
    __logpath: pathlib.Path | None
    __formatter: LogFormatter
    __vlevel: int
    __dlevel: int

    def __do_log(self, name: str, msg: str) -> None: ...

class ApplicationProtocolP(Protocol, ApplicationProtocol):
    __elist: list[ExcType]
