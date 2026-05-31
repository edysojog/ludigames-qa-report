"""
UI Tests for play.ludigames.com
---------------------------------
These tests verify the browser experience using Playwright.
They simulate real user interactions: loading pages, searching for games,
and navigating to game and category pages.
"""

import pytest
from playwright.sync_api import expect

BASE_URL = "https://play.ludigames.com"

# Real product ID discovered from the gamelist API (Real Word Scramble)
VALID_GAME_PID = 8087

# Action category ID discovered by navigating to a category page
VALID_CAT_ID = 18547


def dismiss_cookie_popup(page):
    """
    Dismiss the Didomi cookie consent popup if it appears.
    It blocks all clicks until accepted.
    """
    try:
        agree_btn = page.locator("#didomi-notice-agree-button")
        if agree_btn.is_visible(timeout=5000):
            agree_btn.click()
            page.wait_for_timeout(1000)
    except:
        pass  # popup didn't appear, continue normally


# ---------------------------------------------------------------------------
# TC-UI-01: Homepage loads and game cards are visible
# Why: The most basic user expectation — landing on the site and seeing games.
#      If no game cards render, the entire portal is effectively broken.
# ---------------------------------------------------------------------------
def test_homepage_loads_with_game_cards(page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)
    dismiss_cookie_popup(page)

    # At least one game link should be visible on the homepage
    game_links = page.locator("a[href*='game.html?pID=']")
    assert game_links.count() > 0, "Expected at least one game card link on the homepage"


# ---------------------------------------------------------------------------
# TC-UI-02: Search for a known game returns the correct result
# Why: Search is a core feature users rely on to find specific games.
#      The search-btn link navigates to search.html where the #search input
#      is visible. Confirmed via DevTools: a.search-btn exists after networkidle.
# ---------------------------------------------------------------------------
def test_search_returns_correct_result(page):
    page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(5000)
    dismiss_cookie_popup(page)

    # Click the search icon link
    page.locator("a.search-btn").click()
    page.wait_for_timeout(2000)

    # Type in the search input
    search_input = page.locator("#search")
    expect(search_input).to_be_visible(timeout=10000)
    search_input.fill("pixelcraft")
    search_input.press("Enter")
    page.wait_for_timeout(2000)

    # "PixelCraft Parkour" should appear in the results
    result = page.get_by_text("PixelCraft Parkour", exact=False)
    expect(result).to_be_visible(timeout=10000)


# ---------------------------------------------------------------------------
# TC-UI-03: Search with empty input does not break the page
# Why: Edge case — opening the search bar and pressing enter without typing
#      should not crash the page or show an error state.
# ---------------------------------------------------------------------------
def test_search_empty_input_does_not_break_page(page):
    page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(5000)
    dismiss_cookie_popup(page)

    # Click the search icon link
    page.locator("a.search-btn").click()
    page.wait_for_timeout(2000)

    # Press enter without typing anything
    search_input = page.locator("#search")
    expect(search_input).to_be_visible(timeout=10000)
    search_input.press("Enter")
    page.wait_for_timeout(1000)

    # Page should still be alive — title should not be empty
    assert page.title() != "", "Search page should still render with empty query"


# ---------------------------------------------------------------------------
# TC-UI-04: Game page loads successfully for a valid product ID
# Why: Every game card on the site links to game.html?pID=<id>.
#      This verifies the game detail page renders without a blank screen.
# ---------------------------------------------------------------------------
def test_game_page_loads_for_valid_pid(page):
    url = f"{BASE_URL}/game.html?pID={VALID_GAME_PID}"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)

    # Page title should not be empty
    assert page.title() != "", "Game page should have a non-empty title"

    # The page body should have content
    body_text = page.locator("body").inner_text()
    assert len(body_text.strip()) > 0, "Game page body should not be empty"


# ---------------------------------------------------------------------------
# TC-UI-05: Category page loads and displays game cards
# Why: Category browsing is the main way users discover new games.
#      We verified catId=18547 is the Action category during research.
# ---------------------------------------------------------------------------
def test_category_page_loads_with_games(page):
    url = f"{BASE_URL}/category.html?catId={VALID_CAT_ID}"
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(2000)

    # Page should load without errors
    assert page.title() != "", "Category page should have a non-empty title"

    # Game links should be visible
    game_links = page.locator("a[href*='game.html?pID=']")
    assert game_links.count() > 0, "Category page should display at least one game"