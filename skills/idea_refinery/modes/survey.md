# Mode: Survey

Build or extend the literature knowledge base around the current idea version.

## Trigger

User says: "survey literature on X", "find papers about X", "what's the related work for X".

## Composability

- **Standalone**: user explicitly requests a survey
- **Called by**: evaluate (when knowledge gaps found), propose (when new direction needs context), auto (as sub-step)

## Procedure

### 1. Determine Scope

Read the current idea version and config.md to understand focus:

```bash
python3 scripts/status.py --tree-only   # see where we are
python3 scripts/refs.py stats            # what's already known
```

Scope the survey:
- **If called standalone**: broad survey around the idea's domain
- **If called by evaluate/propose**: targeted search on specific gaps or directions
- **If first survey (seed)**: cover core topic + adjacent areas, last 2-3 years

### 2. Discover Papers

Use all available discovery methods:

**All Semantic Scholar calls must include** `-H "x-api-key: $S2_API_KEY"`. If not set, warn user.

| Method | When to Use | How |
|--------|------------|-----|
| Semantic Scholar API | Keyword search, citation graph | `curl -s -H "x-api-key: $S2_API_KEY" "https://api.semanticscholar.org/graph/v1/paper/search?query=<KEYWORDS>&limit=20&fields=title,year,authors,citationCount,externalIds,abstract&sort=citationCount:desc"` |
| Semantic Scholar (recent) | Find cutting-edge work | Same but add `&year=2024-2026` |
| Semantic Scholar (citations) | Find successors of a paper | `curl -s -H "x-api-key: $S2_API_KEY" ".../paper/ArXiv:{ID}?fields=citations.title,citations.year,citations.authors,citations.externalIds,citations.citationCount"` |
| Semantic Scholar (references) | Find predecessors | Same URL but `fields=references.title,...` |
| Web search | Broad sweep, surveys | `WebSearch: "<topic>" site:arxiv.org` |
| Papers With Code | Find benchmarks, code | `WebSearch: "<topic>" site:paperswithcode.com` |
| Citation chain | Trace research lineage | Follow references + citing papers (see `/paper_related_works`) |

**Fastest bootstrap strategy — do this FIRST before broad keyword searches:**

1. **Anchor paper**: Find the most relevant *recent* paper (last 1-2 years, high citations) on the topic. Read its **Related Work** section and **Experiment baselines** table via AlphaXiv. These give you:
   - The landscape of prior approaches (from Related Work)
   - The strongest competing methods with concrete numbers (from baselines)
   - Key citations to follow for both foundational and state-of-the-art work

2. **Survey/review papers**: Search for surveys (`WebSearch: "<topic> survey" site:arxiv.org`). Read the **taxonomy/categorization** sections and **comparison tables** — a single survey paper provides a curated map of the entire field.

After reading these sections, extract cited paper IDs and add them to refs.db. Then selectively read the most relevant cited papers. One well-chosen anchor paper or survey covers more ground than dozens of API queries.

### 3. Read Papers

**Always try AlphaXiv first** for any arXiv paper:

```
WebFetch: https://alphaxiv.org/overview/{PAPER_ID}.md    # structured overview (fast)
WebFetch: https://alphaxiv.org/abs/{PAPER_ID}.md         # full text (if overview lacks detail)
```

If AlphaXiv returns 404, fall back to reading the PDF directly.

**For key papers** (foundations, main competitors): use `/paper_related_works` logic to map predecessors and successors.

### 4. Adaptive Search Depth

| Situation | Search Depth |
|-----------|-------------|
| Direction well-covered by refs.db | Minimal -- 1-2 new papers, reuse cached |
| Introduces new technique/domain | Moderate -- 3-5 new papers |
| Pivots to unfamiliar subfield | Deep -- run a mini `/topic_survey` |
| Finds paper citing unknown work | Follow the chain -- read references and successors |
| Suspects direction already done | Aggressive novelty search -- look for exact prior work |
| Feasibility unclear | Clone repos to check training configs and resource needs |

