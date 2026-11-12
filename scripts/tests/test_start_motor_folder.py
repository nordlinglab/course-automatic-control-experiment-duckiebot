# Copyright 2026 Torbjörn E. M. Nordling <t@nordlinglab.org>
# SPDX-License-Identifier: Apache-2.0
"""Tests of scripts/start_motor_folder.py: a new motor folder and its trials.

Run from the repository root: python -m pytest scripts/tests
"""

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from duckiebot_analysis.data.layout import (  # noqa: E402
    RUNS_COLUMNS,
    TRIALS_COLUMNS,
    read_runs,
    read_setup,
    read_trials,
)

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = "scripts/start_motor_folder.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, SCRIPT, *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def folder(tmp_path) -> Path:
    return tmp_path / "data" / "raw" / "db17-r5-left-m9"


# ------------------------------------------------- a new folder


def test_creates_every_file_and_folder_the_readers_need(folder):
    out = _run(str(folder))
    assert out.returncode == 0, out.stderr
    for sub in ("frames", "pi", "manual"):
        assert (folder / sub).is_dir()
    assert (folder / "manual" / "README.md").read_text(encoding="utf-8").strip()
    assert (folder / "README.md").read_text(encoding="utf-8").strip()
    assert (folder / "runs.csv").read_text(encoding="utf-8") == (
        ",".join(RUNS_COLUMNS) + "\n"
    )
    assert (folder / "trials.csv").read_text(encoding="utf-8") == (
        ",".join(TRIALS_COLUMNS) + "\n"
    )
    assert read_runs(folder) == []
    assert read_trials(folder) == []


def test_setup_toml_is_filled_from_the_folder_name_and_the_kit(folder):
    assert _run(str(folder)).returncode == 0
    setup = read_setup(folder)
    assert (setup.robot, setup.motor, setup.motor_label) == ("r5", "left", "m9")
    assert setup.hat == "Adafruit DC & Stepper Motor HAT, PCA9685 at 0x60"
    assert setup.pwm_frequency_hz == 1600
    assert setup.quantisation == "pca9685"
    assert setup.supply == "5.1 V mains adapter, powering both the Pi and the motor HAT"
    assert setup.positive_duty_turns == "cw"
    assert setup.extra["marker"] == (
        "blue tape on the yellow wheel, from the hub to the rim"
    )
    assert setup.extra["sync_led"] == (
        "green LED on GPIO21, switched just before every motor command"
    )
    text = (folder / "setup.toml").read_text(encoding="utf-8")
    lines = text.splitlines()
    k = next(i for i, x in enumerate(lines) if x.startswith("positive_duty_turns"))
    # Tells the student to check by eye.
    assert "ccw" in lines[k - 1] and "camera" in lines[k - 1]


def test_a_both_folder_lists_the_left_then_the_right_motor(tmp_path):
    folder = tmp_path / "raw" / "db17-r5-both-m9-m10"
    assert _run(str(folder)).returncode == 0
    setup = read_setup(folder)
    assert (setup.motor, setup.motor_label) == ("both", "m9, m10")


