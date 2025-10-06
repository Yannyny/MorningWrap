from typing import Optional, List, Dict
from bs4 import BeautifulSoup
from utils import generate_summary_with_ai
from playwright.sync_api import sync_playwright

LISTING_URL = "https://enmax.wd3.myworkdayjobs.com/en-US/ENMAXCareers/jobs"
USER_AGENT = "MorningWrap/1.0 (+https://github.com/Yannyny/MorningWrap)"

def render_page_html(url: str, headless: bool = True, wait_ms: int = 1500) -> Optional[str]:
    """Render the URL with Playwright and return page HTML (rendered)."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            page.set_extra_http_headers({"User-Agent": USER_AGENT})
            page.goto(url, timeout=60000)
            page.wait_for_timeout(wait_ms)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        print("Playwright render failed:", e)
        return None

def parse_enmax_job_list_from_html(html: str) -> List[Dict]:
    """
    Parse the rendered ENMAX listing HTML and return a list of job dicts:
      { title, href, location, posted_on, job_id }
    """
    soup = BeautifulSoup(html, "html.parser")
    out: List[Dict] = []

    # Find the ul with aria-label "Page 1 of 1" and role="list" (robust: find all matching ULs)
    uls = soup.find_all("ul", {"role": "list"})
    target_uls = []
    for u in uls:
        aria = u.get("aria-label", "")
        # pick the UL that matches the visible pagination label OR contains job items
        if "Page" in aria or u.find("a", {"data-automation-id": "jobTitle"}):
            target_uls.append(u)

    if not target_uls:
        # fallback: any ul that contains anchors with data-automation-id jobTitle
        candidates = soup.select("ul a[data-automation-id='jobTitle']")
        if candidates:
            # get parent ul(s)
            for a in candidates:
                parent_ul = a.find_parent("ul")
                if parent_ul and parent_ul not in target_uls:
                    target_uls.append(parent_ul)

    for ul in target_uls:
        # iterate direct li children to avoid nested lists
        for li in ul.find_all("li", recursive=False):
            try:
                # Title + href (anchor with data-automation-id="jobTitle")
                a = li.find("a", {"data-automation-id": "jobTitle"})
                title = a.get_text(strip=True) if a else li.get_text(strip=True)
                href = a.get("href") if a else None

                # Location: look for dl/dd under div with data-automation-id="locations"
                loc_dd = li.select_one("[data-automation-id='locations'] dd")  # CSS: dd inside the locations block
                location = loc_dd.get_text(separator=" ", strip=True) if loc_dd else "Location not specified"

                # Posted on: similar structure
                posted_dd = li.select_one("[data-automation-id='postedOn'] dd")
                posted_on = posted_dd.get_text(separator=" ", strip=True) if posted_dd else None

                # Job id: under ul[data-automation-id="subtitle"] > li
                job_id_li = li.select_one("ul[data-automation-id='subtitle'] li")
                job_id = job_id_li.get_text(strip=True) if job_id_li else None

                out.append({
                    "title": title,
                    "href": href,
                    "location": location,
                    "posted_on": posted_on,
                    "job_id": job_id
                })
            except Exception as e:
                # skip problematic items but keep processing others
                print(e)
                continue

    return out

def main():
    print("Generating your daily ENMAX jobs review...")
    rendered_html = render_page_html(LISTING_URL, headless=True, wait_ms=1800)
    if not rendered_html:
        print("Could not render listing page; aborting.")
        return

    job_listings = parse_enmax_job_list_from_html(rendered_html)

    # small sanity output
    print(f"Found {len(job_listings)} jobs (grouped by sections).")

    for j in job_listings:
        print(f"Title: {j['title']}, Location: {j['location']}, URL: {j['href']}")

    print("\n=============================================")
    print("✨ ENMAX JOBS REVIEW ✨")
    print("=============================================\n")

    # Summarize each job using your LLM helper
    for idx, job in enumerate(job_listings, start=1):
        title = job["title"]
        href = job["href"]
        print(f"Job n°{idx}:")
        # pass the job's href (not the listing url) and job['soup']
        summary = generate_summary_with_ai(title, href)
        print(f"📰 Title: {title}")
        print(f"📍 Location: {job['location']}")
        print(f"🔗 Link: {href}")
        print(f"📝 AI Summary: {summary}\n")
        print("---------------------------------------------\n")

if __name__ == "__main__":
    main()
