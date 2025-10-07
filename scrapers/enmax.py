from urllib.parse import urljoin

from bs4 import BeautifulSoup


def parse_enmax_job_list_from_html(html_str: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html_str, "html.parser")
    job_listings: list[dict] = []
    uls = soup.find_all("ul", {"role": "list"})
    target_uls = []
    for u in uls:
        aria = u.get("aria-label", "")
        if "Page" in aria or u.find("a", {"data-automation-id": "jobTitle"}):
            target_uls.append(u)
    if not target_uls:
        candidates = soup.select("ul a[data-automation-id='jobTitle']")
        if candidates:
            for a in candidates:
                parent_ul = a.find_parent("ul")
                if parent_ul and parent_ul not in target_uls:
                    target_uls.append(parent_ul)

    for ul in target_uls:
        for li in ul.find_all("li", recursive=False):
            try:
                a = li.find("a", {"data-automation-id": "jobTitle"})
                title = a.get_text(strip=True) if a else li.get_text(strip=True)
                href = a.get("href") if a else None
                url = urljoin(base_url, href)

                loc_dd = li.select_one("[data-automation-id='locations'] dd") 
                location = loc_dd.get_text(separator=" ", strip=True) if loc_dd else "Location not specified"

                posted_dd = li.select_one("[data-automation-id='postedOn'] dd")
                posted_on = posted_dd.get_text(separator=" ", strip=True) if posted_dd else None

                job_id_li = li.select_one("ul[data-automation-id='subtitle'] li")
                job_id = job_id_li.get_text(strip=True) if job_id_li else None

                job_listings.append({
                    "title": title,
                    "url": url,
                    "location": location,
                    "posted_on": posted_on,
                    "job_id": job_id
                })
            except Exception as e:
                print(e)
                continue

    return job_listings
