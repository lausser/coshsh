# .agents

Agent-facing project knowledge, kept vendor-neutral and under version control.

Nothing in here is specific to one AI coding tool. Tool-specific directories
(`.claude/`, `.cursor/`, `.aider*`, ...) stay untracked and personal; each
developer links from their tool's expected location into this directory, so the
*content* is shared and reviewed while the *wiring* stays local.

## Layout

```
.agents/
└── skills/
    └── coshsh-classes/     # how to write coshsh datasources, classes,
        ├── SKILL.md        # details, datarecipients, templates, cookbooks
        ├── references/     # deep-dive docs loaded on demand
        └── assets/         # copy-paste skeletons
```

## Wiring it up

Claude Code discovers skills under `.claude/skills/`:

```sh
mkdir -p .claude/skills
ln -s ../../.agents/skills/coshsh-classes .claude/skills/coshsh-classes
```

The symlink is deliberately **not** committed — `.claude/` is personal. Only the
target under `.agents/` is versioned.

## Editing

Edit the files under `.agents/` directly (following the symlink is the same
thing). Changes belong in the same commit as the code they describe: a skill
that documents behaviour the code no longer has is worse than no skill at all.

## Related

- `docs/ai_handover.md` — architecture and control-flow reference for the whole
  codebase. Deeper and broader than the skill; the skill is the practical
  "how do I write X" companion.
- `CLAUDE.md` — working agreements for agents in this repo.
