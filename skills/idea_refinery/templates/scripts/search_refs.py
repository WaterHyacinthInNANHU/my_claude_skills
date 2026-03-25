#!/usr/bin/env python3
"""Interactive fuzzy paper search for idea_refinery workspaces.

Loop-style REPL: type a query, browse results one at a time with arrow keys.
Supports fuzzy matching across title, authors, notes, and abstract.

Usage:
    python3 scripts/search_refs.py              # interactive mode
    python3 scripts/search_refs.py "query"      # one-shot mode (prints all)
    python3 scripts/search_refs.py --db refs.db # specify database path
"""

import os
import re
import readline
import sqlite3
import sys
import termios
import tty
from difflib import SequenceMatcher


# --- Color codes ---
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"
CLEAR_LINE = "\033[2K"
MOVE_UP = "\033[A"


def get_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def load_all_papers(conn):
    """Load all papers into memory for fuzzy matching."""
    rows = conn.execute(
        "SELECT id, title, authors, year, venue, arxiv_id, url, code_url, "
        "direction, relevance, read, notes, relationship, abstract "
        "FROM papers ORDER BY year DESC, title"
    ).fetchall()
    return [dict(r) for r in rows]


def paper_link(paper):
    """Get the best available link for a paper."""
    if paper.get("arxiv_id"):
        return f"https://arxiv.org/abs/{paper['arxiv_id']}"
    if paper.get("url"):
        return paper["url"]
    return None


def fuzzy_score(query, paper):
    """Score a paper against the query. Returns 0-1 (higher is better)."""
    query_lower = query.lower()
    tokens = query_lower.split()

    fields = [
        ("title", 3.0),
        ("authors", 2.0),
        ("id", 2.0),
        ("notes", 1.0),
        ("abstract", 0.8),
        ("relationship", 0.8),
        ("direction", 0.5),
        ("venue", 0.5),
    ]

    best_score = 0.0

    for field_name, weight in fields:
        value = paper.get(field_name) or ""
        value_lower = value.lower()
        if not value_lower:
            continue

        if query_lower in value_lower:
            best_score = max(best_score, 0.9 * weight)
            continue

        if all(t in value_lower for t in tokens):
            best_score = max(best_score, 0.8 * weight)
            continue

        token_scores = []
        for t in tokens:
            if t in value_lower:
                token_scores.append(1.0)
                continue
            words = value_lower.split()
            word_best = max((SequenceMatcher(None, t, w).ratio() for w in words), default=0.0)
            token_scores.append(word_best)

        if token_scores:
            avg = sum(token_scores) / len(token_scores)
            best_score = max(best_score, avg * weight * 0.7)

    for t in tokens:
        if re.match(r"^\d{4}$", t) and t == str(paper.get("year") or ""):
            best_score += 0.3

    return best_score


def fuzzy_search(papers, query, limit=20):
    """Fuzzy search papers, return top results."""
    scored = [(fuzzy_score(query, p), p) for p in papers]
    scored.sort(key=lambda x: -x[0])
    return [(s, p) for s, p in scored if s >= 0.2][:limit]


def format_card(paper, idx, total):
    """Format a single paper as a detailed card for browsing."""
    link = paper_link(paper)
    year = paper.get("year") or "?"
    authors = paper.get("authors") or "?"
    title = paper.get("title") or "?"
    venue = paper.get("venue") or ""
    direction = paper.get("direction") or ""
    read_mark = "read" if paper.get("read") else "unread"
    relevance = paper.get("relevance") or ""

    lines = []
    lines.append(f"{BOLD}[{idx}/{total}]{RESET} {DIM}(up/down to browse, Enter to search, q to quit){RESET}")
    lines.append("")
    venue_str = f" | {venue}" if venue else ""
    lines.append(f"  {BOLD}{title}{RESET}")
    lines.append(f"  {DIM}{authors}, {year}{venue_str}{RESET}")
    lines.append("")

    if link:
        lines.append(f"  {CYAN}{link}{RESET}")
    if paper.get("code_url"):
        lines.append(f"  {GREEN}code: {paper['code_url']}{RESET}")

    meta = []
    if direction:
        meta.append(f"dir:{direction}")
    if relevance:
        meta.append(f"rel:{relevance}")
    meta.append(read_mark)
    lines.append(f"  {' | '.join(meta)}")

    if paper.get("relationship"):
        lines.append(f"  {YELLOW}role: {paper['relationship']}{RESET}")

    abstract = paper.get("abstract") or ""
    if abstract:
        lines.append("")
        # Word-wrap abstract to ~80 chars
        words = abstract.split()
        cur_line = "  "
        for w in words:
            if len(cur_line) + len(w) + 1 > 80:
                lines.append(f"{DIM}{cur_line}{RESET}")
                cur_line = "  " + w
            else:
                cur_line += (" " if len(cur_line) > 2 else "") + w
        if cur_line.strip():
            lines.append(f"{DIM}{cur_line}{RESET}")

    notes = paper.get("notes") or ""
    if notes:
        lines.append("")
        lines.append(f"  {YELLOW}notes: {notes}{RESET}")

    return lines


def get_terminal_height():
    try:
        return os.get_terminal_size().lines
    except Exception:
        return 24


