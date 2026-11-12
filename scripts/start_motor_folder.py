#!/usr/bin/env python3
# Copyright 2026 Torbjörn E. M. Nordling <t@nordlinglab.org>
# SPDX-License-Identifier: Apache-2.0
"""Start a motor folder, or list the Pi's trials in its trials.csv.

Step 1 of README.md, From video to figures. Without --trials, it creates the
motor folder db17-<robot>-<position>-<motor> inside data/raw with frames/,
pi/, manual/, an empty runs.csv and trials.csv, a setup.toml filled in for
the course kit, and a README.md to complete (data/schema.md §2). An existing
file is never overwritten.

With --trials, it reads every pi/*_meta.json that motor_trial.py wrote and
adds one row to trials.csv for each trial not yet listed (data/schema.md §5).
--run and --match fill in the video (run) of the trials whose name contains
the given text, also for trials listed earlier without a run.

Examples:
    python scripts/start_motor_folder.py data/raw/db17-r5-left-m9
    python scripts/start_motor_folder.py data/raw/db17-r5-left-m9 --trials
    python scripts/start_motor_folder.py data/raw/db17-r5-left-m9 --trials \\
        --run R5-L-m9_C_b060p040_rep01-03_20261105 --match _C_b060p040_
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path

from duckiebot_analysis.data.layout import (
    RUNS_COLUMNS,
    TRIAL_STATUSES,
    TRIALS_COLUMNS,
    motor_ids,
    parse_motor_folder,
)

COMMAND = "python scripts/start_motor_folder.py"
EXAMPLE = "data/raw/db17-r5-left-m9"
NAME_RULE = (
    "Name it db17-<robot>-<position>-<motor>, such as db17-r5-left-m9: the "
    "robot, then left or right (where the motor sits on the robot), then the "
    "number written on the motor, in lower-case letters and digits only. For a "
    "test that drives both motors, use db17-<robot>-both-<left motor>-<right "
    "motor>, such as db17-r5-both-m9-m10."
)

SETUP_TOML = """\
# Constants of the setup (data/schema.md section 6). Check every value against
# your robot, correct what differs, and delete a line you do not know.
robot = "{robot}"  # from the folder name
# The position of the motor on the robot, from the folder name:
motor = "{motor}"
# The number written on the motor (for both: left, then right), from the folder name:
motor_label = "{label}"
hat = "Adafruit DC & Stepper Motor HAT, PCA9685 at 0x60"
pwm_frequency_hz = 1600  # MotorKit default
quantisation = "pca9685"  # motor_trial.py writes the duty straight to the HAT
supply = "5.1 V mains adapter, powering both the Pi and the motor HAT"
# Check by eye: cw or ccw, as the camera sees the wheel turn at a positive duty.
positive_duty_turns = "cw"
marker = "blue tape on the yellow wheel, from the hub to the rim"
sync_led = "green LED on GPIO21, switched just before every motor command"
"""

README = """\
# {name}

- Group:
- Members:
- Date of the recordings:
- Robot: {robot}, {motors}
- Notes: anything that affects the use of the data, such as a video recorded twice
"""

MANUAL_README = """\
# Hand measurements

This folder holds the values measured by hand, such as the wheel radius, in
`measurements.csv` (data/schema.md section 8), and photos or scans of the
sheets they were written on.
"""


class UserError(Exception):
    """A mistake the student can fix; printed as one line, without traceback."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line."""
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument(
        "folder",
        type=Path,
        help="motor folder data/raw/db17-<robot>-<position>-<motor>, "
        f"such as {EXAMPLE}",
    )
    p.add_argument(
        "--trials",
        action="store_true",
        help="add the trials of pi/*_meta.json to trials.csv",
    )
    p.add_argument(
        "--run",
        help="with --trials and --match: the video file name without .mp4",
    )
    p.add_argument(
        "--match",
        help="with --trials and --run: text that the names of the video's "
        "trials contain, such as _C_b060p040_",
    )
    args = p.parse_args(argv)
    if (args.run is None) != (args.match is None):
        p.error("give --run and --match together")
    if args.run is not None and not args.trials:
        p.error("--run and --match only work together with --trials")
    if args.match == "" or args.run == "":
        p.error("--run and --match must not be empty")
    return args


