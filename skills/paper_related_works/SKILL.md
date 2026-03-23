---
name: paper_related_works
description: Given a paper, find its related works (cited references and successor/citing papers) and produce a structured map.
---

# paper_related_works

Given an academic paper, build a comprehensive related-works map covering both **predecessors** (papers it cites) and **successors** (papers that cite it or build on it).

## When to Use

- User provides a paper (arXiv link, PDF, paper ID, or title)
- User wants to understand what a paper builds on
- User wants to find follow-up work or improvements
- User wants to trace a line of research

## Workflow

### Step 1: Identify the Paper

Parse the paper from user input (arXiv URL, ID, title, PDF path).

**Use AlphaXiv skill to read the paper (always try this first):**

1. Extract paper ID from input (see AlphaXiv skill for ID parsing rules)
2. Fetch machine-readable report:
   ```
   WebFetch: https://alphaxiv.org/overview/{PAPER_ID}.md
   ```
3. If report lacks detail on references, fetch full text:
   ```
   WebFetch: https://alphaxiv.org/abs/{PAPER_ID}.md
   ```
4. If both 404, fall back to reading the PDF directly

Extract the full paper content for the walkthrough and related works analysis.

### Step 2: Paper Walkthrough

Write a structured walkthrough of the paper. This goes at the top of the final report.

#### 2a. Background & Problem

- What problem does the paper address?
- Why is it important? (real-world motivation, limitations of prior work)
- What gap in existing methods does it target?

#### 2b. Motivation & Key Insight

- What is the core insight or observation that drives the approach?
- What makes this paper's angle different from prior attempts?
- Any motivating examples or failure cases of existing methods?

#### 2c. Method

- High-level approach (1-2 paragraphs, not full math)
- Architecture diagram or pipeline description
- Key design choices and why they matter
- Core algorithm steps (numbered list or pseudocode if helpful)
- Important hyperparameters or training details

#### 2d. Results Overview

- Main benchmarks and datasets used
- Key quantitative results (table format):

```markdown
| Method | Benchmark | Metric | Value |
|--------|-----------|--------|-------|
| This paper | ... | ... | ... |
| Best baseline | ... | ... | ... |
```

- Most important ablation findings
- Qualitative results or visualizations (describe key figures)

#### 2e. Limitations & Future Work

- Limitations acknowledged by the authors
- Limitations you observe (not mentioned in paper)
- Future directions proposed by the authors
- Open questions that remain

### Step 3: Extract Cited Works (Predecessors)

From the paper's references and related work section, identify papers grouped by role:

| Role | Description | Example |
|------|-------------|---------|
| **Foundation** | Core method this paper builds on | "We build on DP3 [Ze et al.]" |
| **Baseline** | Methods compared against in experiments | "We compare with ACT, DP..." |
| **Component** | Borrowed modules (encoder, loss, etc.) | "We use PTv3 as backbone" |
| **Concurrent** | Independent parallel work on same problem | "Concurrent to ours, X also..." |
| **Problem** | Papers defining the problem or benchmark | "On the RLBench benchmark [James et al.]" |

For each cited paper, extract:
- Title, authors, year
- arXiv ID (if identifiable)
- Role (from table above)
- One-line description of relationship

### Step 4: Find Successor Works

Search for papers that cite or build on the target paper using multiple sources:

**4a. Semantic Scholar API (primary)**

```bash
# Get paper details + citations
curl -s "https://api.semanticscholar.org/graph/v1/paper/ArXiv:{PAPER_ID}?fields=title,year,citationCount,citations.title,citations.year,citations.authors,citations.externalIds,citations.citationCount"
```

```bash
# If not found by arXiv ID, search by title
curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=<URL_ENCODED_TITLE>&limit=5&fields=title,year,externalIds,citations.title,citations.year,citations.authors,citations.externalIds,citations.citationCount"
```

**4b. Web search (supplementary)**

```
WebSearch: "<paper_title>" improvements OR "builds on" OR "extends" site:arxiv.org
WebSearch: "<paper_title>" cite OR citing 2024 2025 2026
```

**4c. AlphaXiv (if available)**

Check the AlphaXiv overview for mentions of follow-up or concurrent work.

**4d. Connected Papers / Papers With Code**

```
WebSearch: "<paper_title>" site:paperswithcode.com
WebSearch: "<paper_title>" site:connectedpapers.com
```

### Step 5: Classify & Rank Successors

For each successor found, classify:

