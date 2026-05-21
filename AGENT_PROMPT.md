# Agent Prompt: Random README Banner Backend

## Overview

Build a backend service that serves a random rotating banner image for use in GitHub README files.
The service is stateless on its own but tracks state through Supabase. It cycles through 30 images
without repeating until all have been shown, then resets. It includes key-based auth and rate limiting.

---

## Tech Stack

| Layer    | Technology                     |
|----------|--------------------------------|
| Backend  | Python 3.12 + FastAPI          |
| Database | Supabase (PostgreSQL)          |
| Hosting  | Vercel (serverless)            |
| Images   | 30 WebP files at 3:1 ratio     |

---

## Folder Structure

Build the following structure exactly:

```
random-banner/
├── src/
│   └── img/
│       ├── 1.webp
│       ├── 2.webp
│       └── ... (30 images - already exist, do not touch)
├── api/
│   └── index.py
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── vercel.json
└── README.md
```

---

## Supabase Schema

Run this SQL in the Supabase SQL Editor to create the two required tables.

```sql
-- tracks which image numbers have been shown in the current cycle
CREATE TABLE shown_banners (
  id        SERIAL PRIMARY KEY,
  image_number INTEGER NOT NULL CHECK (image_number BETWEEN 1 AND 30),
  shown_at  TIMESTAMPTZ DEFAULT NOW()
);

-- single-row table that caches the active image and the rate limit window
-- id is always 1 - only one row ever exists
CREATE TABLE rate_limit (
  id           INTEGER PRIMARY KEY DEFAULT 1,
  image_number INTEGER NOT NULL,
  available_at TIMESTAMPTZ NOT NULL
);

-- disable RLS on both tables so the anon key can read and write freely
ALTER TABLE shown_banners DISABLE ROW LEVEL SECURITY;
ALTER TABLE rate_limit     DISABLE ROW LEVEL SECURITY;
```

---

## Environment Variables

### Backend `.env` file (never commit this)

```
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-supabase-anon-key
BANNER_KEY=your-unique-custom-key-goes-here
```

### `.env.example` file (commit this)

```
SUPABASE_URL=
SUPABASE_KEY=
BANNER_KEY=
```

### Vercel Environment Variables (set in dashboard)

Set these three keys in the Vercel project settings under Environment Variables:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `BANNER_KEY`

### GitHub Secret (for the README link)

The README embeds the banner URL. Store `BANNER_KEY` as a GitHub repository secret named
`BANNER_KEY` under Settings > Secrets and Variables > Actions if you use GitHub Actions.
For a static README embed (simpler), paste the full URL with the key directly into the README.

---

## File: `requirements.txt`

```
fastapi==0.115.0
supabase==2.9.0
python-dotenv==1.0.1
```

---

## File: `vercel.json`

```json
{
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/api/index.py"
    }
  ]
}
```

Vercel's Python runtime bundles all project files by default. The `src/img/` folder will be
included in the serverless function bundle automatically. No extra `includeFiles` config is needed.

---

## File: `.gitignore`

```
.env
__pycache__/
*.pyc
.vercel
```

---

## File: `api/index.py`

This is the entire backend. Build it exactly as shown.

