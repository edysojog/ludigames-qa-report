"""
API Tests for play.ludigames.com
---------------------------------
These tests verify the behavior of the gamelist API and CDN endpoints
discovered through DevTools research during manual exploration of the site.
"""

import requests
import pytest

BASE_URL = "https://play.ludigames.com"
CDN_URL = "https://cdn.ludigames.com"
API_ENDPOINT = f"{BASE_URL}/ludiapi/gamelist.php"

# Category IDs loaded by the homepage (discovered via DevTools Network tab)
VALID_CAT_IDS = "18575,18571,18854,19023,21317"

# A known valid game key from the gamelist API response
VALID_GAME_KEY = "pixelcraftParkourFree"

# Required fields every game object must have
REQUIRED_GAME_FIELDS = {"name", "product_id", "product_key", "isPortrait", "assets"}

# The API requires a Referer header — it only accepts requests originating
# from the site itself (discovered when bare requests returned 403)
HEADERS = {
    "Referer": "https://play.ludigames.com/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


# ---------------------------------------------------------------------------
# TC-API-01: Valid category IDs return HTTP 200 with non-empty JSON
# Why: This is the core API call the homepage depends on. If it breaks,
#      no games are shown to any user.
# ---------------------------------------------------------------------------
def test_valid_cat_ids_return_200_with_data():
    response = requests.get(
        API_ENDPOINT,
        params={"cat_id": VALID_CAT_IDS, "orderByRank": ""}, headers=HEADERS
    )
    assert response.status_code == 200, "Expected HTTP 200 for valid category IDs"
    data = response.json()
    assert isinstance(data, dict), "Response should be a JSON object"
    assert len(data) > 0, "Response should not be empty for valid category IDs"


# ---------------------------------------------------------------------------
# TC-API-02: Each game object contains all required fields
# Why: If any required field is missing, the frontend will break when trying
#      to render game cards (no name, no thumbnail key, no orientation info).
# ---------------------------------------------------------------------------
def test_each_game_has_required_fields():
    response = requests.get(
        API_ENDPOINT,
        params={"cat_id": VALID_CAT_IDS, "orderByRank": ""}, headers=HEADERS
    )
    data = response.json()

    for cat_id, games in data.items():
        assert isinstance(games, list), f"Category {cat_id} should contain a list of games"
        for game in games:
            missing = REQUIRED_GAME_FIELDS - game.keys()
            assert not missing, (
                f"Game '{game.get('name', 'unknown')}' in category {cat_id} "
                f"is missing fields: {missing}"
            )


# ---------------------------------------------------------------------------
# TC-API-03: product_id is always an integer, isPortrait is always a boolean
# Why: Type mismatches cause silent bugs on the frontend — a string product_id
#      breaks URL generation, a non-boolean isPortrait breaks layout logic.
# ---------------------------------------------------------------------------
def test_game_field_types_are_correct():
    response = requests.get(
        API_ENDPOINT,
        params={"cat_id": VALID_CAT_IDS, "orderByRank": ""}, headers=HEADERS
    )
    data = response.json()

    for cat_id, games in data.items():
        for game in games:
            assert isinstance(game["product_id"], int), (
                f"product_id should be int, got {type(game['product_id'])} "
                f"for game '{game['name']}'"
            )
            assert isinstance(game["isPortrait"], bool), (
                f"isPortrait should be bool, got {type(game['isPortrait'])} "
                f"for game '{game['name']}'"
            )


# ---------------------------------------------------------------------------
# TC-API-04: Invalid cat_id values return an empty object, not an error
# Why: Robustness check — the API should handle bad input gracefully
#      instead of crashing with a 500 error or returning malformed data.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("bad_cat_id", ["-1", "abc", "99999999"])
def test_invalid_cat_id_returns_empty_object(bad_cat_id):
    response = requests.get(
        API_ENDPOINT,
        params={"cat_id": bad_cat_id, "orderByRank": ""}, headers=HEADERS
    )
    assert response.status_code == 200, (
        f"Expected HTTP 200 even for invalid cat_id '{bad_cat_id}', "
        f"got {response.status_code}"
    )
    data = response.json()
    assert data == {}, (
        f"Expected empty object {{}} for invalid cat_id '{bad_cat_id}', got: {data}"
    )


# ---------------------------------------------------------------------------
# TC-API-05: Missing cat_id parameter returns 200 without crashing
# Why: The API should not crash when a required parameter is omitted.
#      We discovered it returns a status wrapper object instead of {}, which
#      is still valid — what matters is it doesn't return a 500 error.
# ---------------------------------------------------------------------------
def test_missing_cat_id_returns_200():
    response = requests.get(API_ENDPOINT, params={"orderByRank": ""}, headers=HEADERS)
    assert response.status_code == 200, "Expected HTTP 200 even with missing cat_id"
    data = response.json()
    assert isinstance(data, dict), "Expected a JSON object response for missing cat_id"


# ---------------------------------------------------------------------------
# TC-API-06: orderByRank parameter does not affect game order
# Why: During research we found that orderByRank= and orderByRank=true
#      return identical results. This test documents and locks in that behavior
#      so any future change is caught immediately.
# ---------------------------------------------------------------------------
def test_order_by_rank_does_not_change_results():
    response_default = requests.get(
        API_ENDPOINT,
        params={"cat_id": "18575,18571", "orderByRank": ""}, headers=HEADERS
    )
    response_ranked = requests.get(
        API_ENDPOINT,
        params={"cat_id": "18575,18571", "orderByRank": "true"}, headers=HEADERS
    )

    assert response_default.status_code == 200
    assert response_ranked.status_code == 200

    data_default = response_default.json()
    data_ranked = response_ranked.json()

    assert data_default == data_ranked, (
        "orderByRank=true should return the same results as orderByRank="
    )


# ---------------------------------------------------------------------------
# TC-API-07: Valid game key returns HTTP 200 with JSON from CDN
# Why: Each game page loads its data from cdn.ludigames.com/h5/{key}/data.json.
#      If this endpoint is down or broken, the game simply won't load.
# ---------------------------------------------------------------------------
def test_valid_game_cdn_data_returns_200():
    url = f"{CDN_URL}/h5/{VALID_GAME_KEY}/data.json"
    response = requests.get(url, headers=HEADERS)
    assert response.status_code == 200, (
        f"Expected HTTP 200 for CDN data.json of '{VALID_GAME_KEY}', "
        f"got {response.status_code}"
    )
    data = response.json()
    assert data is not None, "CDN data.json should return valid JSON"


# ---------------------------------------------------------------------------
# TC-API-08: Non-existent game key returns HTTP 404 from CDN
# Why: Verifies the CDN handles missing resources correctly and returns
#      a proper 404 rather than serving a default/wrong game's data.
# ---------------------------------------------------------------------------
def test_fake_game_cdn_data_returns_404():
    url = f"{CDN_URL}/h5/thisGameDefinitelyDoesNotExistFree/data.json"
    response = requests.get(url, headers=HEADERS)
    assert response.status_code == 404, (
        f"Expected HTTP 404 for non-existent game on CDN, "
        f"got {response.status_code}"
    )