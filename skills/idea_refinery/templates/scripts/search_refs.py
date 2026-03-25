#!/usr/bin/env python3
"""Interactive fuzzy paper search for idea_refinery workspaces.

Loop-style REPL: type a query, get matching papers with links.
Supports fuzzy matching across title, authors, notes, and abstract.

Usage:
    python3 scripts/search_refs.py              # interactive mode
    python3 scripts/search_refs.py "query"      # one-shot mode
    python3 scripts/search_refs.py --db refs.db # specify database path
"""

import os
import re
import readline
import sqlite3
import sys
from difflib import SequenceMatcher


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
    """Score a paper against the query using fuzzy matching.

    Searches across title, authors, notes, abstract, relationship, id.
    Returns a score between 0 and 1 (higher is better).
    """
    query_lower = query.lower()
    tokens = query_lower.split()

    # Fields to search, with weights
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

        # Exact substring match (strong signal)
        if query_lower in value_lower:
            score = 0.9 * weight
            best_score = max(best_score, score)
            continue

        # All tokens present (strong signal)
        if all(t in value_lower for t in tokens):
            score = 0.8 * weight
            best_score = max(best_score, score)
            continue

        # Token-level fuzzy matching
        token_scores = []
        for t in tokens:
            # Check substring match for individual token
            if t in value_lower:
                token_scores.append(1.0)
                continue
            # SequenceMatcher for fuzzy
            words = value_lower.split()
            word_best = 0.0
            for w in words:
                ratio = SequenceMatcher(None, t, w).ratio()
                word_best = max(word_best, ratio)
            token_scores.append(word_best)

        if token_scores:
            avg = sum(token_scores) / len(token_scores)
            score = avg * weight * 0.7
            best_score = max(best_score, score)

    # Year matching bonus
    for t in tokens:
        if re.match(r"^\d{4}$", t):
            paper_year = str(paper.get("year") or "")
            if t == paper_year:
                best_score += 0.3

    return best_score


def format_result(paper, idx, verbose=False):
    """Format a paper result for display."""
    link = paper_link(paper)
    year = paper.get("year") or "?"
    authors = paper.get("authors") or "?"
    # Truncate long author lists
    if authors and len(authors) > 50:
        authors = authors[:47] + "..."
    title = paper.get("title") or "?"
    venue = paper.get("venue") or ""
    direction = paper.get("direction") or ""
    read_mark = "*" if paper.get("read") else " "
    relevance = paper.get("relevance") or ""

    # Color codes
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RESET = "\033[0m"

    lines = []
    # Main line
    venue_str = f" ({venue})" if venue else ""
    lines.append(
        f"  {BOLD}{idx}.{RESET} [{read_mark}] {BOLD}{title}{RESET} "
        f"{DIM}— {authors}, {year}{venue_str}{RESET}"
    )

    # Link + metadata
    meta_parts = []
    if link:
        meta_parts.append(f"{CYAN}{link}{RESET}")
    if paper.get("code_url"):
        meta_parts.append(f"{GREEN}code: {paper['code_url']}{RESET}")
    if direction:
        meta_parts.append(f"dir:{direction}")
    if relevance:
        meta_parts.append(f"rel:{relevance}")
    if meta_parts:
        lines.append(f"       {' | '.join(meta_parts)}")

    # Abstract (always shown, truncated)
    abstract = paper.get("abstract") or ""
    if abstract:
        if len(abstract) > 150:
            abstract = abstract[:147] + "..."
        lines.append(f"       {DIM}{abstract}{RESET}")

    # Notes + role (if verbose)
    if verbose:
        notes = paper.get("notes") or ""
        rel = paper.get("relationship") or ""
        if rel:
            lines.append(f"       {YELLOW}role: {rel}{RESET}")
        if notes:
            if len(notes) > 120:
                notes = notes[:117] + "..."
            lines.append(f"       {DIM}notes: {notes}{RESET}")

    return "\n".join(lines)


def search(papers, query, limit=10):
    """Fuzzy search papers, return top results."""
    scored = [(fuzzy_score(query, p), p) for p in papers]
    scored.sort(key=lambda x: -x[0])
    # Filter out very low scores
    threshold = 0.2
    results = [(s, p) for s, p in scored if s >= threshold]
    return results[:limit]