| Relationship | Description |
|-------------|-------------|
| **Direct extension** | Explicitly builds on this paper's method |
| **Application** | Applies the method to a new domain/task |
| **Improvement** | Proposes fixes or enhancements |
| **Comparison** | Uses as baseline in experiments |
| **Integration** | Combines with other methods |

Rank by relevance: direct extensions > improvements > applications > comparisons.

### Step 6: Produce the Report

**ASK USER** before generating: "I found N predecessors and M successors. Want me to:
1. Full map (all papers, grouped and annotated)
2. Key papers only (most influential predecessors + direct successors)
3. Focus on a specific branch (e.g., only RL-based successors)?"

Output format:

```markdown
# Paper Walkthrough & Related Works: <Paper Title>

**Paper:** <title> (<authors>, <year>)
**arXiv:** <link>
**Core contribution:** <1 sentence>

---

## 1. Paper Walkthrough

### Background & Problem
<What problem, why it matters, what gap exists>

### Motivation & Key Insight
<Core insight, what's different from prior work>

### Method
<High-level approach, architecture, key design choices>

### Results
| Method | Benchmark | Metric | Value |
|--------|-----------|--------|-------|
| This paper | ... | ... | ... |
| Best baseline | ... | ... | ... |

<Key ablation findings, qualitative highlights>

### Limitations & Future Work
- <Author-stated limitations>
- <Observed limitations>
- <Proposed future directions>

---

## 2. Predecessors (Papers This Work Builds On)

### Foundations
| Paper | Year | Relationship | Code |
|-------|------|-------------|------|
| [Title](https://arxiv.org/abs/...) | ... | ... | [repo](url) |

### Baselines
| Paper | Year | Relationship | Code |
|-------|------|-------------|------|

### Components
| Paper | Year | Relationship | Code |
|-------|------|-------------|------|

### Concurrent Work
| Paper | Year | Relationship | Code |
|-------|------|-------------|------|

## 3. Successors (Papers That Build on This Work)

### Direct Extensions
| Paper | Year | What They Add | Citations | Code |
|-------|------|--------------|-----------|------|
| [Title](https://arxiv.org/abs/...) | ... | ... | ... | [repo](url) |

### Improvements
| Paper | Year | What They Fix/Improve | Citations | Code |
|-------|------|----------------------|-----------|------|

### Applications
| Paper | Year | Domain/Task | Citations | Code |
|-------|------|------------|-----------|------|

## 4. Research Lineage

<ASCII diagram showing the main line of research>

<target_paper>
├── built on: <foundation_1> → <foundation_2> → ...
├── extended by: <successor_1>, <successor_2>
└── applied to: <application_1>

## 5. Suggested Reading Order

1. <paper> — <why read this first>
2. <paper> — <builds on #1>
...
```

### Step 7: Save Report

**Always save the report to a file.** Ask user for preferred location, default:

```bash
mkdir -p doc/related_works
```

Save as `doc/related_works/<paper_short_name>_related.md`.

**Every paper entry MUST include a clickable link.** Use this format for all tables:

```markdown
| [Paper Title](https://arxiv.org/abs/XXXX.XXXXX) | 2025 | Relationship | `XXXX.XXXXX` |
```

If no arXiv ID, use Semantic Scholar link: `https://www.semanticscholar.org/paper/<S2_ID>`

For papers with code, add repo link:

```markdown
| [Paper Title](https://arxiv.org/abs/XXXX.XXXXX) | 2025 | Description | [code](https://github.com/...) |
```

### Step 8: Offer Next Steps

After presenting the map, ask:

- "Want me to deep-dive into any of these papers? (I can create a skill with `/create_skill_with_paper`)"
- "Want me to survey the broader topic? (I can run `/topic_survey`)"
- "Want me to find the code repos for any of these?"

## Tips

- Semantic Scholar API has rate limits (~100 req/5min for unauthenticated). Space requests if doing bulk lookups.
- Papers <6 months old may have few/no citations yet. Rely more on web search for recent successors.
- Some papers cite predecessors only in supplementary material — check appendices.
- For very popular papers (>500 citations), filter successors by citation count or recency to keep the map manageable.

## Error Handling

| Issue | Recovery |
|-------|----------|
| AlphaXiv 404 | Fall back to reading PDF directly |
| Semantic Scholar rate limit | Wait 60s and retry, or switch to web search |
| Paper not on arXiv | Search by title on Semantic Scholar, Google Scholar |
| Too many successors | Filter: citations > 10, or last 2 years only |
| No successors found | Paper may be very recent; note this and rely on web search |