def check_folder(folder: Path) -> tuple[str, str, tuple[str, ...]]:
    """Return the robot, position, and motor labels of a motor folder path.

    Raises:
        UserError: If the name is not that of a motor folder with its motor
            labels, or the folder is not inside a raw folder.
    """
    try:
        robot, position = parse_motor_folder(folder)
        labels = motor_ids(folder)
    except ValueError:
        raise UserError(f"{folder.name!r} is not a motor folder name. {NAME_RULE}")
    if not labels:
        raise UserError(f"{folder.name!r} lacks the motor's number. {NAME_RULE}")
    if folder.parent.name != "raw":
        raise UserError(
            f"{folder} is not inside a folder named raw; put the motor folder "
            f"in data/raw, such as {EXAMPLE}"
        )
    return robot, position, labels


def create(folder: Path, robot: str, position: str, labels: tuple[str, ...]) -> None:
    """Create the motor folder's subfolders and files; keep any that exist."""
    label = ", ".join(labels)
    files = {
        "README.md": README.format(
            name=folder.name,
            robot=robot,
            motors=f"motor {labels[0]} on the left and {labels[1]} on the right"
            if position == "both"
            else f"motor {labels[0]} on the {position}",
        ),
        "runs.csv": ",".join(RUNS_COLUMNS) + "\n",
        "trials.csv": ",".join(TRIALS_COLUMNS) + "\n",
        "setup.toml": SETUP_TOML.format(robot=robot, motor=position, label=label),
        "manual/README.md": MANUAL_README,
    }
    for sub in ("frames", "pi", "manual"):
        (folder / sub).mkdir(parents=True, exist_ok=True)
    kept = []
    for name, text in files.items():
        path = folder / name
        if path.exists():
            kept.append(name)
            continue
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    if kept:
        print(f"left unchanged, as they already exist: {', '.join(kept)}")
    print(f"{folder} is ready.")
    print("Next: fill in README.md and check every value in setup.toml.")


