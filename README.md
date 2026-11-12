---
title: "course-automatic-control-experiment-duckiebot"
author: "Torbjörn E. M. Nordling"
date: "2026-11-12"
version: "0.2"
license: "Apache-2.0"
purpose: "Instructions, analysis code, and report template for Experiment 2, and the groups' data and reports."
type: "student"
---

# course-automatic-control-experiment-duckiebot

Automatic Control Student Material for the Duckiebot Experiments

Write everything in this repository in English: reports, code, comments, file names, and commit messages.

## Experiment 2 in brief

You measure how the wheel of a Duckiebot DB17 responds to steps of the motor's PWM duty cycle, and show where the linear first-order model of the course fails: dead zone, duty-dependent gain and time constant, and hysteresis.
The Raspberry Pi of the robot drives the motor and logs every command, while a phone films the spinning wheel with a sync LED in view.
The code in `scripts/` turns each video and the Pi log into wheel angle, speed, and input, and draws the figures of the case study.

- 8 Duckiebots, R1 to R8, so 8 groups, one robot per group.
- Each group hands in one report, written together.
- The software on the Duckiebot is already on its SD card;
  this repository holds only the code that runs on your computer.

## Hand-in: two pull requests

You hand in by opening two pull requests to this repository, <https://github.com/nordlinglab/course-automatic-control-experiment-duckiebot>:

1. **Data pull request**, first.
   It adds your group's motor folders in `data/raw/`, organised and named as described under [Data](#data), and nothing else.
   A teaching assistant reviews it;
   fix what the review asks for and push again until the teaching assistant approves it.
2. **Report pull request**, after the data pull request is approved.
   It adds the LaTeX source of your group report in `doc/report_FamilynameYEAR_TwoTitleWords_Group<NN>/`, and any change you made to `scripts/`.
   **Deadline: 2026-11-26.**

