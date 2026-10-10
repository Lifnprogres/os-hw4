# Homework 4: Virtual Memory and Scheduling

Justin Saldana

- `vmsched.py`: completed starter program, including the B-g experiment.
- `hw4-answers.html`: all Part A and Part B questions and answers. Download it and open it in a browser; GitHub displays HTML source rather than rendering the answer sheet.
- `baseline-output.txt`: complete actual run before the B-g change, used for the main Part B tables.
- `modified-output.txt`: complete actual run after the B-g change.
- `experiment-plan.txt`: prediction recorded before the modified run.

Run on Windows from PowerShell:

```powershell
py .\vmsched.py
```

On macOS/Linux:

```bash
python3 vmsched.py
```

The submitted program includes RR q=20, marked # B-g. Remove that extra SCHEDULERS entry to reproduce baseline-output.txt.

The outputs were generated in the execution environment, not on the student's Windows computer. The assignment's fixed seeds and deterministic rules make these results reproducible. All experiments ran without a missing-TODO message. Homework 3's explicit lock-order check and all placement self-checks passed. The implementations were additionally checked against independent exhaustive banker orders, unit-time round-robin schedules, and frame-preserving replacement traces. Both answer sheets contain all expected answer IDs and correct table dimensions. The answer sheet includes the original `answer-data` JSON format so it can be loaded into the supplied homework HTML.

Submit this repository's URL, as required by the assignment.
