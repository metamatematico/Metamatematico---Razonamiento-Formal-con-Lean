# Agents

Claude Code agent definitions for the AI Mathematician project.

## proof-engineer

Lean 4 theorem proving specialist that validates knowledge base templates through compiler-driven refinement.

### Key Features

- **4-stage proof loop**: Gather → Attempt → Verify → Refine
- **Tactic selection guide**: 15+ goal types with primary/secondary tactics
- **Error barrier analysis**: 7 error categories with resolution strategies
- **Dynamic skill loading**: Loads `lean-tp-*` and `lean-fp-*` skills based on error patterns
- **Max 3 iterations**: Reports proof barrier if unresolved

### Usage

Invoked as a Claude Code subagent to process the validation queue:

```python
# Example: Validate a knowledge base template
task = Task(
    subagent_type="proof-engineer",
    prompt="Validate and complete this theorem: ..."
)
```

### Integration with Two-Stage Pipeline

```
Knowledge Base → proof-engineer → Training Dataset
(templates)      (validation)     (verified proofs)
```

The agent continuously asks: *"Is this a legal method of procedure?"*

## Installation

To use with Claude Code, copy to your global config:

```bash
cp agents/proof-engineer.md ~/.claude/agents/
```

## Sync Workflow

1. Edit agent definitions in this repo
2. Submit PR for review
3. After merge, copy to `~/.claude/agents/`

## Workflows

See [`WORKFLOWS.md`](./WORKFLOWS.md) for the vision of the complete mathematical research system:
- 5 operational workflows
- 3 core agents (1 implemented, 2 planned)
- Integration patterns

**Currently Available**: Basic theorem proving via `proof-engineer`

## Related

- [`skills/`](./skills/) - Lean skills loaded by this agent
- [`WORKFLOWS.md`](./WORKFLOWS.md) - Vision for multi-agent research system
- [`dataset/dataset_schema.md`](../dataset/dataset_schema.md) - Schema for validation records
- [`knowledgebase/`](../knowledgebase/) - Source templates to validate
