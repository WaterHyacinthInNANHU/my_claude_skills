#!/usr/bin/env python3
"""Reference database manager for idea_refinery.

SQLite + FTS5 backend for managing papers with rich context.
Supports add, search, get, list, update, link, export.

Usage:
    python3 refs.py init                          # Create database
    python3 refs.py add --arxiv 2401.12345 ...    # Add a paper
    python3 refs.py search "diffusion policy"     # Full-text search
    python3 refs.py get ze2025idp3                # Get paper details
    python3 refs.py list [--direction A.1] ...    # List papers with filters
    python3 refs.py update ze2025idp3 --notes "..." # Update fields
    python3 refs.py link A.1.2 ze2025idp3 builds_on  # Link paper to idea version
    python3 refs.py links A.1.2                   # Show papers for an idea version
    python3 refs.py export-bib [--direction A.1]  # Export to BibTeX
    python3 refs.py export-md [--direction A.1]   # Export to markdown table
    python3 refs.py import-bib refs.bib           # Import from BibTeX
    python3 refs.py stats                         # Database statistics
    python3 refs.py remove ze2025idp3             # Remove a paper
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import textwrap
from datetime import date
from pathlib import Path

DEFAULT_DB = "refs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY,
    arxiv_id TEXT,
    title TEXT NOT NULL,
    authors TEXT,
    year INTEGER,
    venue TEXT,
    url TEXT,
    code_url TEXT,
    direction TEXT DEFAULT 'seed',
    role TEXT,
    relevance TEXT DEFAULT 'medium',
    read INTEGER DEFAULT 0,
    abstract TEXT,
    notes TEXT,
    relationship TEXT,
    resource_details TEXT,
    added_date TEXT,
    updated_date TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5(
    id, title, authors, abstract, notes, relationship,
    content='papers', content_rowid='rowid'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS papers_ai AFTER INSERT ON papers BEGIN
    INSERT INTO papers_fts(rowid, id, title, authors, abstract, notes, relationship)
    VALUES (new.rowid, new.id, new.title, new.authors, new.abstract, new.notes, new.relationship);
END;

CREATE TRIGGER IF NOT EXISTS papers_ad AFTER DELETE ON papers BEGIN
    INSERT INTO papers_fts(papers_fts, rowid, id, title, authors, abstract, notes, relationship)
    VALUES ('delete', old.rowid, old.id, old.title, old.authors, old.abstract, old.notes, old.relationship);
END;

CREATE TRIGGER IF NOT EXISTS papers_au AFTER UPDATE ON papers BEGIN
    INSERT INTO papers_fts(papers_fts, rowid, id, title, authors, abstract, notes, relationship)
    VALUES ('delete', old.rowid, old.id, old.title, old.authors, old.abstract, old.notes, old.relationship);
    INSERT INTO papers_fts(rowid, id, title, authors, abstract, notes, relationship)
    VALUES (new.rowid, new.id, new.title, new.authors, new.abstract, new.notes, new.relationship);
END;

CREATE TABLE IF NOT EXISTS idea_paper_links (
    idea_version TEXT NOT NULL,
    paper_id TEXT NOT NULL,
    role TEXT,
    note TEXT,
    PRIMARY KEY (idea_version, paper_id),
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);
"""


def get_db(db_path=None):
    path = db_path or DEFAULT_DB
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path=None):
    conn = get_db(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"Database initialized: {db_path or DEFAULT_DB}")


def generate_id(authors, year, title):
    """Generate a BibTeX-style key: firstauthor_year_firstword."""
    first_author = ""
    if authors:
        first_author = authors.split(",")[0].split(" and ")[0].strip()
        first_author = first_author.split()[-1].lower() if first_author else ""
        first_author = re.sub(r"[^a-z]", "", first_author)
    first_word = ""
    if title:
        words = re.sub(r"[^a-zA-Z0-9\s]", "", title).split()
        skip = {"a", "an", "the", "on", "in", "of", "for", "with", "to", "and", "via"}
        for w in words:
            if w.lower() not in skip:
                first_word = w.lower()
                break
    yr = str(year) if year else ""
    key = f"{first_author}{yr}{first_word}"
    return key or "unknown"