```python
import os
import random
import pathlib
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from supabase import create_client, Client

# load env vars from .env in local dev
load_dotenv()

app = FastAPI()

# total number of banner images in src/img
TOTAL_IMAGES = 30

# combined window in seconds: 30s rate limit + 5s post-response timeout
CACHE_SECONDS = 35

# path to the images folder relative to this file
IMG_DIR = pathlib.Path(__file__).parent.parent / "src" / "img"


def get_db() -> Client:
    # read credentials from environment
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    return create_client(url, key)


def serve_image(image_number: int) -> Response:
    # build absolute path for the requested image
    img_path = IMG_DIR / f"{image_number}.webp"

    # return 404 if the file is somehow missing
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    img_bytes = img_path.read_bytes()

    return Response(
        content=img_bytes,
        media_type="image/webp",
        headers={
            # prevent GitHub and CDNs from caching this response
            "Cache-Control": "no-cache no-store must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.get("/banner")
async def get_banner(key: str = "") -> Response:
    # --- step 1: verify the api key ---
    expected_key = os.environ.get("BANNER_KEY", "")
    if not key or key != expected_key:
        raise HTTPException(status_code=403, detail="Forbidden")

    db = get_db()
    now = datetime.now(timezone.utc)

    # --- step 2: check the rate limit cache table ---
    # the rate_limit table holds one row with id=1
    # if that row exists and available_at is in the future
    # return the same image that was last served
    rate_result = db.table("rate_limit").select("*").eq("id", 1).execute()

    if rate_result.data:
        row = rate_result.data[0]

        # parse the stored timestamp string into a timezone-aware datetime
        available_at_str: str = row["available_at"]
        available_at = datetime.fromisoformat(
            available_at_str.replace("Z", "+00:00")
        )

        if now < available_at:
            # still within the rate limit window
            # return the cached image without touching shown_banners
            cached_number: int = row["image_number"]
            return serve_image(cached_number)

    # --- step 3: get all image numbers already shown in this cycle ---
    shown_result = db.table("shown_banners").select("image_number").execute()
    shown_numbers = {r["image_number"] for r in shown_result.data}

    # --- step 4: compute which images are still unseen ---
    all_numbers = set(range(1, TOTAL_IMAGES + 1))
    unseen = list(all_numbers - shown_numbers)

    # --- step 5: if all 30 images have been shown reset the cycle ---
    if not unseen:
        # delete all rows from shown_banners to start a fresh cycle
        # filter gt 0 guarantees a valid filter since image_number is always >= 1
        db.table("shown_banners").delete().gt("image_number", 0).execute()
        unseen = list(all_numbers)

    # --- step 6: pick a random unseen image ---
    image_number = random.choice(unseen)

    # --- step 7: record this image as shown in the current cycle ---
    db.table("shown_banners").insert({"image_number": image_number}).execute()

    # --- step 8: update the rate limit cache row ---
    # upsert creates the row if id=1 does not exist or updates it if it does
    new_available_at = (now + timedelta(seconds=CACHE_SECONDS)).isoformat()
    db.table("rate_limit").upsert({
        "id": 1,
        "image_number": image_number,
        "available_at": new_available_at
    }).execute()

    # --- step 9: serve the image bytes ---
    return serve_image(image_number)


@app.get("/health")
async def health():
    # simple liveness check endpoint for debugging
    return {"status": "ok"}
```

---

## File: `README.md`

Use this template. Replace `YOUR_VERCEL_DOMAIN` and `YOUR_KEY`.

```markdown
![Banner](https://YOUR_VERCEL_DOMAIN.vercel.app/banner?key=YOUR_KEY)

# Your Project Name

rest of your README below...
```

**Important note about GitHub image caching:**
GitHub proxies all README images through its `camo` CDN. This means the banner image may be
cached for up to a few minutes. The banner will still rotate correctly - the next time GitHub
refreshes the cached image, the new one appears. There is no workaround for this within GitHub's
Markdown renderer.

---

## Logic Summary

```
Request arrives at /banner?key=VALUE
│
├── key wrong?        → 403 Forbidden
│
├── rate_limit row exists AND available_at > now?
│   └── YES → return cached image_number (no DB writes)
│
└── NO → pick new image
    │
    ├── fetch shown_banners image_number set
    ├── compute unseen = {1..30} minus shown set
    ├── unseen is empty? → DELETE shown_banners → reset unseen to {1..30}
    ├── pick random from unseen
    ├── INSERT image_number into shown_banners
    ├── UPSERT rate_limit row with new image_number and available_at = now+35s
    └── return image bytes as image/webp
```

---

## Constraints and Notes

- Images must be named `1.webp` through `30.webp` inside `src/img/`
- The `rate_limit` table always has at most one row (`id = 1`)
- The `shown_banners` table will have between 0 and 29 rows at any time
- RLS must be disabled on both tables (done in the schema SQL above)
- Vercel serverless functions are stateless. All state lives in Supabase
- The CACHE_SECONDS value of 35 covers both the 30-second rate limit window
  and the 5-second post-response timeout as a single combined guard
- The anon key is safe to use here because RLS is off and the tables only hold
  non-sensitive integer and timestamp data

---

## Testing Checklist

After deployment, verify the following manually:

1. `GET /health` returns `{"status": "ok"}`
2. `GET /banner` with no key returns HTTP 403
3. `GET /banner?key=wrongkey` returns HTTP 403
4. `GET /banner?key=CORRECT_KEY` returns a WebP image with HTTP 200
5. Two requests within 35 seconds return the same image bytes
6. After 35 seconds, a new request returns a different image
7. After 30 requests, the cycle resets and `shown_banners` is cleared
8. The `rate_limit` table always has exactly one row after the first valid request
