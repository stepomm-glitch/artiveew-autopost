# artiveew autopost

Approved Instagram carousels in `posts/` are published automatically at their scheduled time.

## Adding a post
```
posts/002_alhambra_boabdil/
  01.jpg … 07.jpg   slides in order
  caption.txt       caption and hashtags
  post.json         {"status": "draft", "publish_at": "2026-11-10T20:00:00+09:00"}
```
- `draft`: waiting for review, never published
- `approved`: published at `publish_at` (checked every 30 minutes)
- `published`: done; `media_id` is recorded

## Secrets (Settings → Secrets and variables → Actions)
- `IG_ACCESS_TOKEN`: system-user access token from the Meta app (Instagram API, Unified login). It does not expire.
The Instagram account ID (not secret) is set in `.github/workflows/publish.yml` as `IG_USER_ID`.

## Test without posting
Actions → "Publish approved posts" → Run workflow → tick "dry run".
