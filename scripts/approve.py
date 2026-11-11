"""Approve a ready post so the publish workflow posts it at publish_at.

Usage: python scripts/approve.py <post folder> [publish_at]
  post folder  e.g. s01_millais_ophelia (a unique prefix such as s01 also works)
  publish_at   optional ISO time, e.g. 2026-11-11T21:00:00+09:00 (keeps the planned time if omitted)
Only posts with status "ready" can be approved.
"""
import datetime as dt
import json
import sys
from pathlib import Path

POSTS = Path(__file__).resolve().parent.parent / "posts"


def main():
    if len(sys.argv) < 2 or not sys.argv[1].strip():
        sys.exit("usage: approve.py <post folder> [publish_at]")
    key = sys.argv[1].strip()
    matches = [p for p in POSTS.iterdir() if p.is_dir() and (p.name == key or p.name.startswith(key))]
    exact = [p for p in matches if p.name == key]
    if exact:
        matches = exact
    if len(matches) != 1:
        sys.exit(f"'{key}' matches {len(matches)} posts: {[p.name for p in matches]}")
    meta_path = matches[0] / "post.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("status") != "ready":
        sys.exit(f"{matches[0].name} is '{meta.get('status')}', only 'ready' posts can be approved")
    when = sys.argv[2].strip() if len(sys.argv) > 2 else ""
    if when:
        meta["publish_at"] = when
    if not meta.get("publish_at"):
        sys.exit("publish_at is empty; pass a time")
    dt.datetime.fromisoformat(meta["publish_at"])  # validate
    meta["status"] = "approved"
    meta["approved_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"approved {matches[0].name}, publishes at {meta['publish_at']}")


if __name__ == "__main__":
    main()
