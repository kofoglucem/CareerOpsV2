import asyncio
import json
from playwright.async_api import async_playwright, Browser, BrowserContext
from typing import Optional

# Active browser contexts keyed by user_id
_contexts: dict[str, BrowserContext] = {}
_playwright_instance = None


async def get_playwright():
    global _playwright_instance
    if _playwright_instance is None:
        _playwright_instance = await async_playwright().start()
    return _playwright_instance


async def create_browser_context(
    user_id: str,
    proxy_config: dict | None = None,
    cookies: list | None = None,
) -> BrowserContext:
    pw = await get_playwright()
    launch_args = {
        "headless": True,
        "args": ["--no-sandbox", "--disable-dev-shm-usage"],
    }
    if proxy_config:
        launch_args["proxy"] = {
            "server": f"http://{proxy_config['server']}:{proxy_config['port']}",
            "username": proxy_config["username"],
            "password": proxy_config["password"],
        }
    browser: Browser = await pw.chromium.launch(**launch_args)
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800},
    )
    if cookies:
        await context.add_cookies(cookies)
    _contexts[user_id] = context
    return context


async def get_context(user_id: str) -> BrowserContext | None:
    return _contexts.get(user_id)


async def close_context(user_id: str):
    ctx = _contexts.pop(user_id, None)
    if ctx:
        await ctx.close()


async def save_cookies(context: BrowserContext) -> list:
    return await context.cookies()