def cmd_add(args):
    conn = get_db(args.db)
    today = date.today().isoformat()

    paper_id = args.id
    if not paper_id:
        paper_id = generate_id(args.authors, args.year, args.title)

    # Check for duplicate
    existing = conn.execute("SELECT id FROM papers WHERE id = ?", (paper_id,)).fetchone()
    if existing:
        print(f"Paper '{paper_id}' already exists. Use 'update' to modify.", file=sys.stderr)
        conn.close()
        return 1

    url = args.url
    if not url and args.arxiv:
        url = f"https://arxiv.org/abs/{args.arxiv}"

    conn.execute(
        """INSERT INTO papers (id, arxiv_id, title, authors, year, venue, url, code_url,
           direction, role, relevance, read, abstract, notes, relationship, resource_details,
           added_date, updated_date)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            paper_id, args.arxiv, args.title, args.authors, args.year, args.venue,
            url, args.code_url, args.direction, args.role, args.relevance,
            1 if args.read else 0, args.abstract, args.notes, args.relationship,
            args.resource_details, today, today,
        ),
    )
    conn.commit()
    conn.close()
    print(f"Added: {paper_id}")
    return 0


def cmd_search(args):
    conn = get_db(args.db)
    query = args.query

    # FTS5 search
    rows = conn.execute(
        """SELECT p.id, p.title, p.authors, p.year, p.relevance, p.direction,
                  highlight(papers_fts, 4, '>>>', '<<<') as notes_highlight
           FROM papers_fts f
           JOIN papers p ON f.rowid = p.rowid
           WHERE papers_fts MATCH ?
           ORDER BY rank
           LIMIT ?""",
        (query, args.limit),
    ).fetchall()

    if not rows:
        print("No results found.")
        conn.close()
        return

    for r in rows:
        print(f"[{r['id']}] {r['title']}")
        print(f"  Authors: {r['authors'] or '?'} | Year: {r['year'] or '?'} | "
              f"Relevance: {r['relevance'] or '?'} | Direction: {r['direction'] or '?'}")
        if r["notes_highlight"]:
            # Show truncated highlighted notes
            highlight = r["notes_highlight"][:200]
            print(f"  Notes: {highlight}")
        print()

    print(f"({len(rows)} result{'s' if len(rows) != 1 else ''})")
    conn.close()


def cmd_get(args):
    conn = get_db(args.db)
    row = conn.execute("SELECT * FROM papers WHERE id = ?", (args.paper_id,)).fetchone()
    if not row:
        print(f"Paper '{args.paper_id}' not found.", file=sys.stderr)
        conn.close()
        return 1

    if args.json:
        print(json.dumps(dict(row), indent=2))
    else:
        print(f"# {row['title']}")
        print(f"ID: {row['id']}")
        print(f"arXiv: {row['arxiv_id'] or 'N/A'}")
        print(f"Authors: {row['authors'] or 'N/A'}")
        print(f"Year: {row['year'] or 'N/A'} | Venue: {row['venue'] or 'N/A'}")
        print(f"URL: {row['url'] or 'N/A'}")
        print(f"Code: {row['code_url'] or 'N/A'}")
        print(f"Direction: {row['direction']} | Role: {row['role'] or 'N/A'} | "
              f"Relevance: {row['relevance']} | Read: {'Yes' if row['read'] else 'No'}")
        if row["abstract"]:
            print(f"\n## Abstract\n{row['abstract']}")
        if row["notes"]:
            print(f"\n## Notes\n{row['notes']}")
        if row["relationship"]:
            print(f"\n## Relationship to Our Idea\n{row['relationship']}")
        if row["resource_details"]:
            print(f"\n## Resource Details\n{row['resource_details']}")

        # Show linked idea versions
        links = conn.execute(
            "SELECT idea_version, role, note FROM idea_paper_links WHERE paper_id = ?",
            (args.paper_id,),
        ).fetchall()
        if links:
            print(f"\n## Linked Idea Versions")
            for l in links:
                print(f"  - {l['idea_version']} ({l['role'] or 'N/A'}): {l['note'] or ''}")

    conn.close()
    return 0


def cmd_list(args):
    conn = get_db(args.db)
    query = "SELECT id, title, authors, year, venue, relevance, direction, role, read FROM papers WHERE 1=1"
    params = []

    if args.direction:
        query += " AND direction = ?"
        params.append(args.direction)
    if args.relevance:
        query += " AND relevance = ?"
        params.append(args.relevance)
    if args.role:
        query += " AND role = ?"
        params.append(args.role)
    if args.unread:
        query += " AND read = 0"
    if args.year:
        query += " AND year = ?"
        params.append(args.year)

    query += " ORDER BY "
    if args.sort == "year":
        query += "year DESC, title"
    elif args.sort == "relevance":
        query += "CASE relevance WHEN 'high' THEN 1 WHEN 'medium' THEN 2 WHEN 'low' THEN 3 ELSE 4 END, year DESC"
    else:
        query += "added_date DESC"

    if args.limit:
        query += " LIMIT ?"
        params.append(args.limit)

    rows = conn.execute(query, params).fetchall()

    if args.json:
        print(json.dumps([dict(r) for r in rows], indent=2))
    else:
        if not rows:
            print("No papers found.")
            conn.close()
            return

        for r in rows:
            read_mark = "✓" if r["read"] else " "
            print(f"[{read_mark}] {r['id']:30s} | {r['year'] or '?':4} | "
                  f"{r['relevance'] or '?':6s} | {r['direction'] or '?':8s} | "
                  f"{(r['title'] or '')[:60]}")

        print(f"\n({len(rows)} paper{'s' if len(rows) != 1 else ''})")
    conn.close()


def cmd_update(args):
    conn = get_db(args.db)
    existing = conn.execute("SELECT id FROM papers WHERE id = ?", (args.paper_id,)).fetchone()
    if not existing:
        print(f"Paper '{args.paper_id}' not found.", file=sys.stderr)
        conn.close()
        return 1

    updates = []
    params = []
    fields = [
        "title", "authors", "year", "venue", "url", "code_url", "arxiv",
        "direction", "role", "relevance", "abstract", "notes",
        "relationship", "resource_details",
    ]
    for f in fields:
        val = getattr(args, f.replace("-", "_"), None)
        if val is not None:
            col = "arxiv_id" if f == "arxiv" else f
            updates.append(f"{col} = ?")
            params.append(val)
    if args.read:
        updates.append("read = 1")
    if args.append_notes:
        updates.append("notes = COALESCE(notes, '') || '\n\n' || ?")
        params.append(args.append_notes)

    if not updates:
        print("Nothing to update.", file=sys.stderr)
        conn.close()
        return 1

    updates.append("updated_date = ?")
    params.append(date.today().isoformat())
    params.append(args.paper_id)

    conn.execute(f"UPDATE papers SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    print(f"Updated: {args.paper_id}")
    return 0


def cmd_link(args):
    conn = get_db(args.db)
    # Verify paper exists
    existing = conn.execute("SELECT id FROM papers WHERE id = ?", (args.paper_id,)).fetchone()
    if not existing:
        print(f"Paper '{args.paper_id}' not found.", file=sys.stderr)
        conn.close()
        return 1

    conn.execute(
        """INSERT OR REPLACE INTO idea_paper_links (idea_version, paper_id, role, note)
           VALUES (?, ?, ?, ?)""",
        (args.idea_version, args.paper_id, args.role, args.note),
    )
    conn.commit()
    conn.close()
    print(f"Linked: {args.paper_id} → {args.idea_version} ({args.role or 'N/A'})")
    return 0


def cmd_links(args):
    conn = get_db(args.db)
    rows = conn.execute(
        """SELECT p.id, p.title, p.year, p.relevance, l.role, l.note
           FROM idea_paper_links l
           JOIN papers p ON l.paper_id = p.id
           WHERE l.idea_version = ?
           ORDER BY l.role, p.year""",
        (args.idea_version,),
    ).fetchall()

    if not rows:
        print(f"No papers linked to version '{args.idea_version}'.")
        conn.close()
        return

    print(f"Papers for idea version: {args.idea_version}\n")
    for r in rows:
        print(f"  [{r['id']}] {r['title']} ({r['year'] or '?'})")
        print(f"    Role: {r['role'] or 'N/A'} | Relevance: {r['relevance'] or '?'}")
        if r["note"]:
            print(f"    Note: {r['note']}")
        print()

    print(f"({len(rows)} paper{'s' if len(rows) != 1 else ''})")
    conn.close()


def cmd_export_bib(args):
    conn = get_db(args.db)
    query = "SELECT * FROM papers WHERE 1=1"
    params = []
    if args.direction:
        query += " AND direction = ?"
        params.append(args.direction)
    if args.idea_version:
        query = """SELECT p.* FROM papers p
                   JOIN idea_paper_links l ON p.id = l.paper_id
                   WHERE l.idea_version = ?"""
        params = [args.idea_version]

    query += " ORDER BY year DESC, id"
    rows = conn.execute(query, params).fetchall()

    for r in rows:
        entry_type = "article"
        if r["venue"]:
            v = r["venue"].lower()
            if any(k in v for k in ["neurips", "icml", "iclr", "cvpr", "iccv", "aaai", "corl", "rss", "iros"]):
                entry_type = "inproceedings"

        bib = f"@{entry_type}{{{r['id']},\n"
        if r["title"]:
            bib += f"  title     = {{{r['title']}}},\n"
        if r["authors"]:
            bib += f"  author    = {{{r['authors']}}},\n"
        if r["year"]:
            bib += f"  year      = {{{r['year']}}},\n"
        if r["venue"]:
            field = "booktitle" if entry_type == "inproceedings" else "journal"
            bib += f"  {field:9s} = {{{r['venue']}}},\n"
        if r["arxiv_id"]:
            bib += f"  eprint    = {{{r['arxiv_id']}}},\n"
            bib += f"  archivePrefix = {{arXiv}},\n"
        if r["url"]:
            bib += f"  url       = {{{r['url']}}},\n"
        if r["code_url"]:
            bib += f"  code      = {{{r['code_url']}}},\n"
        bib += "}\n"
        print(bib)

    print(f"% Exported {len(rows)} entries", file=sys.stderr)
    conn.close()


def cmd_export_md(args):
    conn = get_db(args.db)
    query = "SELECT * FROM papers WHERE 1=1"
    params = []
    if args.direction:
        query += " AND direction = ?"
        params.append(args.direction)

    query += " ORDER BY relevance, year DESC"
    rows = conn.execute(query, params).fetchall()

    print("# References\n")
    print(f"| # | Paper | Year | Venue | Relevance | Direction | Code |")
    print(f"|---|-------|------|-------|-----------|-----------|------|")
    for i, r in enumerate(rows, 1):
        title = r["title"] or "?"
        link = r["url"] or ""
        paper_col = f"[{title}]({link})" if link else title
        code_col = f"[code]({r['code_url']})" if r["code_url"] else ""
        print(f"| {i} | {paper_col} | {r['year'] or '?'} | {r['venue'] or ''} | "
              f"{r['relevance'] or '?'} | {r['direction'] or ''} | {code_col} |")

    print(f"\n*{len(rows)} papers*", file=sys.stderr)
    conn.close()


def cmd_import_bib(args):
    """Simple BibTeX parser — handles common formats."""
    conn = get_db(args.db)
    bib_text = Path(args.bib_file).read_text()
    today = date.today().isoformat()

    # Split into entries
    entries = re.findall(r"@\w+\{([^,]+),([^@]*)\}", bib_text, re.DOTALL)
    count = 0

    for key, body in entries:
        key = key.strip()
        fields = {}
        for match in re.finditer(r"(\w+)\s*=\s*\{([^}]*)\}", body):
            fields[match.group(1).lower()] = match.group(2).strip()

        # Skip if already exists
        if conn.execute("SELECT id FROM papers WHERE id = ?", (key,)).fetchone():
            continue

        arxiv_id = fields.get("eprint", "")
        url = fields.get("url", "")
        if not url and arxiv_id:
            url = f"https://arxiv.org/abs/{arxiv_id}"

        year = None
        if "year" in fields:
            try:
                year = int(fields["year"])
            except ValueError:
                pass

        conn.execute(
            """INSERT INTO papers (id, arxiv_id, title, authors, year, venue, url, code_url,
               direction, relevance, added_date, updated_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'imported', 'medium', ?, ?)""",
            (
                key, arxiv_id, fields.get("title", key),
                fields.get("author", ""), year,
                fields.get("booktitle", fields.get("journal", "")),
                url, fields.get("code", ""),
                today, today,
            ),
        )
        count += 1

    conn.commit()
    conn.close()
    print(f"Imported {count} new entries from {args.bib_file}")


def cmd_remove(args):
    conn = get_db(args.db)
    existing = conn.execute("SELECT id, title FROM papers WHERE id = ?", (args.paper_id,)).fetchone()
    if not existing:
        print(f"Paper '{args.paper_id}' not found.", file=sys.stderr)
        conn.close()
        return 1

    conn.execute("DELETE FROM idea_paper_links WHERE paper_id = ?", (args.paper_id,))
    conn.execute("DELETE FROM papers WHERE id = ?", (args.paper_id,))
    conn.commit()
    conn.close()
    print(f"Removed: {args.paper_id} ({existing['title']})")
    return 0


def cmd_stats(args):
    conn = get_db(args.db)
    total = conn.execute("SELECT COUNT(*) as c FROM papers").fetchone()["c"]
    read = conn.execute("SELECT COUNT(*) as c FROM papers WHERE read = 1").fetchone()["c"]
    by_rel = conn.execute(
        "SELECT relevance, COUNT(*) as c FROM papers GROUP BY relevance ORDER BY c DESC"
    ).fetchall()
    by_dir = conn.execute(
        "SELECT direction, COUNT(*) as c FROM papers GROUP BY direction ORDER BY c DESC"
    ).fetchall()
    links = conn.execute("SELECT COUNT(*) as c FROM idea_paper_links").fetchone()["c"]

    print(f"Total papers: {total} ({read} read)")
    print(f"Idea-paper links: {links}")
    print(f"\nBy relevance:")
    for r in by_rel:
        print(f"  {r['relevance'] or 'unset':10s} {r['c']}")
    print(f"\nBy direction:")
    for r in by_dir:
        print(f"  {r['direction'] or 'unset':10s} {r['c']}")
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Idea Refinery reference database manager")
    parser.add_argument("--db", default=DEFAULT_DB, help="Database path (default: refs.db)")
    sub = parser.add_subparsers(dest="command", required=True)

    # init
    sub.add_parser("init", help="Initialize database")

    # add
    p = sub.add_parser("add", help="Add a paper")
    p.add_argument("--id", help="BibTeX key (auto-generated if omitted)")
    p.add_argument("--arxiv", help="arXiv ID (e.g. 2401.12345)")
    p.add_argument("--title", required=True)
    p.add_argument("--authors", default="")
    p.add_argument("--year", type=int)
    p.add_argument("--venue", default="")
    p.add_argument("--url", default="")
    p.add_argument("--code-url", default="")
    p.add_argument("--direction", default="seed")
    p.add_argument("--role", default="")
    p.add_argument("--relevance", default="medium", choices=["high", "medium", "low"])
    p.add_argument("--read", action="store_true")
    p.add_argument("--abstract", default="")
    p.add_argument("--notes", default="")
    p.add_argument("--relationship", default="")
    p.add_argument("--resource-details", default="")

    # search
    p = sub.add_parser("search", help="Full-text search")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=10)

    # get
    p = sub.add_parser("get", help="Get full paper details")
    p.add_argument("paper_id")
    p.add_argument("--json", action="store_true")

    # list
    p = sub.add_parser("list", help="List papers with filters")
    p.add_argument("--direction")
    p.add_argument("--relevance", choices=["high", "medium", "low"])
    p.add_argument("--role")
    p.add_argument("--year", type=int)
    p.add_argument("--unread", action="store_true")
    p.add_argument("--sort", default="date", choices=["date", "year", "relevance"])
    p.add_argument("--limit", type=int)
    p.add_argument("--json", action="store_true")

    # update
    p = sub.add_parser("update", help="Update paper fields")
    p.add_argument("paper_id")
    p.add_argument("--title")
    p.add_argument("--authors")
    p.add_argument("--year", type=int)
    p.add_argument("--venue")
    p.add_argument("--url")
    p.add_argument("--code-url")
    p.add_argument("--arxiv")
    p.add_argument("--direction")
    p.add_argument("--role")
    p.add_argument("--relevance", choices=["high", "medium", "low"])
    p.add_argument("--read", action="store_true")
    p.add_argument("--abstract")
    p.add_argument("--notes")
    p.add_argument("--append-notes", help="Append to existing notes")
    p.add_argument("--relationship")
    p.add_argument("--resource-details")

    # link
    p = sub.add_parser("link", help="Link paper to idea version")
    p.add_argument("idea_version", help="e.g. A.1.2")
    p.add_argument("paper_id")
    p.add_argument("role", nargs="?", default="", help="builds_on, supports, contradicts, compares")
    p.add_argument("--note", default="")

    # links
    p = sub.add_parser("links", help="Show papers linked to an idea version")
    p.add_argument("idea_version")

    # export-bib
    p = sub.add_parser("export-bib", help="Export to BibTeX")
    p.add_argument("--direction")
    p.add_argument("--idea-version", help="Export papers linked to this version")

    # export-md
    p = sub.add_parser("export-md", help="Export to markdown table")
    p.add_argument("--direction")

    # import-bib
    p = sub.add_parser("import-bib", help="Import from BibTeX file")
    p.add_argument("bib_file")

    # stats
    sub.add_parser("stats", help="Show database statistics")

    # remove
    p = sub.add_parser("remove", help="Remove a paper")
    p.add_argument("paper_id")

    args = parser.parse_args()

    if args.command == "init":
        init_db(args.db)
    elif args.command == "add":
        return cmd_add(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "get":
        return cmd_get(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "update":
        return cmd_update(args)
    elif args.command == "link":
        return cmd_link(args)
    elif args.command == "links":
        cmd_links(args)
    elif args.command == "export-bib":
        cmd_export_bib(args)
    elif args.command == "export-md":
        cmd_export_md(args)
    elif args.command == "import-bib":
        cmd_import_bib(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "remove":
        return cmd_remove(args)
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
