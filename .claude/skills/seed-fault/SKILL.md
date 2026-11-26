---
name: seed-fault
description: Deliberately break the pipeline in one named way to prove a test and the leakage hook catch it. Use when asked to seed, inject or demonstrate a fault. Seeds and records only; it never fixes.
allowed-tools: Read, Edit, Bash(python -m pytest*), Bash(make test), Bash(git diff*), Bash(git status)
---

# Fault to seed: $ARGUMENTS

Work in this order. Do not fix anything: the fix is done in a separate
session that is not told what was broken, so the turns it needs are a fair
measure of how loudly the suite reports the fault.

1. **Predict.** Name the one file and the smallest edit that produces this
   fault, and the test in `tests/` you expect to go red. If no existing
   test should catch it, say so before editing: that is a finding.

2. **Seed it** with a single Edit to that file. If the file is under `src/`,
   the PostToolUse hook runs `tests/test_leakage.py` and, on failure, its
   stderr comes back to you as a message. Quote that message verbatim.
   If no hook message arrives, say so: either the file is outside `src/`
   or the leakage tests stayed green.

3. **Record.** Run `python -m pytest tests/ -q` and show the output
   verbatim. Then run `git diff` and show it: that is the exact change.

4. **Stop.** Report, in this order: the diff, the hook stderr (or "hook did
   not fire"), the red test names, and whether your prediction in step 1
   held. Leave the fault in place.

Never edit `tests/`, `data/raw/`, or `.claude/` while seeding. A fault that
needs one of those is out of scope for this skill.