Commit the LaTeX source, the bibliography, and the figures, never the compiled PDF.
[Step by step](#step-by-step-accounts-tools-and-hand-in) shows how, from creating a GitHub account onwards.

## Files provided

The steps are those of [From video to figures](#from-video-to-figures).

| File | Use |
|---|---|
| `README.md` | These instructions. |
| `data/schema.md` | Every stored variable, its format, and how each derived quantity and its uncertainty is computed; the scripts cite its sections as §. |
| `doc/template_Nordling2026_LatexExample/` | Example report: copy it to start your group report. |
| `doc/lecture_Nordling2026_Exp2/` | Slides of the Experiment 2 lecture. |
| `assets/image/` | Screenshots for the step-by-step instructions. |
| `requirements.txt` | Python packages the scripts need. |
| `scripts/track_video.py` | Step 2: tracks the marker, hub, and sync LED in one video and writes its frame table `frames/<run>.parquet`; prints the row for `runs.csv`. |
| `scripts/process_raw.py` | Step 3: synchronises the Pi command log with the video through the LED and computes wheel angle, speed, acceleration, and input, with uncertainty, into `data/processed/`. |
| `scripts/quality_report.py` | Step 3: writes `quality.md` in the motor folders you name, with the checks, warnings, and recommendations. |
| `scripts/select_wheel_frames.py` | Step 5, optional: picks the video frames shown in the wheel-overlay figure of the article's supplement. |
| `scripts/plot_case_study_csme2026.py` | Step 4: fits the models and draws the case-study figures (small duty, step to 0.6, step to 1.0, hysteresis, rest noise, methods, wheel overlay) and writes their numbers as LaTeX macros in `results.tex`. |
| `scripts/duckiebot_analysis/` | The library the scripts import: `tracking/` (video and blob tracking), `data/` (file formats and Pi logs), `analysis/` (angle, sync, processing, quality, case study), `models/`, and `visualization/` (figures). |
| `scripts/tests/test_student_kit.py` | Tests of the trial names, folder names, LED colour, and motor selection. |

## Using the code

### Install once

You need Python 3.12 or newer, which NumPy and SciPy require, and FFmpeg (`ffmpeg` and `ffprobe` on the PATH).
From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows in Git Bash, activate with `source .venv/Scripts/activate`.
Activate again in every new terminal, and check the installation with `pytest scripts/tests`.

### From video to figures

Run every command from the repository root.
The example is robot R5, left wheel, motor m9;
replace the names with yours.

1. Create the motor folder and copy the Pi logs into it unchanged, as described under [Data](#data).
2. Track each video:

   ```bash
   python scripts/track_video.py <video-folder>/<run>.mp4 \
       --folder data/raw/db17-r5-left-m9 --mode stand \
       --camera "phone slow motion 1280x720 240 fps" \
       --experiment <label> --sync log+led \
       --pi-log "pi/<trial1>_events.csv;pi/<trial2>_events.csv" \
       --trials "<trial1>;<trial2>" \
       >> data/raw/db17-r5-left-m9/runs.csv
   ```

   The defaults are the kit's blue marker tape and green sync LED.
   Check the first line it prints, `<n> frames, marker absent in <m>`;
   if `m` is large, give a wider colour rule with `--marker-colour`, and use the same rule for every clip.
   To track a video again, first delete its row from `runs.csv`, then rerun the command with `--force`, which replaces the frame table;
   `runs.csv` must list each run once.
3. Process the motor folder and check its quality:

   ```bash
   python scripts/process_raw.py data/raw/db17-r5-left-m9
   python scripts/quality_report.py --raw data/raw --processed data/processed \
       db17-r5-left-m9
   ```

   Name only your own motor folders, so that the report leaves other groups' `quality.md` unchanged.
   Read `data/raw/db17-r5-left-m9/quality.md`.
   A warning means the data should not be used for the quantities it affects:
   use a clean trial of the same condition, or record the clip again.
   Every trial should report `log+led`, which shows the LED was read.
4. Draw the figures and compute the numbers:

   ```bash
   python scripts/plot_case_study_csme2026.py --data data \
       --folder db17-r5-left-m9 --label R5-L-m9 \
       --figures build/figures/db17-r5-left-m9
   ```

   It needs one run of the dense sweep (E1, run name `R5-L-m9_A_sweep_dense_...`) and one run of the steps 0 → 0.6 → 1.0 → 0.6 → 0 (E2, run name `R5-L-m9_C_b060p040...`), and stops if it finds more than one.
   Copy the figures your report uses into its `figures/` folder.
5. Optional, for the wheel-overlay figure, run before step 4:

   ```bash
   python scripts/select_wheel_frames.py <video-folder>/<run>.mp4 --turns ccw
   ```

   with `--turns` set to `positive_duty_turns` of the motor's `setup.toml`.

## Data

The data is organised exactly as in the dataset of the article.

### What to commit

Commit only measured data, small enough for git:

- the frame table of each video, `frames/<run>.parquet` (about 1 MB each);
- the Pi logs, unchanged;
- `runs.csv`, `trials.csv`, `setup.toml`, and `quality.md`;
- hand measurements in `manual/`.

Never commit:

- videos (1 to 2.4 GB each): keep them outside the repository and back them up;
  `runs.csv` names each by its SHA-256 checksum;
- `data/processed/` and `data/interim/`, which the scripts regenerate from `data/raw/`;
- `build/`, compiled PDFs, `.venv/`, and caches.

`.gitignore` already excludes all of these.
Add files by name, such as `git add data/raw/db17-r5-left-m9/runs.csv`, never with `git add .`.

### Folders

```text
data/
├── schema.md                     variables, formats, and derivations
├── raw/                          measured data, committed, never edited
│   └── db17-<robot>-<position>-<motor>/   one folder per motor
│       ├── README.md             group, people, dates, and notes on the runs
│       ├── quality.md            checks and warnings, generated
│       ├── setup.toml            constants of the setup
│       ├── runs.csv              one row per video
│       ├── trials.csv            one row per trial
│       ├── frames/<run>.parquet  one frame table per video
│       ├── pi/                   the Pi logs, unchanged
│       └── manual/               values read or written by hand
├── processed/                    computed from raw/, not committed
└── interim/                      scratch files, not committed
```

### Folder names

A motor folder is named `db17-<robot>-<position>-<motor>`, all in lower case:

- `<robot>` is the robot the motor was mounted on, `r1` to `r8`.
- `<position>` is `left` or `right`, the wheel the motor drives, as seen from behind the robot driving forward.
- `<motor>` is the motor's number, `m1` to `m16`, written on the motor.
- A run that drives both wheels goes in `db17-<robot>-both-<left motor>-<right motor>`.

For example, `db17-r5-left-m9` and `db17-r5-both-m9-m10`.
The Pi writes its logs under the label `R5-L-m9`;
copy them unchanged into `data/raw/db17-r5-left-m9/pi/`, together with `motor_mapping.json`, and check that the SHA-256 checksums of both copies match.

### File names

- A run is one video.
  Its name is the video's file name without extension, starting with the Pi label, such as `R5-L-m9_C_b060p040_rep01-03_20261112`.
  Rename the video to its clip name before tracking it, and never rename it afterwards.
- A trial is one command sequence sent by the Pi, named by the Pi, such as `R5-L-m9_C_b060p040_rep01_20261112_142210`.
  A run holds one or more trials.
- Keep the file names the Pi gave its logs.

### Describe the setup

`setup.toml` holds the constants of the setup, for example:

```toml
robot = "r5"
motor = "left"
motor_label = "m9"
hat = "Adafruit DC & Stepper Motor HAT, PCA9685 at 0x60"
hat_channel = "M1"
pwm_frequency_hz = 1600
quantisation = "pca9685"
supply = "5.1 V mains adapter, powering both the Pi and the motor HAT"
positive_duty_turns = "cw"
marker = "blue tape on the yellow wheel, from the hub to the rim"
sync_led = "green LED on GPIO21, switched just before every motor command"
```

`positive_duty_turns` is `cw` or `ccw`, the direction a positive duty turns the wheel as the camera sees it.
Start `runs.csv` and `trials.csv` with these header lines:

```text
run,video_file,video_sha256,video_bytes,duration_s,resolution,fps_nominal,mode,experiment,sync,pi_log,trials,notes
```

```text
trial,run,script,script_commit,args,start_pi,duration_s,changes,status,notes
```

`track_video.py` prints the `runs.csv` rows;
write one `trials.csv` row per trial from its `_meta.json`.
`data/schema.md` defines every column.

## Your group report

Place the report in its own folder in `doc/`, named

```text
doc/report_FamilynameYEAR_TwoTitleWords_Group<NN>/
```

- `Familyname` is the family name of the first author, in ASCII letters.
- `YEAR` is the four-digit year of the report.
- `TwoTitleWords` is two words from the report title, each starting with a capital letter.
- `<NN>` is your two-digit group number.

For example, `doc/report_Andersson2026_WheelDynamics_Group03/`:

```text
doc/report_Andersson2026_WheelDynamics_Group03/
├── main.tex
├── references.bib
└── figures/
    └── fig-step-06.pdf
```

List every group member as an author, with their student ID, in order of falling contribution, and describe each member's contribution in the Contributions section with the CRediT roles, as the example report shows.

## Writing the report

We recommend LaTeX with the standard `article` class and APA references through `biblatex-apa`.
The report must compile with `pdflatex`, or with LuaLaTeX when it contains Chinese text, as Appendix B of the example report explains.

Start from the example report in `doc/template_Nordling2026_LatexExample/`: copy the folder to your report folder and replace its text.
The example has the structure of a technical report, and its text explains how to write each section and how to format figures, tables, equations, units, citations, and code.
Its minimal skeleton is:

```latex
\documentclass{article}
\usepackage[T1]{fontenc}
\usepackage{graphicx}
\usepackage{csquotes}
\usepackage[backend=biber,style=apa,annotation=false]{biblatex}
\addbibresource{references.bib}

\title{Nonlinear Dynamics of a Duckiebot Wheel Motor}
\author{Ann Andersson \and Bo-Wei Chen \and Carlos Garcia}

\begin{document}
\maketitle
...
\begin{figure}
  \centering
  \includegraphics[width=\linewidth]{figures/fig-step-06.pdf}
  \caption{...}
\end{figure}
...
\section*{Contributions}
...
\printbibliography
\end{document}
```

Compile it into `build/` from the repository root, which runs `pdflatex` and `biber` as often as needed:

```bash
latexmk -pdf -cd \
  -outdir=../../build/report_Andersson2026_WheelDynamics_Group03 \
  doc/report_Andersson2026_WheelDynamics_Group03/main.tex
```

## Step by step: accounts, tools, and hand-in

Git keeps the history of every file in a repository, and GitHub stores repositories online.
You need no earlier experience with either:
follow these steps in order.
Steps 1, 2, and 4 are for every group member, step 3 for one member only.

### 1. Create a GitHub account (every member)

Open <https://github.com/signup>, enter your email address, a password, and a username, and confirm the code GitHub sends to your email.
Tell your group members your username.

![GitHub sign-up page](assets/image/github-signup.jpg)

### 2. Install git (Windows only)

macOS and Linux include git;
on macOS, the first `git` command you type in Terminal offers to install the Command Line Tools, which contain it.
On Windows, open <https://git-scm.com/install/windows>, click **Click here to download**, run the installer, and accept every default setting.
It installs **Git Bash**, the terminal in which you type every command of this README on Windows.

![Git for Windows download page](assets/image/git-install-windows.jpg)

Then tell git your name and email address once, in Git Bash or Terminal, with the email of your GitHub account:

```bash
git config --global user.name "Ann Andersson"
git config --global user.email "ann.andersson@example.com"
```

### 3. Fork the repository for your group (one member)

A **fork** is your group's own copy of this repository on GitHub.
You may change your fork freely;
a **pull request** then asks the teaching assistants to copy your changes from the fork into this repository.

1. Open <https://github.com/nordlinglab/course-automatic-control-experiment-duckiebot>, sign in, and click **Fork**.

   ![Fork button of the course repository](assets/image/github-repository-fork.jpg)

2. Keep the owner (your username) and the name, and click **Create fork**.

   ![Create a new fork](assets/image/github-fork-create.jpg)

3. In your fork, open **Settings**, then **Collaborators**, and click **Add people**.

   ![Collaborators settings of the fork](assets/image/github-fork-collaborators.jpg)

4. Type the username of a group member and click **Add to repository**;
   repeat for every member.
   Each member then accepts the invitation in the email from GitHub, or under the bell icon at the top right of github.com.

   ![Add people dialog](assets/image/github-fork-add-people.jpg)

### 4. Copy the fork to your computer (every member)

On the page of your group's fork, click **Code** and copy the HTTPS address.

![Code button with the clone address](assets/image/github-repository-clone-url.jpg)

In Git Bash or Terminal, go to the folder where you keep your course work, and type, with that address:

```bash
git clone <address of your group's fork>
cd course-automatic-control-experiment-duckiebot
git remote add upstream \
  https://github.com/nordlinglab/course-automatic-control-experiment-duckiebot.git
```

`clone` copies the fork, and `remote add` names this course repository `upstream`, so you can start your report from its latest version.

The first time you push, git asks you to sign in to GitHub:

- **Windows:** a window opens;
  choose to sign in with your browser.
- **macOS and Linux:** git asks for your username and a password.
  GitHub refuses your account password here, so create a token instead:
  open <https://github.com/settings/tokens/new>, write a note such as `course`, keep the expiration, tick **public_repo**, click **Generate token** at the bottom, and paste the token as the password.
  macOS remembers it;
  on Linux, run `git config --global credential.helper store` first so that you need to paste it only once.

![New personal access token](assets/image/github-token-classic.jpg)

### 5. Hand in the data: pull request 1

Work on a branch, a named line of commits, so that your hand-in stays separate from `main`:

```bash
git switch -c group03-data
cd data/raw/db17-r5-left-m9
git add README.md setup.toml runs.csv trials.csv quality.md
git add frames/*.parquet pi/* manual/*
git commit -m "Add data of robot R5, left wheel, motor m9"
git push -u origin group03-data
cd ../../..
```

- `switch -c` creates the branch and moves to it.
- `add` chooses the files to save, each by name;
  `git status` lists what you changed and what you are about to commit.
- `commit` saves them with a message that says what they are.
- `push` sends the branch to your fork.
- `git pull` later fetches the commits your group members pushed;
  run it each time before you start work.

Then open your fork on GitHub, click **Contribute**, and **Open pull request**.

![Contribute and Open pull request](assets/image/github-contribute-pull-request.jpg)

Check that the base repository is `nordlinglab/course-automatic-control-experiment-duckiebot` with base `main`, and the head repository is your fork with your branch.
Write a title, list your group members in the description, and click **Create pull request**.

![Open a pull request](assets/image/github-pull-request-form.jpg)

### 6. Answer the review

A teaching assistant reviews the pull request and writes comments on it.
Fix what they ask for on the same branch, then `git add`, `git commit`, and `git push` again:
the pull request updates itself.
Do not open a new pull request.
When the teaching assistant approves it, the data is part of this repository.

### 7. Hand in the report: pull request 2

After the data pull request is approved, start a new branch from the latest version of this repository, which now holds your data:

```bash
git fetch upstream
git switch -c group03-report upstream/main
git add doc/report_Andersson2026_WheelDynamics_Group03/main.tex
git add doc/report_Andersson2026_WheelDynamics_Group03/references.bib
git add doc/report_Andersson2026_WheelDynamics_Group03/figures/fig-step-06.pdf
git commit -m "Add the group report"
git push -u origin group03-report
```

Open the pull request as in step 5, by **2026-11-26**.

### On an iPad

An iPad can do every step except the analysis, which needs FFmpeg, NumPy, SciPy, and pyarrow:
run the scripts on a group member's Windows, macOS, or Linux computer.

**In Safari, without an app.**
Steps 1 and 3 work as above on github.com.
Instead of steps 4 and 5:

1. On your fork, open the branch menu, type `group03-data`, and click **Create branch group03-data from main**.

   ![Create a branch](assets/image/github-branch-create.jpg)

2. Click **Add file**:
   **Create new file** makes a file, and **Upload files** adds files from your iPad to the folder you are in.

   ![Add file menu](assets/image/github-add-file-menu.jpg)

3. To make a folder, create a file in it:
   type the whole path as the file name, such as `data/raw/db17-r5-left-m9/README.md`, where every `/` starts a new folder, write the file, and click **Commit changes**.

   ![Create a new file in new folders](assets/image/github-new-file.jpg)

4. Commit directly to your branch, never to `main`.

   ![Commit changes dialog](assets/image/github-commit-dialog.jpg)

5. Open the new folder, choose **Add file**, **Upload files**, select the files, and commit them to your branch.
   GitHub accepts files of up to 25 MB through the browser.

   ![Upload files](assets/image/github-upload-files.jpg)

6. Open the pull request with **Contribute** as in step 5.

For the report, use **Overleaf** (<https://www.overleaf.com>) in Safari: upload the files of the example report to a new project, write, and compile there.
Then download the source with **Menu**, **Download**, **Source**, and upload `main.tex`, `references.bib`, and the figures to your report folder on a branch `group03-report`, made after the data pull request is approved.
Before you make that branch, click **Sync fork** on your fork, so that it holds the approved data.

**With an app.**
**Working Copy**, in the App Store, is a git app for iPad that clones, commits, and pushes like the commands above.
Some of its features need a paid unlock;
check in the App Store which ones before you rely on it.

## Connecting to the Duckiebot

You control the robot's Raspberry Pi from your computer with SSH, a terminal on the Pi, and copy its logs with `scp`.
Windows 10 and 11, macOS, and Linux include both commands;
type them in Git Bash, PowerShell, or Terminal.
On an iPad, install an SSH app such as **Termius** from the App Store.

Your computer must be on the same Wi-Fi network as the robot.
The teaching assistants give you the robot's user name, address, and password.

```bash
ssh <user>@<address>
```

- The first time, SSH asks whether to trust the robot: type `yes`.
- The password does not show while you type it.
- Start `tmux new -A -s run` on the Pi before a test, so that the test continues if the connection drops;
  the same command reconnects.
- Ctrl+C stops the motors;
  `exit` closes the connection.

Copy the Pi logs of your motor into your motor folder, on your computer, not on the Pi:

```bash
scp '<user>@<address>:fresh_motor_study/data/raw/R5-L-m9/*' \
  data/raw/db17-r5-left-m9/pi/
scp '<user>@<address>:fresh_motor_study/metadata/motor_mapping.json' \
  data/raw/db17-r5-left-m9/pi/
```