def read_key():
    """Read a single keypress, handling arrow key escape sequences."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                if ch3 == "A":
                    return "up"
                elif ch3 == "B":
                    return "down"
                elif ch3 == "C":
                    return "right"
                elif ch3 == "D":
                    return "left"
            return "esc"
        elif ch == "\r" or ch == "\n":
            return "enter"
        elif ch == "\x03":  # Ctrl-C
            return "ctrl-c"
        elif ch == "\x04":  # Ctrl-D
            return "ctrl-d"
        elif ch == "q" or ch == "Q":
            return "q"
        elif ch == "j":
            return "down"
        elif ch == "k":
            return "up"
        elif ch == "v":
            return "v"
        else:
            return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def clear_card(num_lines):
    """Clear the previously printed card lines."""
    for _ in range(num_lines):
        sys.stdout.write(f"{MOVE_UP}{CLEAR_LINE}\r")
    sys.stdout.flush()


def is_tty():
    """Check if stdin is a real terminal."""
    try:
        return os.isatty(sys.stdin.fileno())
    except Exception:
        return False


def browse_results(results):
    """Browse search results one at a time with arrow keys.

    Returns True to go back to search prompt, False to quit entirely.
    Falls back to printing all results if not a real terminal.
    """
    if not results:
        print("No matches found. Try broader terms.\n")
        return True

    # Fallback: print all if not a tty (piped input)
    if not is_tty():
        for i, (_, p) in enumerate(results, 1):
            card = format_card(p, i, len(results))
            print("\n".join(card))
            print()
        return True

    total = len(results)
    idx = 0
    last_card_lines = 0

    while True:
        _, paper = results[idx]
        card = format_card(paper, idx + 1, total)

        # Clear previous card
        if last_card_lines > 0:
            clear_card(last_card_lines)

        # Print new card
        output = "\n".join(card)
        print(output)
        last_card_lines = len(card)

        key = read_key()

        if key == "down" or key == "right":
            if idx < total - 1:
                idx += 1
        elif key == "up" or key == "left":
            if idx > 0:
                idx -= 1
        elif key == "enter":
            return True
        elif key in ("q", "ctrl-c", "ctrl-d", "esc"):
            return False


def format_link_line(paper):
    """One-line format for /links."""
    link = paper_link(paper)
    if link:
        year = paper.get("year") or "?"
        return f"  {paper['title']} ({year}) -- {link}"
    return None


def print_help():
    print(f"""
{BOLD}Commands:{RESET}
  <query>       Search papers (fuzzy match across title, authors, notes, etc.)
                Then browse results one-by-one with up/down arrow keys.
  /all          Browse all papers
  /links        List all paper links (copy-paste friendly)
  /dir <name>   Browse papers in a direction (e.g., /dir A.1)
  /help         Show this help
  /q            Quit (also: quit, exit, Ctrl-D, Ctrl-C)

{BOLD}While browsing:{RESET}
  up/k          Previous result
  down/j        Next result
  Enter         Back to search
  q / Esc       Quit
""")


def interactive(conn, papers, initial_query=None):
    """Interactive search loop."""
    print(f"{BOLD}Paper Search{RESET} ({len(papers)} papers in database)")
    print(f"Type a query to search, /help for commands, /q to quit.\n")

    query = initial_query

    while True:
        try:
            if query is None:
                query = input(f"{BOLD}search>{RESET} ").strip()
            if not query:
                query = None
                continue

            # Commands
            if query in ("/q", "quit", "exit"):
                break
            if query == "/help":
                print_help()
                query = None
                continue
            if query == "/all":
                results = [(1.0, p) for p in papers]
                if not browse_results(results):
                    break
                query = None
                continue
            if query == "/links":
                for p in papers:
                    line = format_link_line(p)
                    if line:
                        print(line)
                print()
                query = None
                continue
            if query.startswith("/dir "):
                dir_name = query[5:].strip()
                filtered = [(1.0, p) for p in papers if (p.get("direction") or "").lower() == dir_name.lower()]
                if filtered:
                    if not browse_results(filtered):
                        break
                else:
                    print(f"No papers in direction '{dir_name}'")
                    dirs = sorted(set(p.get("direction") or "?" for p in papers))
                    print(f"Available directions: {', '.join(dirs)}\n")
                query = None
                continue

            # Fuzzy search
            results = fuzzy_search(papers, query)
            if not browse_results(results):
                break
            query = None

        except (KeyboardInterrupt, EOFError):
            print()
            break


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Interactive fuzzy paper search")
    parser.add_argument("query", nargs="*", help="Initial search query (optional)")
    parser.add_argument("--db", default="refs.db", help="Path to refs.db")
    args = parser.parse_args()

    if not os.path.exists(args.db):
        print(f"Database not found: {args.db}", file=sys.stderr)
        print("Run this from an idea_refinery workspace, or use --db <path>", file=sys.stderr)
        sys.exit(1)

    conn = get_db(args.db)
    papers = load_all_papers(conn)

    if not papers:
        print("No papers in database yet.")
        conn.close()
        sys.exit(0)

    initial_query = " ".join(args.query) if args.query else None

    # One-shot mode if piped (not a tty)
    if initial_query and not sys.stdin.isatty():
        results = fuzzy_search(papers, initial_query)
        for i, (score, p) in enumerate(results, 1):
            card = format_card(p, i, len(results))
            print("\n".join(card))
            print()
        conn.close()
        sys.exit(0)

    interactive(conn, papers, initial_query)
    conn.close()


if __name__ == "__main__":
    main()
