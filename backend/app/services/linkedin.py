import asyncio
import json
from playwright.async_api import BrowserContext, Page
from .browser import create_browser_context, save_cookies


async def linkedin_login(
    user_id: str,
    email: str,
    password: str,
    proxy_config: dict,
    existing_cookies: list | None = None,
) -> tuple[bool, list]:
    context = await create_browser_context(user_id, proxy_config, existing_cookies)
    page = await context.new_page()
    try:
        await page.goto("https://www.linkedin.com/login", wait_until="networkidle", timeout=30000)

        # Check if already logged in
        if "feed" in page.url or "mynetwork" in page.url:
            cookies = await save_cookies(context)
            await page.close()
            return True, cookies

        await page.fill("#username", email)
        await page.fill("#password", password)
        await page.click('[data-litms-control-urn="login-submit"]')
        await page.wait_for_url("**/feed/**", timeout=15000)

        cookies = await save_cookies(context)
        await page.close()
        return True, cookies
    except Exception:
        await page.close()
        return False, []


async def search_linkedin_jobs(
    context: BrowserContext,
    keywords: list[str],
    location: str | None = None,
    max_results: int = 25,
) -> list[dict]:
    query = " ".join(keywords)
    location_param = location or ""
    url = (
        f"https://www.linkedin.com/jobs/search/"
        f"?keywords={query}&location={location_param}&f_TPR=r86400"
    )
    page = await context.new_page()
    jobs = []
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_selector(".jobs-search__results-list", timeout=15000)

        # Scroll to load more
        for _ in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)

        job_cards = await page.query_selector_all(".jobs-search__results-list li")
        for card in job_cards[:max_results]:
            try:
                title_el = await card.query_selector(".base-search-card__title")
                company_el = await card.query_selector(".base-search-card__subtitle")
                location_el = await card.query_selector(".job-search-card__location")
                link_el = await card.query_selector("a.base-card__full-link")
                time_el = await card.query_selector("time")

                title = await title_el.inner_text() if title_el else ""
                company = await company_el.inner_text() if company_el else ""
                loc = await location_el.inner_text() if location_el else ""
                url_val = await link_el.get_attribute("href") if link_el else ""
                posted = await time_el.get_attribute("datetime") if time_el else ""

                # Extract job ID from URL
                job_id = ""
                if url_val and "currentJobId=" in url_val:
                    job_id = url_val.split("currentJobId=")[1].split("&")[0]
                elif url_val and "/jobs/view/" in url_val:
                    job_id = url_val.split("/jobs/view/")[1].split("/")[0]

                description = ""
                if url_val:
                    desc_page = await context.new_page()
                    try:
                        await desc_page.goto(url_val, wait_until="networkidle", timeout=20000)
                        desc_el = await desc_page.query_selector(".description__text")
                        if desc_el:
                            description = await desc_el.inner_text()
                    except Exception:
                        pass
                    finally:
                        await desc_page.close()

                if title:
                    jobs.append({
                        "linkedin_job_id": job_id,
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": loc.strip(),
                        "description": description.strip(),
                        "url": url_val,
                        "posted_at": posted,
                    })
            except Exception:
                continue
    except Exception:
        pass
    finally:
        await page.close()
    return jobs
