"""The normalized session model.

Every reader (Claude Code, Codex, Cursor) produces one `Session` made of these
records. Everything downstream works on this model only, so a new agent means
a new reader and nothing else.

Each record carries `source`, an opaque pointer back to the log line it came
from (e.g. "claude_code:<session_id>:<uuid>"). The rendered handoff keeps these
pointers so a reader can check any statement against the original evidence.
"""

from dataclasses import dataclass, field


@dataclass
class Prompt:
    """Something the human typed. Quoted verbatim later as the record of intent."""

    ts: str
    text: str
    turn: int
    source: str


@dataclass
class Edit:
    """One change to one file, as the agent's tool saw it."""

    ts: str
    path: str
    kind: str  # "edit" (old->new), "write" (whole file), "patch" (unified diff)
    old: str
    new: str
    turn: int
    source: str


@dataclass
class Command:
    """A shell command the agent ran, with whatever output we could recover."""

    ts: str
    command: str
    output: str
    turn: int
    source: str
    exit_code: int | None = None


@dataclass
class Claim:
    """A sentence the agent wrote to the human that asserts a fact about the work.

    Claims are what we verify. They are never copied into the handoff as truth.
    """

    ts: str
    text: str
    turn: int
    source: str


@dataclass
class Session:
    tool: str  # "claude_code" | "codex" | "cursor"
    session_id: str
    cwd: str
    branch: str | None
    started: str | None
    ended: str | None
    prompts: list[Prompt] = field(default_factory=list)
    edits: list[Edit] = field(default_factory=list)
    commands: list[Command] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    skipped_records: int = 0  # lines we could not interpret; reported, never hidden

    @property
    def touched_paths(self) -> list[str]:
        seen: dict[str, None] = {}
        for edit in self.edits:
            seen.setdefault(edit.path, None)
        return list(seen)
