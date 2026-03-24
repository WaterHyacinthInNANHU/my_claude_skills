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
            # suffix is "" for root, "/A" for direction, "/A.1" for sub
            branches.append({"branch": name, "suffix": suffix})
    return branches


def parse_scores_from_card(card_path):
    """Parse validation scores from an idea card file."""
    scores = {}
    dim_names = ["novelty", "theory", "contribution", "feasibility", "risk"]
    try:
        text = Path(card_path).read_text()
        for dim in dim_names:
            # Match patterns like "| Novelty | 4/5 |" or "| Novelty | ⬤⬤⬤⬤○ |"
            pattern = rf"\|\s*{dim}\s*\|[^|]*?(\d)/5"
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                scores[dim[0].upper()] = int(m.group(1))
            else:
                # Try bullet notation
                pattern2 = rf"\|\s*{dim}\s*\|\s*([\u2B24\u25CB]+)"
                m2 = re.search(pattern2, text, re.IGNORECASE)
                if m2:
                    scores[dim[0].upper()] = m2.group(1).count("\u2B24")
    except Exception:
        pass
    return scores


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
        # Extract GPU info
        for line in text.splitlines():
            if "GPU" in line and "|" in line:
                cells = [c.strip() for c in line.split("|")]
                if len(cells) >= 3 and cells[2] and cells[2] != "Budget":
                    parts.append(cells[2])
            if "deadline" in line.lower() and "|" in line:
                cells = [c.strip() for c in line.split("|")]
                if len(cells) >= 3 and cells[2] and cells[2] != "Budget":
                    parts.append(f"deadline {cells[2]}")
        # Extract strategy
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

        # Count per direction
        dir_counts = {}
        rows = cur.execute("SELECT direction, COUNT(*) FROM papers GROUP BY direction").fetchall()
        for d, c in rows:
            if d:
                dir_counts[d] = c
        conn.close()
        return {"total": total, "read": read_count, "by_direction": dir_counts}
    except Exception:
        return None


def get_sketch_info(cwd):
    """Parse key fields from sketch.md."""
    sketch_path = os.path.join(cwd, "doc/agent/sketch.md")
    if not os.path.exists(sketch_path):
        return {}
    try:
        text = Path(sketch_path).read_text()
        info = {}
        for field in ["Phase", "Iteration", "Current idea version", "Last action", "Blocking issues"]:
            m = re.search(rf"\*\*{re.escape(field)}:\*\*\s*(.+)", text)
            if m:
                info[field.lower().replace(" ", "_")] = m.group(1).strip()
        # Get next steps
        m = re.search(r"## Next Steps\s*\n((?:\d+\..+\n?)+)", text)
        if m:
            info["next_steps"] = m.group(1).strip()
        return info
    except Exception:
        return {}


def build_tree(cwd, tag):
    """Build the idea tree structure."""
    branches = get_idea_branches(cwd, tag)
    versions_dir = os.path.join(cwd, "doc/agent/idea_versions")
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

        # Try to find associated idea card and parse scores
        scores = {}
        card_dir = versions_dir
        if os.path.isdir(card_dir):
            for f in os.listdir(card_dir):
                fpath = os.path.join(card_dir, f)
                s = parse_scores_from_card(fpath)
                # Try to match card to branch by checking content
                try:
                    content = Path(fpath).read_text()
                    if node_id != "root" and node_id.lower() in content.lower():
                        scores = s
                        break
                    elif node_id == "root" and "v0" in f:
                        scores = s
                        break
                except Exception:
                    pass

        is_current = b["branch"] == current
        depth = suffix.count("/") + suffix.count(".")
        nodes.append({
            "id": node_id,
            "branch": b["branch"],
            "suffix": suffix,
            "scores": scores,
            "is_current": is_current,
            "depth": depth,
            "label": label,
        })

    return nodes


def format_tree_text(nodes, tag):
    """Format the tree as indented text."""
    if not nodes:
        return "  (no branches yet)"

    lines = []
    # Sort: root first, then alphabetically by suffix
    root = [n for n in nodes if n["id"] == "root"]
    children = sorted([n for n in nodes if n["id"] != "root"], key=lambda x: x["suffix"])

    def fmt_node(n):
        score_str = f"[{format_scores(n['scores'])}]" if n["scores"] else ""
        marker = " <- current" if n["is_current"] else ""
        return f"{n['label']} {score_str}{marker}"

    if root:
        lines.append(f"  {fmt_node(root[0])}")

    # Simple tree rendering for directions
    prev_prefix = ""
    for i, n in enumerate(children):
        parts = n["id"].split(".")
        dir_letter = parts[0] if parts else n["id"]
        indent = "  " * (len(parts))
        connector = "\u251c\u2500" if i < len(children) - 1 else "\u2514\u2500"
        lines.append(f"  {indent}{connector} {fmt_node(n)}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Idea refinery status")
    parser.add_argument("--tree-only", action="store_true", help="Show only the idea tree")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--cwd", default=".", help="Workspace directory")
    args = parser.parse_args()

    cwd = os.path.abspath(args.cwd)
    tag = get_tag(cwd)
    if not tag:
        # Try to detect from sketch.md
        sketch = get_sketch_info(cwd)
        print("Not on an ideate/ branch. cd to a workspace and checkout an ideate branch.")
        sys.exit(1)

    current_branch = get_current_branch(cwd)
    nodes = build_tree(cwd, tag)
    config_summary = get_config_summary(cwd)
    refs = get_refs_stats(cwd)
    sketch = get_sketch_info(cwd)
    threshold = get_convergence_threshold(cwd)

    if args.json:
        data = {
            "tag": tag,
            "branch": current_branch,
            "config": config_summary,
            "threshold": threshold,
            "sketch": sketch,
            "tree": nodes,
            "refs": refs,
        }
        print(json.dumps(data, indent=2))
        return

    # Find current node
    current_node = next((n for n in nodes if n["is_current"]), None)
    current_id = current_node["id"] if current_node else "?"
    current_version = sketch.get("current_idea_version", "?")

    print(f"=== IDEA REFINERY STATUS: {tag} ===")
    print(f"Config: {config_summary}")
    print(f"Current: {current_version} on branch {current_branch}")
    print()

    # Tree
    print("TREE:")
    print(format_tree_text(nodes, tag))
    print()

    if args.tree_only:
        return

    # Refs
    if refs:
        dir_str = " ".join(f"{k}:{v}" for k, v in refs["by_direction"].items())
        print(f"REFS: {refs['total']} papers ({refs['read']} read) | {dir_str}")
    else:
        print("REFS: no database")
    print()

    # Convergence check
    if current_node and current_node["scores"]:
        below = []
        for dim, score in current_node["scores"].items():
            if score < threshold:
                dim_names = {"N": "Novelty", "T": "Theory", "C": "Contribution", "F": "Feasibility", "R": "Risk"}
                below.append(f"{dim_names.get(dim, dim)}>={int(threshold)} (currently {score})")
        if below:
            print(f"CONVERGENCE: {len(below)} dim(s) below threshold: {', '.join(below)}")
        else:
            print("CONVERGENCE: All dimensions meet threshold!")
    else:
        print("CONVERGENCE: not yet scored")
    print()

    # Next steps from sketch
    if sketch.get("next_steps"):
        print(f"NEXT: {sketch['next_steps'].splitlines()[0]}")


if __name__ == "__main__":
    main()
