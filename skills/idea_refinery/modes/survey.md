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

### 7. Commit & Report

```bash
git add refs.db doc/agent/ && git commit -m "survey: found N papers on <topic>, M highly relevant"
```

Present a summary to the user:
- Papers found (total, highly relevant, read)
- Key findings that affect the idea
- Knowledge gaps remaining
- Suggested next mode: evaluate, propose, or more survey
