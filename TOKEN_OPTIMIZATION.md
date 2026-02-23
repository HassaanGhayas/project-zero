# Token Optimization Strategy

## Problem
Large documentation files consume unnecessary tokens in every conversation.
- `doc.md`: 1200 lines (excessive)
- Multiple redundant spec files
- Verbose examples and explanations

## Solution: Three-Tier Documentation

### Tier 1: Quick Reference (Minimal Tokens)
- **README_QUICKSTART.md** (~50 lines) - Entry point
- **Token cost**: ~200 tokens
- **Use**: First thing new users read

### Tier 2: Essential Architecture (Lean)
- **doc_condensed.md** (~300 lines) - Condensed version
- **Token cost**: ~1,200 tokens
- **Use**: Understanding architecture without verbose examples

### Tier 3: Complete Reference (Archived)
- **documents/doc.md** (1200 lines - original, kept for reference)
- **Token cost**: ~5,000 tokens
- **Use**: Deep reference when needed, archived from main flow

## Token Savings Achieved

| Document | Original Lines | New Size | Reduction | Token Savings |
|----------|---|---|---|---|
| README → README_QUICKSTART | 198 | 80 | 60% | ~500 |
| doc.md (keep but not default) | 1200 | doc_condensed 300 | 75% | ~3,600 |
| **Total Savings Per Session** | - | - | - | **~4,100 tokens** |

## Recommendations for Future Optimization

### What To Keep
✅ **task.md files** - Essential for tracking work
✅ **spec.md files** - Required for feature definition
✅ **data-model.md** - Critical for schema understanding
✅ **MANUAL_E2E_TEST_GUIDE.md** - Needed for testing

### What To Condense
⚠️ **research.md** (331 lines) - Move findings to memory
⚠️ **quickstart.md** (478 lines) - Superseded by README_QUICKSTART
⚠️ **Verbose contract specs** - Extract essentials only

### What To Archive
📦 **Prompt History Records** - Move to separate `history-archive/`
📦 **Old spec versions** - Keep one canonical version
📦 **Verbose examples** - Link to separate examples/ folder

## Usage

**For Claude agents (future sessions):**
```
Load: README_QUICKSTART.md (quick refresh)
Load: CLAUDE.md (rules/commands)
Load: .specify/memory/constitution.md (non-negotiables)
Reference: doc_condensed.md (if architecture questions arise)
Skip: documents/doc.md (unless explicitly needed)
```

**For new users:**
- Start: README_QUICKSTART.md (3 min read)
- Then: MANUAL_E2E_TEST_GUIDE.md (20 min practical)
- Deep dive: doc_condensed.md (if interested)

## Memory Files (Persistent Across Sessions)

Instead of re-reading documentation, use memory files:

```markdown
# .specify/memory/silver-tier-gmail.md
## Architecture Summary
- Gmail watcher polls every 120s
- Creates action files with YAML frontmatter
- Status field editing triggers approval workflow
- MCP server executes archival via Gmail API

## Key Files
- gmail_watcher.py (detection)
- status_field_watcher.py (approval)
- approved_watcher.py (execution)
- gmail_server.py (MCP)
```

## Implementation

Already done:
✅ Created README_QUICKSTART.md
✅ Created doc_condensed.md
✅ Kept original doc.md for reference

Next steps:
⏳ Archive old prompt history (optional)
⏳ Condense quickstart.md → extracted to README_QUICKSTART
⏳ Create memory snapshots for each tier

## Result

**Per-session token savings**: ~4,100 tokens (~3-5% of typical session)
**Long-term benefit**: Faster context loading, cleaner project structure
**User experience**: Clearer entry points, less cognitive load

---

**Default Load Order:**
1. README_QUICKSTART.md (always)
2. CLAUDE.md (rules)
3. doc_condensed.md (on-demand)
4. doc.md (explicit reference only)
