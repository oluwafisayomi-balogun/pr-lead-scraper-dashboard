"""Search Bluesky for posts that match the phrases in keywords.yaml.

Each matching post becomes a lead dict. This module only fetches and
reshapes data; saving leads is the database layer's job.

Run by hand from the project root:
    .venv/bin/python -m scraper.bluesky
"""

import os
from pathlib import Path

import requests
import yaml
from dotenv import load_dotenv

# bsky.social is the server that holds the account. Logged-in requests sent
# here are forwarded to Bluesky's search service.
API = "https://bsky.social/xrpc"

# Seconds to wait for any one request. Without a timeout, a server that
# never answers would hang the script forever.
TIMEOUT = 10

# The search endpoint's largest page size.
PAGE_SIZE = 100

# keywords.yaml sits next to this file, so build its path from here. That way
# the script works no matter which folder you run it from.
KEYWORDS_PATH = Path(__file__).parent / "keywords.yaml"


def login(handle: str, app_password: str) -> str:
    """Log in and return the access token (accessJwt)."""
    response = requests.post(
        f"{API}/com.atproto.server.createSession",
        json={"identifier": handle, "password": app_password},
        timeout=TIMEOUT,
    )
    # 401 means the handle or app password is wrong. Stop with a clear
    # message instead of failing later on a confusing search error.
    if response.status_code == 401:
        raise SystemExit("Bluesky login failed: check BLUESKY_HANDLE and BLUESKY_APP_PASSWORD in .env")
    # Any other 4xx or 5xx status raises an HTTPError here.
    response.raise_for_status()
    return response.json()["accessJwt"]


def search_phrase(token: str, phrase: str, max_pages: int) -> list[dict]:
    """Return the raw posts for one phrase, newest first, up to max_pages pages."""
    headers = {"Authorization": f"Bearer {token}"}
    posts = []
    cursor = None

    for _ in range(max_pages):
        params = {"q": phrase, "sort": "latest", "limit": PAGE_SIZE}
        # The first request has no cursor. Each later request sends back the
        # cursor from the previous page to get the next one.
        if cursor:
            params["cursor"] = cursor

        response = requests.get(
            f"{API}/app.bsky.feed.searchPosts",
            headers=headers,
            params=params,
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        posts.extend(data.get("posts", []))

        # No cursor in the response means there are no more pages.
        cursor = data.get("cursor")
        if not cursor:
            break

    return posts


def post_to_lead(post: dict, phrase: str) -> dict:
    """Turn one raw Bluesky post into a lead dict.

    Every collector returns this same shape, so storage and the dashboard
    don't need to know which platform a lead came from.
    """
    author = post["author"]
    handle = author["handle"]
    text = post["record"].get("text", "")

    # A post uri looks like at://did:plc:abc123/app.bsky.feed.post/3kxyz.
    # The last part (the rkey) is the post's id inside the web link.
    rkey = post["uri"].rsplit("/", 1)[-1]

    return {
        "platform": "bluesky",
        "post_id": post["uri"],
        "username": handle,
        # Not every account sets a display name.
        "display_name": author.get("displayName", ""),
        "text_preview": text[:280],
        "url": f"https://bsky.app/profile/{handle}/post/{rkey}",
        # createdAt is when the author wrote the post, as an ISO 8601 string.
        "created_at": post["record"].get("createdAt", ""),
        "matched_keyword": phrase,
    }


def collect(config: dict) -> list[dict]:
    """Log in once, search every phrase, and return all leads."""
    # Read the login from .env. A missing variable stops the script with a
    # message that names it, instead of a bare KeyError.
    handle = os.getenv("BLUESKY_HANDLE")
    app_password = os.getenv("BLUESKY_APP_PASSWORD")
    if not handle or not app_password:
        raise SystemExit("Set BLUESKY_HANDLE and BLUESKY_APP_PASSWORD in .env")

    # One login is enough for every search in this run.
    token = login(handle, app_password)
    max_pages = config["bluesky"]["max_pages"]

    leads = []
    for phrase in config["phrases"]:
        for post in search_phrase(token, phrase, max_pages):
            leads.append(post_to_lead(post, phrase))
    return leads


if __name__ == "__main__":
    # This block runs only when the file is run directly, not when another
    # module imports it.
    load_dotenv()  # copies the values in .env into os.environ
    with open(KEYWORDS_PATH) as f:
        config = yaml.safe_load(f)

    leads = collect(config)
    print(f"{len(leads)} leads")
    print(leads[0] if leads else "No leads found")
