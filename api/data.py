import json
import redis
from typing import Dict, Any, Optional

class Database:
    """Simple Redis-backed storage for the readme-banner data."""
    client: redis.Redis

    def __init__(self, host: str, port: int, username: Optional[str], password: Optional[str]) -> None:
        self.client = redis.Redis(
            host=host,
            port=port,
            username=username,
            password=password,
            decode_responses=True
        )
        # Initialize key atomically: set only if it does not exist
        #self.client.set("readme-banner", json.dumps(), nx=True)

    def get_data(self) -> Dict[str, Any]:
        
        if not self.client.exists("readme-banner"):
            data=dict(
                shown_banners=set(),
                rate_limit=dict()
                )
        else:
            raw_data=self.client.get("readme-banner")
            data = json.loads(raw_data)
            shown_banner_set=set(data["shown_banners"])
            data.update({"shown_banners":shown_banner_set})
        
        return data

    def set_data(self, data: Dict[str, Any]) -> None:
        shown_banner_arr=list(str(i) for i in data["shown_banners"])
        data.update({"shown_banners":shown_banner_arr})
        self.client.set("readme-banner", json.dumps(data))


    def close(self) -> None:
        """Close underlying Redis client connections."""
        try:
            self.client.close()
        except Exception:
            # best-effort close; ignore errors during shutdown
            pass

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


