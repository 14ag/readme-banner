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
