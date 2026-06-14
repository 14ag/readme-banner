import os
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Response

from data import Database


# load env vars from .env in local dev
load_dotenv()

app = FastAPI()

# path to the images folder relative to this file
IMG_DIR = Path(__file__).parents[1] / "src" / "img"

# total number of banner images in src/img
TOTAL_IMAGES = len(list(IMG_DIR.glob("*.webp")))

# combined window in seconds: 30s rate limit + 5s post-response timeout
CACHE_SECONDS = 35


host = os.environ.get("REDIS_DATA_HOST")
port = os.environ.get("REDIS_DATA_PORT")
username= os.environ.get("REDIS_DATA_USERNAME")
password = os.environ.get("REDIS_DATA_PASSWORD")
db = Database(host,port,username,password)

def serve_image(image_number: int) -> Response:
    # build absolute path for the requested image
    img_path = IMG_DIR / f"{image_number}.webp"

    # return 404 if the file is somehow missing
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")

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


def verify_banner_header(x_banner_key: str) -> None:
    expected_key = os.environ.get("BANNER_KEY", "")
    if not x_banner_key or x_banner_key != expected_key:
        raise HTTPException(status_code=403, detail="Forbidden")


@app.get("/banner")
async def get_banner(
    key: str = "",
    x_banner_key: str = Header(default="", alias="X-Banner-Key"),
) -> Response:
    # --- step 1: verify the api key ---
    expected_key = os.environ.get("BANNER_KEY", "")
    provided_key = x_banner_key or key
    if not provided_key or provided_key != expected_key:
        raise HTTPException(status_code=403, detail="Forbidden")

    
    db_data = db.get_data()

    now = datetime.now(timezone.utc)

    # --- step 2: check the rate limit cache table ---
    # the rate_limit table holds one row with id=1
    # if that row exists and available_at is in the future
    # return the same image that was last served
    rate_result = db_data["rate_limit"]

    if rate_result:

        # parse the stored timestamp string into a timezone-aware datetime
        available_at_str: str = rate_result["available_at"]
        available_at = datetime.fromisoformat(
            available_at_str.replace("Z", "+00:00")
        )

        if now < available_at:
            # still within the rate limit window
            # return the cached image without touching shown_banners
            cached_number: int = rate_result["image_number"]
            return serve_image(cached_number)

    # --- step 3: get all image numbers already shown in this cycle ---
    shown_numbers = [i[image_number] for i in db_data["show_banners"]]

    # --- step 4: compute which images are still unseen ---
    all_numbers = set(range(1, TOTAL_IMAGES + 1))
    unseen = list(all_numbers - shown_numbers)

    # --- step 5: if all 30 images have been shown reset the cycle ---
    if not unseen:
        # delete all rows from shown_banners to start a fresh cycle
        db_data["show_banners"]=[]
        unseen = list(all_numbers)

    # --- step 6: pick a random unseen image ---
    image_number = random.choice(unseen)

    # --- step 7: record this image as shown in the current cycle ---
    db_data["shown_banners"].append({"image_number": image_number})

    # --- step 8: update the rate limit cache row ---
    # upsert creates the row if id=1 does not exist or updates it if it does
    new_available_at = (now + timedelta(seconds=CACHE_SECONDS)).isoformat()
    db_data["rate_limit"][0] = {
        "image_number": image_number,
        "available_at": new_available_at
    }

    # --- step 9: serve the image bytes ---
    return serve_image(image_number), db.set_data(db_data)


@app.post("/reset")
async def reset_banner_cycle(
    x_banner_key: str = Header(default="", alias="X-Banner-Key"),
):
    verify_banner_header(x_banner_key)

    db_data = db.get_data()
    db_data["show_banners"]=[]
    db_data["rate_limit"][0] = {}
    db.set_data(db_data)

    return {"status": "ok", "reset": True}


@app.get("/health")
async def health():
    # simple liveness check endpoint for debugging
    return {"status": "ok"}