def fts_search(conn, query):
    """Use FTS5 for initial filtering when available."""
    try:
        rows = conn.execute(
            "SELECT p.* FROM papers p JOIN papers_fts f ON p.rowid = f.rowid "
            "WHERE papers_fts MATCH ? ORDER BY rank LIMIT 50",
            (query,),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return None


def print_help():
    BOLD = "\033[1m"
    RESET = "\033[0m"
    print(f"""
{BOLD}Commands:{RESET}
  <query>       Search papers (fuzzy match across title, authors, notes, etc.)
  <number>      Show full details for result #N from last search
  /all          List all papers
  /links        List all paper links (copy-paste friendly)
  /dir <name>   Filter by direction (e.g., /dir A.1)
  /v            Toggle verbose mode (show notes)
  /help         Show this help
  /q            Quit (also: quit, exit, Ctrl-D, Ctrl-C)
""")


def show_detail(paper):
    """Show full details for a single paper."""
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RESET = "\033[0m"

    link = paper_link(paper)
    print(f"\n{BOLD}{'=' * 60}{RESET}")
    print(f"{BOLD}{paper.get('title', '?')}{RESET}")
    print(f"{DIM}{paper.get('authors', '?')}, {paper.get('year', '?')}{RESET}")
    if paper.get("venue"):
        print(f"Venue: {paper['venue']}")
    print(f"ID: {paper['id']}")
    if link:
        print(f"Link: {CYAN}{link}{RESET}")
    if paper.get("code_url"):
        print(f"Code: {GREEN}{paper['code_url']}{RESET}")
    print(f"Direction: {paper.get('direction', '?')} | Relevance: {paper.get('relevance', '?')} | Read: {'yes' if paper.get('read') else 'no'}")
    if paper.get("relationship"):
        print(f"{YELLOW}Role: {paper['relationship']}{RESET}")
    if paper.get("abstract"):
        print(f"\nAbstract:\n{DIM}{paper['abstract']}{RESET}")
    if paper.get("notes"):
        print(f"\nNotes:\n{paper['notes']}")
    if paper.get("resource_details"):
        print(f"\nResources: {paper['resource_details']}")
    print(f"{BOLD}{'=' * 60}{RESET}\n")


def interactive(conn, papers, initial_query=None):
    """Interactive search loop."""
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    verbose = False
    last_results = []

    print(f"{BOLD}Paper Search{RESET} ({len(papers)} papers in database)")
    print(f"Type a query to search, /help for commands, /q to quit.\n")

    # Handle initial query
    if initial_query:
        query = initial_query
    else:
        query = None

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
            if query == "/v":
                verbose = not verbose
                print(f"Verbose mode: {'on' if verbose else 'off'}")
                query = None
                continue
            if query == "/all":
                last_results = [(1.0, p) for p in papers]
                for i, (_, p) in enumerate(last_results, 1):
                    print(format_result(p, i, verbose))
                print(f"\n{DIM}{len(papers)} papers total{RESET}\n")
                query = None
                continue
            if query == "/links":
                for p in papers:
                    link = paper_link(p)
                    if link:
                        year = p.get("year") or "?"
                        print(f"  {p['title']} ({year}) — {link}")
                print()
                query = None
                continue
            if query.startswith("/dir "):
                dir_name = query[5:].strip()
                filtered = [(1.0, p) for p in papers if (p.get("direction") or "").lower() == dir_name.lower()]
                last_results = filtered
                if filtered:
                    for i, (_, p) in enumerate(filtered, 1):
                        print(format_result(p, i, verbose))
                    print(f"\n{DIM}{len(filtered)} papers in direction '{dir_name}'{RESET}\n")
                else:
                    print(f"No papers in direction '{dir_name}'")
                    dirs = sorted(set(p.get("direction") or "?" for p in papers))
                    print(f"Available directions: {', '.join(dirs)}\n")
                query = None
                continue

            # Number: show detail for last result
            if query.isdigit():
                idx = int(query)
                if 1 <= idx <= len(last_results):
                    show_detail(last_results[idx - 1][1])
                else:
                    print(f"No result #{idx}. Last search had {len(last_results)} results.")
                query = None
                continue

            # Fuzzy search
            results = search(papers, query)
            last_results = results

            if results:
                for i, (score, p) in enumerate(results, 1):
                    print(format_result(p, i, verbose))
                print(f"\n{DIM}{len(results)} results (type a number for details){RESET}\n")
            else:
                print("No matches found. Try broader terms.\n")

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
        results = search(papers, initial_query)
        for i, (score, p) in enumerate(results, 1):
            print(format_result(p, i, verbose=True))
        conn.close()
        sys.exit(0)

    interactive(conn, papers, initial_query)
    conn.close()


if __name__ == "__main__":
    main()
