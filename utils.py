import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("morningwrap")
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "MorningWrap/1.0 (+https://github.com/Yannyny/MorningWrap)"})

def fetch_careers_html(url: str, render: bool = False) -> str | None:
    """
    Return raw HTML string. If render=True, use Playwright to get rendered HTML.
    """
    if not render:
        try:
            resp = SESSION.get(url, timeout=15)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            logger.warning("Failed to fetch careers page %s: %s", url, e)
            return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers(SESSION.headers)
            page.goto(url, timeout=60000)
            page.wait_for_timeout(1500)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        logger.warning("Playwright render failed: %s", e)
        return None

def fetch_job_page(href: str, base_url: str = "") -> BeautifulSoup | None:
    if not href:
        return None
    try:
        full = urljoin(base_url, href)
        r = SESSION.get(full, timeout=15)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except requests.RequestException as e:
        logger.warning("fetch_job_page failed for %s: %s", href, e)
        return None

def safe_truncate_text(soup: BeautifulSoup | None, max_chars: int = 10000) -> str:
    if soup is None:
        return ""
    try:
        text = soup.get_text(separator=" ", strip=True)
        return text if len(text) <= max_chars else text[:max_chars] + " [TRUNCATED]"
    except Exception:
        return ""

def log_job(job, idx):
    from summarizer import generate_summary_with_ai

    title = job['title']
    url = job.get('url')
    summary = generate_summary_with_ai(title, url, job.get('soup'))
    lines = [
        "---------------------------------------------",
        f"Job n°{idx}",
        f"📰 Title: {title}",
        f"📍 Location: {job.get('location', 'N/A')}",
        f"🔗 Link: {url or 'N/A'}"
    ]

    if job.get('category'):
        lines.append(f"🔖 Category: {job['category']}")
    if job.get('posted_on'):
        lines.append(f"📅 Posted on: {job['posted_on']}")

    lines.append(f"📝 AI Summary: {summary}")
    lines.append("---------------------------------------------")
    logger.info("\n".join(lines))


def log_jobs(job_listings):
    for idx, job in enumerate(job_listings, start=1):
        log_job(job, idx)