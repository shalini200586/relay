# Phase 0.2–0.4 — Experiment protocol

The goal is to measure, not guess. Every experiment uses the same throwaway repo, the same 10 planted facts, and the same quiz, so results are comparable across conditions.

## Setup (once)

1. Create a throwaway repo, `C:\Users\82069\Projects\relay-lab`, with:
   - `src/calc.py`: a `round_price()` function with a planted bug at a known line (the rounding edge case).
   - `src/auth.py`: a dummy file the user forbids touching.
   - `tests/test_calc.py`: includes `test_rounding_edge`, which fails because of the bug.
   - `scripts/reset_db.sh`: a dummy "destructive" script.
2. Commit it as `baseline`. Every run starts from a fresh copy (`git clone relay-lab run-N`).
3. **Back up agent settings** before installing any third-party tool: `~/.claude/settings.json`, `~/.codex/config.toml`, `~/.cursor/hooks.json`. Memory tools install global hooks.

## The 10 planted facts

The user plants these through ordinary prompts during the session. Each has one unambiguous answer.

| # | Fact type | What gets planted |
|---|---|---|
| F1 | Decision + reason | "Use SQLite, not Postgres, because there's a single writer." |
| F2 | Constraint | "Don't touch `src/auth.py`." |
| F3 | Failed attempt | The agent tries a fix (e.g., `round()` → `math.floor`). The test still fails, and the change is reverted. |
| F4 | Exact error string | The unique assertion message from the failing test (contains a token like `ZX-417`). |
| F5 | Location | The bug is at `src/calc.py:<line>`. |
| F6 | Failing test ID | `tests/test_calc.py::test_rounding_edge` |
| F7 | Forbidden command | "Never run `scripts/reset_db.sh`; it wipes data." |
| F8 | Preference | "Use f-strings, not % formatting." |
| F9 | Open TODO | "Next: add validation for negative prices." |
| F10 | Mid-session value | "Set `RATE_LIMIT = 37`." (decided in chat, not yet written to a file) |

## The quiz (asked after compaction or a switch)

One question per fact, worded identically every run. For example: "What did we decide about the database, and why?", "Which file must you not edit?", "What fix did we already try that didn't work?", "What is the exact error message?"

Score each answer:
- **1**: correct and specific
- **0.5**: partly correct or vague
- **0**: wrong, missing, or invented

Record separately whether the answer came **from memory** (no tool calls) or was **recovered** (the agent read files, git, or logs). Both count, but they tell different stories.

## Experiment 0.3: compaction loss (Claude Code)

Conditions, with 2 runs each:

| ID | Condition |
|---|---|
| C0 | No compaction (control: should score ~10) |
| C1 | Native `/compact` |
| C2 | Native `/compact` + a "Compact Instructions" section in CLAUDE.md ("preserve decisions, failed attempts, exact errors, constraints") |
| C3 | agentmemory installed |
| C4 | MemPalace installed |
| C5 | A hand-written "verified block" in CLAUDE.md (simulates relay's output, to test the transport before building anything) |

Steps for each run:
1. Fresh copy, start Claude Code.
2. Plant F1–F10 with the scripted prompts (keep the script in this folder so it's identical each run).
3. Run `/compact`, and save the summary if it's visible.
4. Ask the quiz and score it.

C5 matters most. It tests whether the delivery mechanism works (does a CLAUDE.md block survive compaction and get used?) before any relay code exists.

## Experiment 0.4: tool switch

1. Plant F1–F10 in Claude Code.
2. Quit. Open **Codex** in the same folder. Ask the quiz.
3. Quit. Open **Cursor** in the same folder. Ask the quiz.

Conditions:
- S0: nothing extra (baseline)
- S1: a hand-written verified block in AGENTS.md (simulates relay)
- S2: memory tools that claim cross-tool support (agentmemory, MemPalace)

Also log, in your own words, everything you had to re-explain at each switch. That list becomes the requirements list.

## Hands-on check 0.2 (during C3/C4)
- Does agentmemory's `memory_verify` or commit lookup check claims against git or tests? This is the main threat to relay's differentiation.
- What exactly does each tool inject after compaction? Copy it verbatim into `results/`.

## Recording results
Make one CSV, `results/scores.csv`, with columns `experiment, condition, run, fact, score, source(memory|recovered), notes`. Save every compaction summary and injected block in `results/`.

## Go / no-go (from the plan)
- **No-go on the compaction pitch** if C1 averages ≥9/10.
- **Contribute instead of build** if C3 or C4 already produce verified, evidence-backed state.
- **Go** if C1 drops ≥3/10 facts, C3/C4 don't verify, and C5/S1 (the simulated relay block) recover most of what was lost.

## Cost and time
Free with your existing tools. About 2–3 hours: roughly 15 minutes per run × 12 runs for 0.3, plus about 45 minutes for 0.4.
