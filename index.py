import os
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Response

from api.data import Database


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


def initialize(x):
    repo_name=x
    pass
    


@app.get("/banner")
async def get_banner(
    repo_name: str= Header(default="readme-banner",alias="repo-name"),
    x_banner_key: str = Header(default="", alias="X-Banner-Key")
) -> Response:
    # --- step 1: verify the api key ---
    verify_banner_header(x_banner_key)

    db_data = db.get_data()
    
    rate_result = db_data["rate_limit"]

    available_at_str: str = rate_result[repo_name].setdefault(repo_name,datetime.now(timezone.utc).isoformat())

    available_at = datetime.fromisoformat(
        available_at_str.replace("Z", "+00:00")
        )
    
    now = datetime.now(timezone.utc)
    if now < available_at:
        raise HTTPException(status_code=403, detail="rate limit")
    
    new_available_at = (now + timedelta(seconds=CACHE_SECONDS)).isoformat()

    # --- update the rate limit ---
    db_data["rate_limit"].update({repo_name:new_available_at})
    
    shown_numbers = db_data["show_banners"]
    all_numbers = set(range(1, TOTAL_IMAGES + 1))
    unseen = list(all_numbers - shown_numbers)

    # --- if all 30 images have been shown reset the cycle ---
    if not unseen:
        unseen =  list(all_numbers)
    
    # --- pick a random unseen image record this image as shown in the current cycle ---
    image_number = random.choice(unseen)        
    db_data["shown_banners"].append(image_number)

    # --- serve the image update db ---
    db.set_data(db_data)
    return serve_image(image_number)


@app.post("/reset")
async def reset_banner_cycle(
    repo_name: str= Header(default="readme-banner",alias="repo-name"),
    x_banner_key: str = Header(default="", alias="X-Banner-Key"),
):
    verify_banner_header(x_banner_key)
    db_data=db.get_data()
    db_data["shown_banners"].clear()
    db_data["rate_limit"].update({repo_name:datetime.now(timezone.utc).isoformat()})
    db.set_data(db_data)

    return {"status": "ok", "reset": True}


@app.get("/health")
async def health():
    # simple liveness check endpoint for debugging
    return {"status": "ok"}