def _meta_row(path: Path) -> tuple[list[str], str]:
    """Return the trials.csv row of one meta file, with an empty run.

    Returns:
        The row and a message when the trial is skipped (row empty then).

    Raises:
        UserError: If the file is not a meta file of motor_trial.py.
    """
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
        trial = meta.get("trial_id") or path.name.removesuffix("_meta.json")
        if meta.get("dry_run"):
            return [], f"skipped {trial}: a dry run, which did not drive the motor"
        schedule = meta["schedule"]
        duration = f"{float(schedule[-1][0]):.1f}"
        status = meta.get("status") or ""
        notes = []
        if meta.get("script_version"):
            notes.append(f"script SHA-256 starts {meta['script_version']}")
        notes.append(f"arguments in pi/{path.name} (parameters)")
        if status not in TRIAL_STATUSES:
            notes.append(f"Pi status {status!r}")
            status = ""
        row = [
            trial,
            "",
            meta.get("script") or "motor_trial.py",
            "",
            "",
            meta.get("date_time") or "",
            duration,
            str(len(schedule) - 1),
            status,
            "; ".join(notes),
        ]
    except (ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
        raise UserError(
            f"{path} cannot be read ({type(exc).__name__}: {exc}); copy it again "
            "from the Pi, or move it out of pi/ if it is not a trial's meta file"
        ) from None
    return row, ""


def _read_table(path: Path) -> tuple[list[str], list[list[str]], str]:
    """Return the header, data rows, and raw text of trials.csv."""
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if not text.strip():
        return list(TRIALS_COLUMNS), [], ""
    table = [r for r in csv.reader(io.StringIO(text)) if r]
    header = table[0]
    missing = [c for c in TRIALS_COLUMNS if c not in header]
    if missing:
        raise UserError(
            f"{path}: its first line lacks {', '.join(missing)}; it must be "
            f"{','.join(TRIALS_COLUMNS)}"
        )
    # Pad short rows, so every column can be indexed.
    rows = [r + [""] * (len(header) - len(r)) for r in table[1:]]
    return header, rows, text


def _csv_lines(rows: list[list[str]]) -> str:
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(rows)
    return buf.getvalue()


def add_trials(folder: Path, run: str | None, match: str | None) -> int:
    """Add the Pi's trials to trials.csv and fill in runs; return the exit status."""
    if not folder.is_dir():
        raise UserError(
            f"{folder} does not exist; create it first with {COMMAND} {folder}"
        )
    metas = sorted((folder / "pi").glob("*_meta.json"))
    if not metas:
        raise UserError(
            f"no *_meta.json file in {folder / 'pi'}; copy the files that "
            "motor_trial.py wrote on the Pi there first"
        )
    path = folder / "trials.csv"
    header, rows, text = _read_table(path)
    col = {name: header.index(name) for name in TRIALS_COLUMNS}
    listed = {r[col["trial"]] for r in rows}
    new = []
    for meta_path in metas:
        row, skipped = _meta_row(meta_path)
        if skipped:
            print(skipped)
        elif row[0] not in listed:
            new.append(row)
            listed.add(row[0])
    new.sort(key=lambda r: (r[5], r[0]))  # in the order the trials ran
    new = [_in_header_order(r, header) for r in new]

    filled = matched = 0
    rewrite = False  # whether a row already in the file changed
    if match is not None:
        for is_new, r in [(False, r) for r in rows] + [(True, r) for r in new]:
            if match not in r[col["trial"]]:
                continue
            matched += 1
            if not r[col["run"]]:
                r[col["run"]] = run or ""
                filled += 1
                rewrite = rewrite or not is_new
    if rewrite:
        # A listed row changed: write the whole table again.
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(_csv_lines([header, *rows, *new]))
    elif new:
        if not text:
            prefix = _csv_lines([header])
        else:
            prefix = "" if text.endswith("\n") else "\n"
        with open(path, "a", encoding="utf-8", newline="") as fh:
            fh.write(prefix + _csv_lines(new))
    print(f"added {len(new)} trial(s) to {path}")
    if match is not None:
        print(f"set the run of {filled} trial(s) to {run}")
        if matched > filled:
            print(f"kept the run of {matched - filled} trial(s) that already had one")
    empty = [r[col["trial"]] for r in rows + new if not r[col["run"]]]
    if empty:
        more = f", and {len(empty) - 3} more" if len(empty) > 3 else ""
        print(
            f"\n{len(empty)} trial(s) have no run yet: {', '.join(empty[:3])}{more}\n"
            "For each video, give its file name without .mp4 and a text that "
            "only the names of its trials contain:\n"
            f"  {COMMAND} {folder} --trials --run <video name> --match <text>"
        )
    if match is not None and not matched:
        print(f"error: no trial name contains {match!r}", file=sys.stderr)
        return 1
    return 0


def _in_header_order(row: list[str], header: list[str]) -> list[str]:
    """Place a row in TRIALS_COLUMNS order under the file's own header."""
    out = [""] * len(header)
    for name, value in zip(TRIALS_COLUMNS, row, strict=True):
        out[header.index(name)] = value
    return out


def main(argv: list[str] | None = None) -> int:
    """Create the folder or add the trials, and return the exit status."""
    args = parse_args(argv)
    try:
        robot, position, labels = check_folder(args.folder)
        if args.trials:
            return add_trials(args.folder, args.run, args.match)
        create(args.folder, robot, position, labels)
    except (UserError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