def test_process_raw_accepts_the_new_folder(folder, tmp_path):
    assert _run(str(folder)).returncode == 0
    out = subprocess.run(
        [
            sys.executable,
            "scripts/process_raw.py",
            str(folder),
            "--out",
            str(tmp_path / "processed"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.returncode == 0, out.stderr


def test_never_overwrites_an_existing_file(folder):
    folder.mkdir(parents=True)
    (folder / "runs.csv").write_text("mine\n", encoding="utf-8")
    (folder / "README.md").write_text("ours\n", encoding="utf-8")
    out = _run(str(folder))
    assert out.returncode == 0, out.stderr
    assert (folder / "runs.csv").read_text(encoding="utf-8") == "mine\n"
    assert (folder / "README.md").read_text(encoding="utf-8") == "ours\n"
    assert "runs.csv" in out.stdout and "README.md" in out.stdout
    assert (folder / "trials.csv").is_file()


@pytest.mark.parametrize(
    "name",
    [
        "db17-r5-lef-m9",  # typo in the position
        "db17-R5-left-m9",  # upper case
        "db17-r5-left",  # no motor identifier
        "db17-r5-both-m9",  # both needs two identifiers
        "r5-left-m9",
        "",
    ],
)
def test_a_bad_name_is_refused_in_plain_words(tmp_path, name):
    folder = tmp_path / "raw" / name if name else tmp_path / "raw" / " "
    out = _run(str(folder))
    assert out.returncode == 1
    assert "Traceback" not in out.stderr
    assert out.stderr.startswith("error:")
    assert "db17-r5-left-m9" in out.stderr  # shows a correct example
    assert not folder.exists()


def test_a_folder_outside_raw_is_refused(tmp_path):
    folder = tmp_path / "db17-r5-left-m9"
    out = _run(str(folder))
    assert out.returncode == 1
    assert "Traceback" not in out.stderr and "raw" in out.stderr
    assert not folder.exists()


def test_help_names_the_placeholder_and_an_example():
    out = _run("--help")
    assert out.returncode == 0
    assert "db17-<robot>-<position>-<motor>" in out.stdout
    assert "db17-r5-left-m9" in out.stdout


# ------------------------------------------------- --trials

# The meta file motor_trial.py writes on the Pi, as in the kit's sample data.
_E1 = "R5-L-m9_A_sweep_{}_010to036by020_rep01_20261105_1{}"
_E2 = "R5-L-m9_C_b060p040_rep0{}_20261105_12000{}"


def _meta(trial: str, when: str, schedule: list, **extra) -> dict:
    return {
        "trial_id": trial,
        "date_time": when,
        "robot_id": "R5",
        "motor_id": "m9",
        "position": "L",
        "parameters": {"exp": trial.split("_")[1]},
        "schedule": schedule,
        "script": "motor_trial.py",
        "script_version": "22498d6a4948",
        "dry_run": False,
        "status": "completed",
        **extra,
    }


_SCHEDULE_B = [
    [0.0, 0.0, False, "rest"],
    [2.0, 0.3, True, "step"],
    [10.0, 0.0, False, "off"],
    [12.04, 0.0, False, "end"],
]


def _write_meta(folder: Path, meta: dict) -> None:
    path = folder / "pi" / f"{meta['trial_id']}_meta.json"
    path.write_text(json.dumps(meta), encoding="utf-8")


@pytest.fixture
def with_trials(folder) -> Path:
    assert _run(str(folder)).returncode == 0
    _write_meta(
        folder,
        _meta(_E1.format("forward", "10000"), "2026-11-05T10:01:00", _SCHEDULE_B),
    )
    _write_meta(
        folder,
        _meta(_E1.format("backward", "10200"), "2026-11-05T10:03:00", _SCHEDULE_B),
    )
    for k in (1, 2):
        _write_meta(
            folder, _meta(_E2.format(k, k), f"2026-11-05T12:0{k}:00", _SCHEDULE_B)
        )
    return folder


def _rows(folder: Path) -> list[dict[str, str]]:
    with open(folder / "trials.csv", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_trials_writes_one_row_per_meta_file_as_the_guide_defines(with_trials):
    out = _run(str(with_trials), "--trials")
    assert out.returncode == 0, out.stderr
    rows = _rows(with_trials)
    trial = _E1.format("forward", "10000")
    assert rows[0] == {
        "trial": trial,
        "run": "",
        "script": "motor_trial.py",
        "script_commit": "",
        "args": "",
        "start_pi": "2026-11-05T10:01:00",
        "duration_s": "12.0",
        "changes": "3",
        "status": "completed",
        "notes": "script SHA-256 starts 22498d6a4948; "
        f"arguments in pi/{trial}_meta.json (parameters)",
    }
    # In the order the trials ran.
    assert [r["start_pi"] for r in rows] == sorted(r["start_pi"] for r in rows)
    assert len(rows) == 4
    # The empty run is pointed out, with the command that fills it.
    assert "--run" in out.stdout and "--match" in out.stdout


def test_trials_fills_the_run_of_the_matching_trials(with_trials):
    e1_run = "R5-L-m9_A_sweep_dense_forward-backward_010to036by020_rep01_20261105"
    out = _run(str(with_trials), "--trials", "--run", e1_run, "--match", "_A_sweep_")
    assert out.returncode == 0, out.stderr
    runs = {r["trial"]: r["run"] for r in _rows(with_trials)}
    assert runs[_E1.format("forward", "10000")] == e1_run
    assert runs[_E1.format("backward", "10200")] == e1_run
    assert runs[_E2.format(1, 1)] == ""


def test_trials_fills_an_empty_run_of_a_listed_trial_and_keeps_a_filled_one(
    with_trials,
):
    assert _run(str(with_trials), "--trials").returncode == 0
    assert (
        _run(str(with_trials), "--trials", "--run", "E2", "--match", "_C_").returncode
        == 0
    )
    assert (
        _run(str(with_trials), "--trials", "--run", "X", "--match", "R5").returncode
        == 0
    )
    rows = _rows(with_trials)
    assert len(rows) == 4  # nothing listed twice
    runs = {r["trial"]: r["run"] for r in rows}
    assert runs[_E2.format(1, 1)] == runs[_E2.format(2, 2)] == "E2"
    assert runs[_E1.format("forward", "10000")] == "X"
    assert read_trials(with_trials)  # every run is filled, so it reads


def test_trials_keeps_rows_typed_by_hand(with_trials):
    path = with_trials / "trials.csv"
    typed = "T1,R1,s.py,,,,,,completed,by hand"  # no final newline
    path.write_text(path.read_text(encoding="utf-8") + typed, encoding="utf-8")
    assert _run(str(with_trials), "--trials").returncode == 0
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[1] == typed
    assert len(lines) == 6


def test_trials_output_is_read_by_read_trials(with_trials):
    assert (
        _run(
            str(with_trials), "--trials", "--run", "V1", "--match", "R5-L-m9"
        ).returncode
        == 0
    )
    trials = read_trials(with_trials)
    assert len(trials) == 4
    assert trials[0].duration_s == 12.0 and trials[0].changes == 3


def test_trials_skips_a_dry_run(with_trials):
    _write_meta(
        with_trials,
        _meta(
            "R5-L-m9_B_p030_rep01_20261105_130000",
            "2026-11-05T13:00:00",
            _SCHEDULE_B,
            dry_run=True,
        ),
    )
    out = _run(str(with_trials), "--trials")
    assert out.returncode == 0
    assert "R5-L-m9_B_p030" not in (with_trials / "trials.csv").read_text(
        encoding="utf-8"
    )
    assert "dry run" in out.stdout


def test_trials_without_meta_files_says_where_to_put_them(folder):
    assert _run(str(folder)).returncode == 0
    out = _run(str(folder), "--trials")
    assert out.returncode == 1
    assert "Traceback" not in out.stderr and "pi" in out.stderr


def test_trials_reports_a_broken_meta_file_in_plain_words(with_trials):
    (with_trials / "pi" / "R5-L-m9_bad_meta.json").write_text("{", encoding="utf-8")
    out = _run(str(with_trials), "--trials")
    assert out.returncode == 1
    assert "Traceback" not in out.stderr
    assert "R5-L-m9_bad_meta.json" in out.stderr


def test_run_and_match_need_each_other_and_trials(with_trials):
    for args in (
        ["--trials", "--run", "V"],
        ["--trials", "--match", "R5"],
        ["--run", "V", "--match", "R5"],
    ):
        out = _run(str(with_trials), *args)
        assert out.returncode != 0
        assert "Traceback" not in out.stderr


def test_trials_on_a_missing_folder_says_to_create_it_first(folder):
    out = _run(str(folder), "--trials")
    assert out.returncode == 1
    assert "Traceback" not in out.stderr
    assert not folder.exists()
