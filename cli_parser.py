#!/usr/bin/env python3
"""
CLI Resume Parser — batch process multiple resumes
Usage:
  python cli_parser.py resume.pdf
  python cli_parser.py resumes/                  # parse all files in folder
  python cli_parser.py resume.pdf --out results/
  python cli_parser.py resume.pdf --format table
"""

import argparse
import json
import os
import sys
from pathlib import Path
from parser_engine import ResumeParser

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns
    RICH = True
    console = Console()
except ImportError:
    RICH = False


def print_result(data, fmt="table"):
    if fmt == "json":
        print(json.dumps(data, indent=2))
        return

    if not RICH:
        print(json.dumps(data, indent=2))
        return

    c = data.get("contact", {})
    console.print(Panel(
        f"[bold cyan]{c.get('name','Unknown')}[/]\n"
        f"📧 {c.get('email','—')}   📞 {c.get('phone','—')}\n"
        f"🔗 {c.get('linkedin','—')}",
        title=f"[bold]Resume Score: [green]{data.get('score','?')}/100[/]",
        border_style="bright_blue"
    ))

    skills = data.get("skills", {})
    for cat, lst in skills.items():
        if lst:
            console.print(f"[bold yellow]{cat.upper()}:[/] {', '.join(lst)}")

    exp = data.get("experience", [])
    if exp:
        t = Table(title="Experience", show_header=True, header_style="bold magenta")
        t.add_column("Title"); t.add_column("Company"); t.add_column("Dates")
        for e in exp:
            t.add_row(e.get("title",""), e.get("company",""), " ".join(e.get("dates",[])))
        console.print(t)

    edu = data.get("education", [])
    if edu:
        t = Table(title="Education", show_header=True, header_style="bold green")
        t.add_column("Degree"); t.add_column("Institution"); t.add_column("Year")
        for e in edu:
            t.add_row(e.get("degree",""), e.get("institution",""), " ".join(e.get("dates",[])))
        console.print(t)


def parse_path(path, out_dir, fmt):
    parser = ResumeParser()
    p = Path(path)

    if p.is_dir():
        files = list(p.glob("*.pdf")) + list(p.glob("*.docx")) + list(p.glob("*.txt"))
        print(f"Found {len(files)} resume(s) in {p}")
        for f in files:
            parse_path(str(f), out_dir, fmt)
        return

    print(f"\n{'='*50}\nParsing: {p.name}")
    try:
        result = parser.parse(str(p))
        print_result(result, fmt)

        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
            out_file = Path(out_dir) / (p.stem + ".json")
            with open(out_file, "w") as f:
                json.dump(result, f, indent=2)
            print(f"✅ Saved → {out_file}")
    except Exception as e:
        print(f"❌ Error parsing {p.name}: {e}")


def main():
    ap = argparse.ArgumentParser(description="Resume Parser CLI")
    ap.add_argument("input", help="Resume file or folder path")
    ap.add_argument("--out", "-o", default=None, help="Output directory for JSON files")
    ap.add_argument("--format", "-f", choices=["table","json"], default="table")
    args = ap.parse_args()

    parse_path(args.input, args.out, args.format)


if __name__ == "__main__":
    main()
