# Copyright 2026 Torbjörn E. M. Nordling <t@nordlinglab.org>
# SPDX-License-Identifier: Apache-2.0
"""Help layout shared by the scripts in scripts/."""

from __future__ import annotations

import argparse


class HelpFormatter(
    argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter
):
    """Keep the description's line breaks and show every option's default.

    The description is the script's docstring, so its example commands stay
    copyable. An option without a default (``None``) states in its own help
    what happens when it is left out; a flag shows ``(default: off)``.
    """

    def _get_help_string(self, action: argparse.Action) -> str | None:
        text = action.help or ""
        if "%(default)" in text or "default:" in text or action.default is None:
            return text
        if action.default is argparse.SUPPRESS or not action.option_strings:
            return text
        if action.default is False and action.nargs == 0:
            return f"{text} (default: off)"
        return f"{text} (default: %(default)s)"
