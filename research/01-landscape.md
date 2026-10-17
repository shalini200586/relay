# Phase 0.1 — Landscape survey

Date: 2026-10-17. Scope: tools that help AI coding agents keep or hand over state across compaction and across tools (Claude Code, Codex, Cursor).

Evidence levels used below:
- **tested**: checked on this machine
- **docs**: official docs or the tool's own README
- **claimed**: third-party write-ups, unverified

Star counts are what the GitHub page showed on the date above.

## 1. How native compaction works

### Claude Code (docs)
- When context fills, Claude Code "clears older tool outputs first, then summarizes the conversation if needed. Your requests and key code snippets are preserved; detailed instructions from early in the conversation may be lost." ([How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works))
- You can steer it with a "Compact Instructions" section in CLAUDE.md, or with `/compact <focus>`.
- CLAUDE.md and auto memory (first 200 lines or 25KB of MEMORY.md) load into the context window. Third-party testing found the root CLAUDE.md came back after 8 of 8 compactions (claimed: [dev.to](https://dev.to/rulestack/2-of-8-claude-code-compactions-dropped-the-skill-body-the-docs-say-is-re-injected-both-through-57lf)).
- **The full transcript stays on disk.** "Each message, tool use, and result is written to a plaintext JSONL file under `~/.claude/projects/`" (docs). Compaction shrinks the context window, not the file.
- Hooks include `PreCompact`, `PostCompact`, and `SessionStart` with `source=compact`. Context is injected via `additionalContext`. Values over 10,000 characters are moved to a file, and Claude sees only a 2,000-character preview (docs: [hooks](https://code.claude.com/docs/en/hooks)).

### Codex CLI (docs + claimed)
- `/compact` "replaces earlier turns with a concise summary" (docs; mechanics not specified).
- Every account agrees that assistant replies and tool outputs are dropped. User messages are kept up to a budget that sources disagree on (20k vs 64k tokens). For OpenAI-hosted models the summary is an encrypted server-side blob (claimed: [gist](https://gist.github.com/osolmaz/a38acf6e522df67530e3ed47c80fdcd5), [deep dive](https://codex.danielvaughan.com/2026/04/14/context-compaction-deep-dive-codex-cli-claude-code-opencode/)).
- Sessions are kept on disk at `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl` (tested).

### Cursor (claimed; status unresolved)
- Sources conflict on whether "Memories" still exists. Some say it became GA in 1.2, others say it was removed in 2.1 ([past.dev](https://www.past.dev/blog/cursor-memory), [memorylake](https://www.memorylake.ai/en/blogs/cursor-forgets-previous-sessions)).
- Rules in `.cursor/rules/*.mdc` are the stable mechanism.
- Agent transcripts are stored at `~/.cursor/projects/<proj>/agent-transcripts/**/*.jsonl` (tested).

### The key finding
Both Claude Code and Codex drop **tool outputs first**. Tool outputs hold the evidence: test results, error messages, and command exit codes. That evidence is still in the JSONL on disk. Community reports list what compaction loses: "Error messages with stack traces get reduced to 'there was an error'", "File paths and line numbers disappear", "Multi-step debugging chains lose the intermediate steps", and "Architectural decisions lose their rationale" (claimed: [claude-brain write-up](https://dev.to/mikeadolan/claude-code-compaction-kept-destroying-my-work-i-built-hooks-that-fixed-it-2dgp)).

## 2. Cross-tool transport that already exists
- **AGENTS.md** (docs, [agents.md](https://agents.md/)):
  - It is read by more than 20 tools, including Codex, Cursor, Gemini CLI, Copilot, Aider, Zed, Windsurf, Devin, Jules, and Amp. Claude Code can read it in place of CLAUDE.md.
  - The site says it is used in "60k+" open-source projects.
  - It has no required sections and is maintained by hand. Nothing in the spec covers session state.
- So a block that relay manages inside AGENTS.md and CLAUDE.md would reach almost every tool, and it would survive Claude Code compaction because CLAUDE.md is reloaded. **Version 1 might not need hooks at all.** Experiment 0.3 has to confirm that.

## 3. Comparison matrix

Columns: **Capture** = how data gets in. **LLM** = whether an LLM is needed. **Compaction** = whether the tool handles compaction specifically. **X-tool** = Codex/Cursor support. **Verifies** = checks claims against git or tests. **Attempts** = reconstructs failed attempts.

| Tool | Category | Capture | LLM | Compaction | X-tool | Verifies | Attempts | License / size | Level |
|---|---|---|---|---|---|---|---|---|---|
| claude-mem | memory | hooks (SessionStart, prompts, Pre/PostToolUse, Stop, SessionEnd) | **yes**: hosted observer (30-day trial), or your own OpenRouter/Gemini/Anthropic key | not mentioned | Codex (via T3 Code), others; Cursor unclear | no | no | Apache-2.0, ~101k stars | docs |
| MemPalace | memory | hooks + mines `~/.claude/projects` | no (optional rerank) | saves before compaction | Claude, Codex, Cursor | no | no | MIT, ~60k | docs |
| agentmemory | memory | 12 Claude / 6 Codex / 7 Cursor hooks + JSONL import | optional | PreCompact re-injects (2k-token budget) | ~20 agents | no (has provenance `memory_verify`, commit lookup) | captures tool errors only | Apache-2.0, ~30k | docs |
| ai-memory | memory + handoff | hooks; server | optional (zero by default) | not specific | 20+ harnesses | no | "what failed" in brief, method unstated | MIT | docs |
| claude-brain | compaction | PreCompact saves full transcript to SQLite; PostCompact re-injects | not stated | **yes** | Claude only | no | no | MIT, 35 stars | docs |
| Entire CLI | session capture | hooks; checkpoints as git refs | optional summaries | no | 8 agents | no | no | MIT (+ commercial control plane) | docs |
| agit | session capture | log parsing; hash-chained JSONL | no | no | 13 adapters | partial (3-way merge, commit link) | no | Apache-2.0, ~7 stars | docs |
| agentgrep | search | log parsing | ? | no | 10 agents | no | no | pre-alpha | docs |
| godic97/claim-check | claim check | Claude Code Stop hook reads transcript | no (regex) | no | Claude only | **yes**: test/build/lint claims vs Bash exit codes, stale if code changed after the run | no | MIT, 0 stars, 1 commit | docs |
| bugyal/claimcheck | claim check | diff + report + test log (CLI/Action) | not stated (zero deps) | no | agent-agnostic | **yes**: verified/unsupported/refuted/uncheckable; flags removed assertions | flags pass/fail flapping | Apache-2.0, 0 stars, 5 commits | docs |
| dannwaneri/claimcheck | claim check | platform on Cloudflare | yes (must quote the diff) | no | — | yes (claimed files vs diff) | no | — | claimed |
| Selvedge | attempts | **agent writes** via MCP/CLI | no (optional embeddings) | no | many via MCP | no | records only what is written; "does not reconstruct unrecorded reasoning" | repo linked, license unstated | docs |
| Beads | tasks | agent writes (`bd`) | not mentioned | "memory decay" of closed tasks | Claude, Codex, Cursor… | no | no | MIT, ~28k | docs |
| Spec Kit | specs | slash commands | via your agent | no | many | partial (`/speckit-converge`, bug verdicts) | no | MIT, ~142k | docs |
| Graphify | code structure | tree-sitter parse; rebuild on commit | code: no; docs/media: optional | no | 17+ assistants | no | no | Apache-2.0/MIT | docs |
| Serena | code structure | LSP over MCP | no | no | MCP clients | no | no | GPL-3.0 (+MIT part), ~30k | docs |
| Agent Trace | attribution spec | format only | — | — | spec | no | no | CC BY 4.0, RFC v0.1 | claimed |
| git-ai | attribution | agent self-reports `git ai checkpoint` | no | no | many | no | no | — | docs |
| AGENTS.md | instructions | manual file | — | reloaded (Claude) | 20+ tools | no | no | open format | docs |

## 4. Gaps (what nobody I found does)
1. **Memory is crowded. Verification is not.** Projects with 30k to 100k stars remember and retrieve. None of them checks whether what they remember is true against git or tests. Their published benchmarks measure retrieval recall (for example, agentmemory reports 95.2% R@5 on LongMemEval-S), not whether a handoff is accurate.
2. **The tools that do verify are tiny and narrow.** There are two zero-star projects: one checks test/build/lint claims inside Claude Code, the other checks a report against a diff in CI. Neither feeds a handoff, survives compaction, or works across tools.
3. **No tool reconstructs failed attempts from logs.** Selvedge records only what an agent chooses to write. Memory tools store raw text or LLM summaries, not structured "tried X, reverted, test still failing" chains.
4. **Compaction drops the evidence first, yet the evidence stays on disk.** A tool that reads the JSONL can recover exactly what compaction removed, without an LLM.
5. **The transport is already solved.** AGENTS.md and CLAUDE.md reach 20+ tools, and CLAUDE.md reloads after compaction. A new protocol is unnecessary.

## 5. Updated hypothesis for relay
> Memory tools remember; nothing checks. relay is a **verified-state layer**. It reads the on-disk logs, recovers the evidence compaction dropped, checks claims against git and tests, reconstructs attempts, and writes a short, evidence-backed block into AGENTS.md/CLAUDE.md that every tool already reads.

What would kill this hypothesis:
- agentmemory's `memory_verify` or commit lookup turns out to verify claims against git and tests. Needs a hands-on check in 0.2.
- Native compaction keeps test results, errors, and failed attempts. Measured in 0.3.
- The managed block doesn't reload after compaction in practice. Measured in 0.3.

## 6. Not yet checked
Mem0, Cline memory bank, Aider/Cline/Copilot log paths, the Agent Trace spec text (repo URL returned 404), MCP registry, and Show HN launch practice.

## Sources
- [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works) · [Claude Code hooks](https://code.claude.com/docs/en/hooks)
- [What survives /compact (dev.to)](https://dev.to/rulestack/2-of-8-claude-code-compactions-dropped-the-skill-body-the-docs-say-is-re-injected-both-through-57lf)
- [Codex compaction gist](https://gist.github.com/osolmaz/a38acf6e522df67530e3ed47c80fdcd5) · [Codex compaction deep dive](https://codex.danielvaughan.com/2026/04/14/context-compaction-deep-dive-codex-cli-claude-code-opencode/)
- [Cursor memory (past.dev)](https://www.past.dev/blog/cursor-memory) · [Cursor forgets sessions (memorylake)](https://www.memorylake.ai/en/blogs/cursor-forgets-previous-sessions)
- [agents.md](https://agents.md/)
- [claude-mem](https://github.com/thedotmack/claude-mem) · [MemPalace](https://github.com/MemPalace/mempalace) · [agentmemory](https://github.com/rohitg00/agentmemory) · [ai-memory](https://github.com/akitaonrails/ai-memory) · [claude-brain](https://github.com/mikeadolan/claude-brain) · [claude-brain write-up](https://dev.to/mikeadolan/claude-code-compaction-kept-destroying-my-work-i-built-hooks-that-fixed-it-2dgp)
- [Entire CLI](https://github.com/entireio/cli) · [agit](https://github.com/agitHQ/agit) · [agentgrep](https://agentgrep.org/backends/cursor-ide/)
- [godic97/claim-check](https://github.com/godic97/claim-check) · [bugyal/claimcheck](https://github.com/bugyal/claimcheck) · [dannwaneri claimcheck write-up](https://dev.to/dannwaneri/i-built-a-lie-detector-for-ai-coding-agents-then-i-read-the-rules-1hhb)
- [Selvedge prior attempts](https://selvedge.sh/prior-attempts/) · [Beads](https://github.com/steveyegge/beads) · [Spec Kit](https://github.com/github/spec-kit)
- [Graphify](https://github.com/safishamsi/graphify) · [Serena](https://github.com/oraios/serena) · [git-ai](https://github.com/git-ai-project/git-ai)
- [GitHub community discussion](https://github.com/orgs/community/discussions/208251)
