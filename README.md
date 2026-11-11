# artiveew autopost

Approved Instagram carousels in `posts/` are published automatically at their scheduled time.

## Adding a post
```
posts/s01_millais_ophelia/
  01.jpg … 07.jpg   slides in order
  caption.txt       caption and hashtags
  post.json         {"status": "draft", "publish_at": "2026-11-10T20:00:00+09:00"}
```
- `draft`: still being made, never published
- `ready`: finished and waiting for approval, never published
- `approved`: published at `publish_at` (checked every 10 minutes)
- `published`: done; `media_id` is recorded

## Approving a post
Only the account owner approves. Either:
- tell Claude in the project thread, e.g. "s01 승인", or
- GitHub → Actions → "Approve post" → Run workflow → enter `s01` (optionally a new time).

Approving a post whose `publish_at` has already passed publishes it on the next run.

## Secrets (Settings → Secrets and variables → Actions)
- `IG_ACCESS_TOKEN`: system-user access token from the Meta app (Instagram API, Unified login). It does not expire.
The Instagram account ID (not secret) is set in `.github/workflows/publish.yml` as `IG_USER_ID`.

## Test without posting
Actions → "Publish approved posts" → Run workflow → tick "dry run".
