#
# File:    ./src/vutils/cli/base/io.py
# Author:  Jiří Kučera <sanczes AT gmail.com>
# Date:    2021-07-11 16:17:41 +0200
# Project: vutils-cli: Auxiliary library for writing CLI applications
#
# SPDX-License-Identifier: MIT
#
"""Handling input/output."""

import re

import colorama

ANSI_CSI_RE = re.compile("\033\\[[0-9;]*[mGKHF]")


def strip_colors(text):
    """"""
    return ANSI_CSI_RE.sub("", text)


def has_colors(stream, choice):
    """"""
    if choice == KW_AUTO:
        choice = KW_ALWAYS if stream.isatty() else KW_NEVER
    return choice == KW_ALWAYS


def maybe_strip_colors(text, stream, choice):
    """"""
    if not has_colors(stream, choice):
        text = strip_colors(text)
    return text


class ColorFactory:
    """"""

    __colored: bool

    __slots__ = ("__colored",)

    def __init__(self, colored=True):
        """"""
        self.__colored = colored

    def reset_all(self):
        """"""
        if not self.__colored:
            return ""
        return colorama.Style.RESET_ALL

    def color(self, code):
        """"""
        if not self.__colored:
            return ""

        style = ""
        bright = False
        color = ""
        for part in code.split("-"):
            part = part.strip().upper()
            if not part:
                continue
            elif part == "BOLD":
                style = colorama.Style.BRIGHT
            elif part == "BRIGHT":
                bright = True
            else:
                color = part

        if color:
            if bright:
                color = f"LIGHT{color}_EX"
            color = getattr(colorama.Fore, color, "")
        if not color:
            return self.reset_all()
        return f"{style}{color}"


class Streams:
    """"""

    __istreams: "list[TextIO]"
    __ostreams: "list[TextIO]"
    __estreams: "list[TextIO]"

    __slots__ = ("__istreams", "__ostreams", "__estreams")

    def __init__(self, istream, ostream, estream):
        """"""
        self.__istreams = [istream]
        self.__ostreams = [ostream]
        self.__estreams = [estream]

    def get_input(self):
        """"""
        return self.__istreams[-1]

    def get_output(self):
        """"""
        return self.__ostreams[-1]

    def get_error(self):
        """"""
        return self.__estreams[-1]

    @contextlib.contextmanager
    def redirect(self, istream=None, ostream=None, estream=None):
        """"""
        if istream is None:
            istream = self.__istreams[-1]
        if ostream is None:
            ostream = self.__ostreams[-1]
        if estream is None:
            estream = self.__estreams[-1]
        self.__istreams.append(istream)
        self.__ostreams.append(ostream)
        self.__estreams.append(estream)
        try:
            yield self
        finally:
            self.__istreams.pop()
            self.__ostreams.pop()
            self.__estreams.pop()
