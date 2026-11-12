# Copyright 2026 Torbjörn E. M. Nordling <t@nordlinglab.org>
# SPDX-License-Identifier: Apache-2.0
"""Tests that help texts and messages guide students the same way everywhere.

Run from the repository root: python -m pytest scripts/tests
"""

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duckiebot_analysis.analysis import case_study as cs  # noqa: E402
from duckiebot_analysis.data import layout  # noqa: E402

SCRIPTS = Path(__file__).resolve().parents[1]
PLACEHOLDER = "db17-<robot>-<position>-<motor>"


def _help(script: str, capsys) -> str:
    with pytest.raises(SystemExit):
        importlib.import_module(script).parse_args(["--help"])
    return " ".join(capsys.readouterr().out.split())


@pytest.mark.parametrize("script", ["track_video", "process_raw"])
def test_folder_help_uses_the_one_placeholder(script, capsys):
    assert PLACEHOLDER in _help(script, capsys)


def test_no_other_motor_folder_placeholder_is_left():
    stale = []
    for path in SCRIPTS.rglob("*.py"):
        if path.name == "test_guidance.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "db17-<robot>-<motor>" in text or "db17-<robot>-<left|right>" in text:
            stale.append(path.name)
    assert stale == []


def test_track_video_lists_the_experiment_names(capsys):
    text = _help("track_video", capsys)
    for name in ("A-dense", "C", "A-sweep", "B", "B+D", "E-air", "E-floor"):
        assert name in text
    assert "E1" in text and "E2" in text


def test_plot_help_says_the_defaults_reproduce_the_article(capsys):
    text = _help("plot_case_study_csme2026", capsys)
    assert "article" in text
    assert "--folder db17-r5-left-m9 --label R5-L-m9" in text


def test_folder_name_error_shows_the_placeholder_and_an_example():
    with pytest.raises(ValueError) as exc:
        layout.parse_motor_folder("db17-r5-lef-m9")
    assert PLACEHOLDER in str(exc.value) and "db17-r5-left-m9" in str(exc.value)


def test_two_matching_runs_say_how_to_fix_it(tmp_path):
    config = cs.configure("db17-r5-left-m9", "R5-L-m9")
    for name in ("R5-L-m9_C_b060p040_rep01-03_20261105", "R5-L-m9_C_b060p040_x"):
        (tmp_path / f"{name}.parquet").touch()
    with pytest.raises(FileNotFoundError) as exc:
        cs._one_run(tmp_path, config.e2_run)
    text = str(exc.value)
    assert "R5-L-m9_C_b060p040_x" in text  # names the runs found
    assert "runs.csv" in text and "process_raw.py" in text
    assert "R5-L-m9_C_b060p040_x.parquet" in text  # the file to delete


def test_no_matching_run_says_how_to_fix_it(tmp_path):
    config = cs.configure("db17-r5-left-m9", "R5-L-m9")
    with pytest.raises(FileNotFoundError) as exc:
        cs._one_run(tmp_path, config.e1_run)
    assert "process_raw.py" in str(exc.value)
    assert "R5-L-m9_A_sweep_dense_" in str(exc.value)
