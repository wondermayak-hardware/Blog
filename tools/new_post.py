#!/usr/bin/env python3
"""Create a post file from a plain HTML body.
python tools/new_post.py body.html --title "My title" --desc "Meta description" --category English --labels "CUET 2027, English" [--date 2026-11-20] [--slug custom-slug]
The body is plain HTML (p, h2, h3, ol, ul). Start with <p>Quick Answer: ...</p>. build.py styles it into Clay UI blocks."""
import argparse, datetime, pathlib, re
ap = argparse.ArgumentParser()
ap.add_argument("body"); ap.add_argument("--title", required=True); ap.add_argument("--desc", required=True)
ap.add_argument("--category", required=True); ap.add_argument("--labels", default=""); ap.add_argument("--date", default=str(datetime.date.today())); ap.add_argument("--slug")
a = ap.parse_args()
slug = a.slug or re.sub(r"[^a-z0-9]+", "-", a.title.lower()).strip("-")[:70].strip("-")
out = pathlib.Path(__file__).resolve().parent.parent / "content" / "posts" / f"{slug}.html"
if out.exists(): raise SystemExit(f"{out.name} already exists")
body = pathlib.Path(a.body).read_text(encoding="utf-8").strip()
out.write_text(f"---\ntitle: {a.title}\ndescription: {a.desc}\ndate: {a.date}\ncategory: {a.category}\nlabels: {a.labels}\n---\n{body}\n", encoding="utf-8")
print("created", out)