**Stop searching** when enough evidence exists for a confident judgment or the direction is clearly a dead end.

### 5. Store All Papers in refs.db

```bash
python3 scripts/refs.py add \
  --title "Paper Title" \
  --authors "Author et al." \
  --year 2025 --arxiv "2401.12345" --venue "IROS" \
  --direction <current_direction> --relevance high --read \
  --notes "Key insight: ..." \
  --relationship "Foundation method we build on"

# After reading, update with details
python3 scripts/refs.py update <paper_id> \
  --append-notes "Training: 4x A100 24h." \
  --resource-details "4x A100, 24h, RLBench dataset"

# Link to current idea version
python3 scripts/refs.py link <version> <paper_id> <role> --note "..."
```

### 6. Code Repo Inspection (when needed)

For core papers where implementation details matter:

```bash
git clone <repo_url> /tmp/idea_refinery_<method>
cd /tmp/idea_refinery_<method>
grep -r "batch_size\|num_gpu\|world_size" configs/ scripts/ --include="*.py" --include="*.yaml"
cat README.md | grep -iA5 "training\|hardware\|gpu\|resource"
rm -rf /tmp/idea_refinery_<method>
```

### 7. Write Survey Document

Write a user-readable survey to `doc/surveys/<topic_slug>.md`. Each survey is named by topic — multiple surveys can coexist (e.g., `sim2real_transfer.md`, `3d_representations.md`).

```markdown
# Survey: <Topic>

> **Date:** <date>
> **Scope:** <what was searched, how deep>
> **Papers found:** N total, M highly relevant, K read
> **Related idea version:** <current version>

## Overview

<2-3 paragraphs: what this research area is about, why it matters to our idea, key trends>

## Key Papers

| # | Paper | Year | Venue | Key Contribution | Relevance to Us |
|---|-------|------|-------|-----------------|----------------|
| 1 | [Title](link) | 2025 | ... | ... | ... |
| 2 | ... | ... | ... | ... | ... |

## Landscape

### <Sub-topic A>
<1-2 paragraphs: what this line of work does, main papers, state of the art>

### <Sub-topic B>
...

## Gaps & Opportunities

- <gap 1>: <what's missing in existing work, how our idea could fill it>
- <gap 2>: ...

## Implications for Our Idea

- **Supports:** <what evidence strengthens our approach>
- **Challenges:** <what evidence raises concerns>
- **New directions:** <ideas sparked by the survey>

## Open Questions

- <question that needs deeper investigation>

---
*Paper metadata powered by [Semantic Scholar](https://www.semanticscholar.org/)*
```

If a survey on the same topic already exists, **overwrite it** (git tracks history).

### 8. Commit & Report

```bash
git add refs.db doc/agent/ doc/surveys/ && git commit -m "survey: <topic> — N papers, M highly relevant"
```

Present a summary to the user:
- Papers found (total, highly relevant, read)
- Key findings that affect the idea
- "Full survey in `doc/surveys/<topic_slug>.md`"
- Knowledge gaps remaining
- Suggested next mode: evaluate, propose, or more survey

### 9. Follow-up Questions (Subagent)

When the user asks questions about the survey or literature (e.g., "how does paper X compare to Y?", "explain the method in Z", "what's the difference between A and B?"), **use a subagent** to answer:

```
Agent(
  description="Answer literature question",
  prompt="Read doc/surveys/<topic>.md and refs.db. Question: <user question>.
          Use refs.py search, AlphaXiv, and Semantic Scholar to find the answer.
          Return a concise answer with paper citations."
)
```

**Why subagent:** Literature Q&A can consume significant context (reading papers, fetching content). Running it in a subagent preserves the main agent's context for the ongoing refinement workflow.

**When to use subagent vs. answering directly:**
- **Subagent**: needs to read/fetch papers, compare methods in detail, look up specific claims
- **Direct**: simple factual question answerable from refs.db or the survey document already in context
