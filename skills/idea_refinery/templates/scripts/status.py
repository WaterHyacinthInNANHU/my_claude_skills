#!/usr/bin/env python3
"""Compact status generator for idea refinery workspaces.

Usage:
    status.py              # full status
    status.py --tree-only  # just the idea tree
    status.py --json       # machine-readable output for auto mode
"""

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path


def run(cmd, cwd=None):
    """Run a shell command, return stdout or empty string on failure."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=10)
        return r.stdout.strip()
    except Exception:
        return ""


def get_tag(cwd):
    """Extract tag from current branch name."""
    branch = run("git branch --show-current", cwd=cwd)
    if branch.startswith("ideate/"):
        parts = branch.split("/")
        return parts[1] if len(parts) >= 2 else ""
    return ""


def get_current_branch(cwd):
    return run("git branch --show-current", cwd=cwd)


def get_idea_branches(cwd, tag):
    """Get all ideate branches and their relationships."""
    raw = run("git branch", cwd=cwd)
    branches = []
    for line in raw.splitlines():
        name = line.strip().lstrip("* ")
        if name.startswith(f"ideate/{tag}"):
            suffix = name[len(f"ideate/{tag}"):]
            branches.append({"branch": name, "suffix": suffix})
    return branches


def parse_idea_card(card_path):
    """Parse an idea card file for scores and metadata."""
    result = {"scores": {}, "description": "", "strengths": [], "weaknesses": [],
              "next_suggestions": [], "title": ""}
    dim_names = ["novelty", "theory", "contribution", "feasibility", "risk"]
    try:
        text = Path(card_path).read_text()

        # Parse scores
        for dim in dim_names:
            pattern = rf"\|\s*{dim}\s*\|[^|]*?(\d)/5"
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                result["scores"][dim[0].upper()] = int(m.group(1))
            else:
                pattern2 = rf"\|\s*{dim}\s*\|\s*([\u2B24\u25CB]+)"
                m2 = re.search(pattern2, text, re.IGNORECASE)
                if m2:
                    result["scores"][dim[0].upper()] = m2.group(1).count("\u2B24")

        # Parse description (## Idea section)
        m = re.search(r"## Idea\s*\n\s*(.+?)(?=\n##|\Z)", text, re.DOTALL)
        if m:
            result["description"] = m.group(1).strip()

        # Parse what changed
        m = re.search(r"## What Changed.*?\n\s*(.+?)(?=\n##|\Z)", text, re.DOTALL)
        if m:
            result["delta"] = m.group(1).strip()

        # Parse bullet list sections (- item)
        def parse_bullet_section(heading):
            m = re.search(rf"## {heading}\s*\n((?:\s*-\s*.+\n?)*)", text)
            if m:
                items = []
                for line in m.group(1).strip().splitlines():
                    item = line.strip().lstrip("- ").strip()
                    # Skip empty items, headings, and template placeholders
                    if item and not item.startswith("#") and not item.startswith("##"):
                        items.append(item)
                return items
            return []

        result["strengths"] = parse_bullet_section("Strengths")
        result["weaknesses"] = parse_bullet_section("Weaknesses")

        # Parse numbered list section (1. item)
        m = re.search(r"## Next Refinement Suggestions\s*\n((?:\s*\d+\..+\n?)*)", text)
        if m:
            items = []
            for line in m.group(1).strip().splitlines():
                item = line.strip().lstrip("0123456789. ").strip()
                if item:
                    items.append(item)
            result["next_suggestions"] = items

        # Title from first line
        first_line = text.splitlines()[0] if text.splitlines() else ""
        m = re.match(r"#\s*Idea Card:\s*(.*)", first_line)
        if m:
            result["title"] = m.group(1).strip()

    except Exception:
        pass
    return result


def format_scores(scores):
    """Format scores as compact string like 'N:4 T:3 C:4 F:5 R:3'."""
    if not scores:
        return "unscored"
    parts = []
    for key in ["N", "T", "C", "F", "R"]:
        if key in scores:
            parts.append(f"{key}:{scores[key]}")
    avg = sum(scores.values()) / len(scores) if scores else 0
    return " ".join(parts) + f" avg={avg:.1f}"


def get_config_summary(cwd):
    """Parse config.md for a compact summary."""
    config_path = os.path.join(cwd, "config.md")
    if not os.path.exists(config_path):
        return "no config.md"
    try:
        text = Path(config_path).read_text()
        parts = []
        for line in text.splitlines():
            if "GPU" in line and "|" in line:
                cells = [c.strip() for c in line.split("|")]
                if len(cells) >= 3 and cells[2] and cells[2] != "Budget":
                    parts.append(cells[2])
            if "deadline" in line.lower() and "|" in line:
                cells = [c.strip() for c in line.split("|")]
                if len(cells) >= 3 and cells[2] and cells[2] != "Budget":
                    parts.append(f"deadline {cells[2]}")
        m = re.search(r"strategy\s*\|\s*(\S+)", text)
        if m:
            parts.append(m.group(1))
        m = re.search(r"beam_width\s*\|\s*(\d+)", text)
        if m:
            parts.append(f"w={m.group(1)}")
        m = re.search(r"max_depth\s*\|\s*(\d+)", text)
        if m:
            parts.append(f"d={m.group(1)}")
        m = re.search(r"convergence_threshold\s*\|\s*([\d.]+)", text)
        if m:
            parts.append(f"thresh={m.group(1)}")
        return " | ".join(parts) if parts else "defaults"
    except Exception:
        return "config error"


def get_convergence_threshold(cwd):
    """Read convergence threshold from config.md."""
    config_path = os.path.join(cwd, "config.md")
    if os.path.exists(config_path):
        try:
            text = Path(config_path).read_text()
            m = re.search(r"convergence_threshold\s*\|\s*([\d.]+)", text)
            if m:
                return float(m.group(1))
        except Exception:
            pass
    return 4.0


def get_refs_stats(cwd):
    """Get reference DB stats."""
    db_path = os.path.join(cwd, "refs.db")
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        total = cur.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        read_count = cur.execute("SELECT COUNT(*) FROM papers WHERE read=1").fetchone()[0]
        dir_counts = {}
        rows = cur.execute("SELECT direction, COUNT(*) FROM papers GROUP BY direction").fetchall()
        for d, c in rows:
            if d:
                dir_counts[d] = c
        conn.close()
        return {"total": total, "read": read_count, "by_direction": dir_counts}
    except Exception:
        return None


def get_refs_for_node(cwd, node_id):
    """Get papers linked to a specific idea version."""
    db_path = os.path.join(cwd, "refs.db")
    if not os.path.exists(db_path):
        return []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        # Papers linked via idea_paper_links
        rows = conn.execute(
            "SELECT p.title, p.year, p.arxiv_id, l.role "
            "FROM idea_paper_links l JOIN papers p ON l.paper_id = p.id "
            "WHERE l.idea_version = ? ORDER BY p.year DESC",
            (node_id,)
        ).fetchall()
        linked = [dict(r) for r in rows]
        # Also papers in this direction
        direction = node_id if node_id != "root" else "seed"
        rows2 = conn.execute(
            "SELECT title, year, arxiv_id, relationship as role "
            "FROM papers WHERE direction = ? AND relevance = 'high' "
            "ORDER BY year DESC LIMIT 5",
            (direction,)
        ).fetchall()
        dir_papers = [dict(r) for r in rows2]
        conn.close()
        # Deduplicate by title
        seen = set()
        result = []
        for p in linked + dir_papers:
            if p["title"] not in seen:
                seen.add(p["title"])
                result.append(p)
        return result
    except Exception:
        return []


def get_sketch_info(cwd):
    """Parse key fields from sketch.md."""
    sketch_path = os.path.join(cwd, "doc/agent/sketch.md")
    if not os.path.exists(sketch_path):
        return {}
    try:
        text = Path(sketch_path).read_text()
        info = {}
        for field in ["Phase", "Iteration", "Current idea version", "Last action", "Blocking issues"]:
            # Match "**Field:** value" on a single line, value stops at next "**" or newline
            pattern = rf"\*\*{re.escape(field)}:\*\*\s*([^\n*]+)"
            m = re.search(pattern, text)
            if m:
                val = m.group(1).strip()
                if val:
                    info[field.lower().replace(" ", "_")] = val
        # Get next steps
        m = re.search(r"## Next Steps\s*\n((?:\d+\..+\n?)+)", text)
        if m:
            info["next_steps"] = m.group(1).strip()
        # Get open questions (bullet items only, skip empty "-")
        m = re.search(r"## Open Questions\s*\n((?:\s*-\s*.+\n?)*)", text)
        if m:
            questions = []
            for line in m.group(1).strip().splitlines():
                q = line.strip().lstrip("- ").strip()
                if q and not q.startswith("#"):
                    questions.append(q)
            if questions:
                info["open_questions"] = questions
        return info
    except Exception:
        return {}


def find_current_card(cwd, node_id):
    """Find the idea card file that matches the current node."""
    versions_dir = os.path.join(cwd, "doc/agent/idea_versions")
    if not os.path.isdir(versions_dir):
        return None
    # Try by filename first
    for f in sorted(os.listdir(versions_dir), reverse=True):
        fpath = os.path.join(versions_dir, f)
        if node_id == "root" and "v0" in f:
            return fpath
        if node_id != "root":
            try:
                content = Path(fpath).read_text()
                if node_id.lower() in content.lower():
                    return fpath
            except Exception:
                pass
    # Return most recent card as fallback
    files = sorted(os.listdir(versions_dir), reverse=True)
    return os.path.join(versions_dir, files[0]) if files else None


def get_recent_commits(cwd, count=5):
    """Get recent commit messages on current branch."""
    raw = run(f"git log --oneline -{count} --show-notes", cwd=cwd)
    return raw.splitlines() if raw else []


def build_tree(cwd, tag):
    """Build the idea tree structure."""
    branches = get_idea_branches(cwd, tag)
    current = get_current_branch(cwd)

    nodes = []
    for b in branches:
        suffix = b["suffix"]
        if suffix == "":
            node_id = "root"
            label = "v0 seed"
        else:
            node_id = suffix.lstrip("/")
            label = node_id

        card_path = find_current_card(cwd, node_id)
        card_data = parse_idea_card(card_path) if card_path else {"scores": {}}

        is_current = b["branch"] == current
        depth = suffix.count("/") + suffix.count(".")
        nodes.append({
            "id": node_id,
            "branch": b["branch"],
            "suffix": suffix,
            "scores": card_data["scores"],
            "is_current": is_current,
            "depth": depth,
            "label": label,
            "card_path": card_path,
            "card": card_data,
        })

    return nodes


def format_tree_text(nodes, tag):
    """Format the tree as indented text."""
    if not nodes:
        return "  (no branches yet)"

    lines = []
    root = [n for n in nodes if n["id"] == "root"]
    children = sorted([n for n in nodes if n["id"] != "root"], key=lambda x: x["suffix"])

    def fmt_node(n):
        score_str = f"[{format_scores(n['scores'])}]" if n["scores"] else ""
        marker = " <- current" if n["is_current"] else ""
        return f"{n['label']} {score_str}{marker}"

    if root:
        lines.append(f"  {fmt_node(root[0])}")

    for i, n in enumerate(children):
        parts = n["id"].split(".")
        indent = "  " * (len(parts))
        connector = "\u251c\u2500" if i < len(children) - 1 else "\u2514\u2500"
        lines.append(f"  {indent}{connector} {fmt_node(n)}")

    return "\n".join(lines)


def truncate(text, max_len=100):
    """Truncate text with ellipsis."""
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def main():
    parser = argparse.ArgumentParser(description="Idea refinery status")
    parser.add_argument("--tree-only", action="store_true", help="Show only the idea tree")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--cwd", default=".", help="Workspace directory")
    args = parser.parse_args()

    cwd = os.path.abspath(args.cwd)
    tag = get_tag(cwd)
    if not tag:
        sketch = get_sketch_info(cwd)
        print("Not on an ideate/ branch. cd to a workspace and checkout an ideate branch.")
        sys.exit(1)

    current_branch = get_current_branch(cwd)
    nodes = build_tree(cwd, tag)
    config_summary = get_config_summary(cwd)
    refs = get_refs_stats(cwd)
    sketch = get_sketch_info(cwd)
    threshold = get_convergence_threshold(cwd)

    # Find current node
    current_node = next((n for n in nodes if n["is_current"]), None)
    current_id = current_node["id"] if current_node else "?"
    current_version = sketch.get("current_idea_version", "?")

    if args.json:
        data = {
            "tag": tag,
            "branch": current_branch,
            "config": config_summary,
            "threshold": threshold,
            "sketch": sketch,
            "tree": [{**n, "card_path": n.get("card_path")} for n in nodes],
            "refs": refs,
            "current_node": {
                "id": current_id,
                "card": current_node["card"] if current_node else {},
                "linked_papers": get_refs_for_node(cwd, current_id),
            },
        }
        print(json.dumps(data, indent=2, default=str))
        return

    print(f"=== IDEA REFINERY STATUS: {tag} ===")
    print(f"Config: {config_summary}")
    print(f"Current: {current_version} on branch {current_branch}")
    phase = sketch.get("phase", "?")
    iteration = sketch.get("iteration", "?")
    print(f"Phase: {phase} | Iteration: {iteration}")
    print()

    # Tree
    print("TREE:")
    print(format_tree_text(nodes, tag))
    print()

    if args.tree_only:
        return

    # --- Current Node Details ---
    if current_node:
        card = current_node.get("card", {})
        print("CURRENT NODE:")

        # Description
        desc = card.get("description", "")
        if desc:
            print(f"  Idea: {truncate(desc, 120)}")

        # Delta from parent
        delta = card.get("delta", "")
        if delta and delta != "Initial seed idea":
            print(f"  Changed: {truncate(delta, 120)}")

        # Scores
        if current_node["scores"]:
            print(f"  Scores: {format_scores(current_node['scores'])}")

        # Strengths
        strengths = card.get("strengths", [])
        if strengths:
            print(f"  Strengths: {'; '.join(truncate(s, 60) for s in strengths[:3])}")

        # Weaknesses
        weaknesses = card.get("weaknesses", [])
        if weaknesses:
            print(f"  Weaknesses: {'; '.join(truncate(s, 60) for s in weaknesses[:3])}")

        # Next refinement suggestions
        suggestions = card.get("next_suggestions", [])
        if suggestions:
            print(f"  Suggestions: {'; '.join(truncate(s, 60) for s in suggestions[:3])}")

        # Key papers linked to this node
        linked_papers = get_refs_for_node(cwd, current_id)
        if linked_papers:
            print(f"  Key papers ({len(linked_papers)}):")
            for p in linked_papers[:5]:
                role = f" [{p['role']}]" if p.get("role") else ""
                arxiv = f" arxiv:{p['arxiv_id']}" if p.get("arxiv_id") else ""
                print(f"    - {p['title']} ({p.get('year', '?')}){role}{arxiv}")

        print()

    # Refs
    if refs:
        dir_str = " ".join(f"{k}:{v}" for k, v in refs["by_direction"].items())
        print(f"REFS: {refs['total']} papers ({refs['read']} read) | {dir_str}")
    else:
        print("REFS: no database")
    print()

    # Convergence check
    if current_node and current_node["scores"]:
        dim_names = {"N": "Novelty", "T": "Theory", "C": "Contribution", "F": "Feasibility", "R": "Risk"}
        below = []
        for dim, score in current_node["scores"].items():
            if score < threshold:
                below.append(f"{dim_names.get(dim, dim)}>={int(threshold)} (currently {score})")
        if below:
            print(f"CONVERGENCE: {len(below)} dim(s) below threshold: {', '.join(below)}")
        else:
            print("CONVERGENCE: All dimensions meet threshold!")
    else:
        print("CONVERGENCE: not yet scored")
    print()

    # Sketch info: last action, blocking issues, open questions
    last_action = sketch.get("last_action", "")
    if last_action and last_action not in ("-", ""):
        print(f"LAST ACTION: {last_action}")
    blocking = sketch.get("blocking_issues", "")
    if blocking and blocking.lower() not in ("none", "-", ""):
        print(f"BLOCKING: {blocking}")
    open_q = sketch.get("open_questions", [])
    if open_q:
        print(f"OPEN QUESTIONS: {'; '.join(open_q[:3])}")

    # Recent commits
    commits = get_recent_commits(cwd, 5)
    if commits:
        print(f"\nRECENT COMMITS:")
        for c in commits:
            print(f"  {c}")

    # Next steps from sketch
    print()
    if sketch.get("next_steps"):
        print(f"NEXT: {sketch['next_steps'].splitlines()[0]}")


if __name__ == "__main__":
    main()
