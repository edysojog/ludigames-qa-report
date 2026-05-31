import pytest
from playwright.sync_api import sync_playwright

BASE_URL = "https://play.ludigames.com"
CDN_URL = "https://cdn.ludigames.com"
API_URL = f"{BASE_URL}/ludiapi"

# Category and game IDs discovered during research
VALID_CAT_IDS = "18575,18571,18854,19023,21317"
VALID_GAME_PID = 8087           # Real Word Scramble
VALID_GAME_KEY = "pixelcraftParkourFree"
VALID_CAT_ID = 18547            # Action category


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
    page = context.new_page()
    yield page
    context.close()
