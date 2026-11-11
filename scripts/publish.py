"""Publish approved, due carousel posts to Instagram.

Each post lives in posts/<id>/ with:
  01.jpg ... NN.jpg   carousel slides in order (JPEG, 1080x1350)
  caption.txt         caption exactly as it should appear
  post.json           {"status": "approved", "publish_at": "2026-11-10T20:00:00+09:00"}

Status flow: draft (in progress) -> ready (finished, waiting for the owner's approval)
-> approved (owner said yes) -> published. Only posts with status "approved" whose
publish_at has passed are published; draft and ready posts are never touched.
After publishing, post.json gets status "published", the media id and time.

Env:
  IG_ACCESS_TOKEN  access token. Either a system-user token from the Meta business
                   portfolio (starts with EAA, never expires) or an Instagram-login
                   token (starts with IG).
  IG_USER_ID       numeric Instagram account ID. Required for EAA tokens, which
                   use graph.facebook.com; IG tokens can look it up themselves.
  IMAGE_BASE_URL   public base URL where posts/ is served, e.g.
                   https://raw.githubusercontent.com/<owner>/<repo>/main
  DRY_RUN=1        print what would happen without calling the API
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

VERSION = "v21.0"


def api_base() -> str:
    token = os.environ.get("IG_ACCESS_TOKEN", "")
    host = "graph.instagram.com" if token.startswith("IG") else "graph.facebook.com"
    return f"https://{host}/{VERSION}"
ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / "posts"


def call(method, path, **params):
    params["access_token"] = os.environ["IG_ACCESS_TOKEN"]
    data = urllib.parse.urlencode(params).encode()
    url = f"{api_base()}/{path}"
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data.decode()}")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} failed: {e.code} {e.read().decode()[:500]}")


def wait_ready(container_id, tries=30):
    for _ in range(tries):
        status = call("GET", container_id, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {container_id} status {status}")
        time.sleep(5)
    raise RuntimeError(f"container {container_id} not ready in time")


def publish(post_dir: Path, base_url: str, user_id: str, dry: bool) -> str:
    slides = sorted(p for p in post_dir.glob("*.jpg"))
    if not 2 <= len(slides) <= 10:
        raise RuntimeError(f"{post_dir.name}: carousel needs 2-10 jpg slides, found {len(slides)}")
    caption = (post_dir / "caption.txt").read_text(encoding="utf-8").strip()
    urls = [f"{base_url}/posts/{post_dir.name}/{urllib.parse.quote(p.name)}" for p in slides]
    if dry:
        print(f"[dry run] {post_dir.name}: {len(urls)} slides, caption {len(caption)} chars")
        for u in urls:
            print("   ", u)
        return "dry-run"
    children = []
    for u in urls:
        c = call("POST", f"{user_id}/media", image_url=u, is_carousel_item="true")
        children.append(c["id"])
    for c in children:
        wait_ready(c)
    carousel = call("POST", f"{user_id}/media", media_type="CAROUSEL",
                    children=",".join(children), caption=caption)
    wait_ready(carousel["id"])
    res = call("POST", f"{user_id}/media_publish", creation_id=carousel["id"])
    return res["id"]


def main():
    dry = os.environ.get("DRY_RUN") == "1"
    base_url = os.environ.get("IMAGE_BASE_URL", "").rstrip("/")
    if not base_url:
        sys.exit("IMAGE_BASE_URL is not set")
    if dry and os.environ.get("IG_ACCESS_TOKEN") and os.environ.get("IG_USER_ID"):
        # read-only call so a dry run also proves the token and account ID work
        info = call("GET", os.environ["IG_USER_ID"], fields="username")
        print(f"token OK: @{info.get('username')}")
    now = dt.datetime.now(dt.timezone.utc)
    due = []
    for meta_path in sorted(POSTS.glob("*/post.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("status") != "approved":
            continue
        when = dt.datetime.fromisoformat(meta["publish_at"])
        if when <= now:
            due.append((meta_path, meta))
    if not due:
        print("nothing due")
        return
    user_id = os.environ.get("IG_USER_ID", "").strip()
    if not user_id:
        if dry:
            user_id = "me"
        elif os.environ["IG_ACCESS_TOKEN"].startswith("IG"):
            user_id = call("GET", "me", fields="user_id")["user_id"]
        else:
            sys.exit("IG_USER_ID is not set (needed for system-user tokens)")
    failed = False
    for meta_path, meta in due:
        try:
            media_id = publish(meta_path.parent, base_url, user_id, dry)
            if not dry:
                meta.update(status="published", media_id=media_id,
                            published_at=dt.datetime.now(dt.timezone.utc).isoformat())
                meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"published {meta_path.parent.name}: {media_id}")
        except Exception as e:  # keep going with other posts, fail the run at the end
            failed = True
            print(f"ERROR {meta_path.parent.name}: {e}", file=sys.stderr)
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
