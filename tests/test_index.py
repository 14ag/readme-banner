from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from api import index


class Result:
    def __init__(self, data):
        self.data = data


class FakeTable:
    def __init__(self, db, name):
        self.db = db
        self.name = name
        self.op = None
        self.payload = None

    def select(self, *_args):
        self.op = "select"
        return self

    def eq(self, *_args):
        return self

    def delete(self):
        self.op = "delete"
        return self

    def gt(self, *_args):
        return self

    def insert(self, payload):
        self.op = "insert"
        self.payload = payload
        return self

    def upsert(self, payload):
        self.op = "upsert"
        self.payload = payload
        return self

    def execute(self):
        if self.name == "rate_limit" and self.op == "select":
            return Result(self.db.rate)
        if self.name == "shown_banners" and self.op == "select":
            return Result([{"image_number": n} for n in self.db.shown])
        if self.name == "shown_banners" and self.op == "delete":
            self.db.shown.clear()
            self.db.deletes += 1
            return Result([])
        if self.name == "shown_banners" and self.op == "insert":
            self.db.shown.append(self.payload["image_number"])
            self.db.inserts += 1
            return Result([self.payload])
        if self.name == "rate_limit" and self.op == "upsert":
            self.db.rate = [self.payload]
            self.db.upserts += 1
            return Result([self.payload])
        return Result([])


class FakeDB:
    def __init__(self, rate=None, shown=None):
        self.rate = rate or []
        self.shown = shown or []
        self.inserts = 0
        self.upserts = 0
        self.deletes = 0

    def table(self, name):
        return FakeTable(self, name)


def client_with(monkeypatch, db):
    monkeypatch.setenv("BANNER_KEY", "secret")
    monkeypatch.setattr(index, "get_db", lambda: db)
    return TestClient(index.app)


def test_health_returns_ok(monkeypatch):
    client = client_with(monkeypatch, FakeDB())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_banner_rejects_missing_or_wrong_key(monkeypatch):
    client = client_with(monkeypatch, FakeDB())

    assert client.get("/banner").status_code == 403
    assert client.get("/banner?key=wrong").status_code == 403


def test_banner_returns_cached_image_within_rate_window(monkeypatch):
    future = (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat()
    db = FakeDB(rate=[{"id": 1, "image_number": 1, "available_at": future}])
    client = client_with(monkeypatch, db)

    response = client.get("/banner?key=secret")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
    assert response.content == (index.IMG_DIR / "1.webp").read_bytes()
    assert db.inserts == 0
    assert db.upserts == 0


def test_banner_picks_unseen_image_and_updates_state(monkeypatch):
    db = FakeDB(shown=[1, 2, 3])
    client = client_with(monkeypatch, db)
    monkeypatch.setattr(index.random, "choice", lambda choices: min(choices))

    response = client.get("/banner?key=secret")

    assert response.status_code == 200
    assert response.content == (index.IMG_DIR / "4.webp").read_bytes()
    assert db.shown == [1, 2, 3, 4]
    assert db.inserts == 1
    assert db.upserts == 1
    assert db.rate[0]["image_number"] == 4


def test_banner_resets_cycle_after_all_images_shown(monkeypatch):
    db = FakeDB(shown=list(range(1, index.TOTAL_IMAGES + 1)))
    client = client_with(monkeypatch, db)
    monkeypatch.setattr(index.random, "choice", lambda choices: min(choices))

    response = client.get("/banner?key=secret")

    assert response.status_code == 200
    assert response.content == (index.IMG_DIR / "1.webp").read_bytes()
    assert db.deletes == 1
    assert db.shown == [1]
