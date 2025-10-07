from typing import List, Dict
from bs4 import BeautifulSoup
from utils import fetch_careers_html, print_jobs


url = "https://enmax.wd3.myworkdayjobs.com/en-US/ENMAXCareers/jobs"
    
def parse_enmax_job_list_from_html(html: str) -> List[Dict]:
    """
    Parse the rendered ENMAX listing HTML and return a list of job dicts:
      { title, href, location, posted_on, job_id }
    """
    soup = BeautifulSoup(html, "html.parser")
    out: List[Dict] = []

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

                loc_dd = li.select_one("[data-automation-id='locations'] dd") 
                location = loc_dd.get_text(separator=" ", strip=True) if loc_dd else "Location not specified"

                posted_dd = li.select_one("[data-automation-id='postedOn'] dd")
                posted_on = posted_dd.get_text(separator=" ", strip=True) if posted_dd else None

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
                print(e)
                continue

    return out

def main():
    print("Generating your daily ENMAX jobs review...")
    rendered_html = fetch_careers_html(url, static=False)
    if not rendered_html:
        print("Could not render listing page; aborting.")
        return
    job_listings = parse_enmax_job_list_from_html(rendered_html)
    print("\n=============================================")
    print("✨ ENMAX JOBS REVIEW ✨")
    print("=============================================\n")
    print(f"Found {len(job_listings)} job(s).")
    print_jobs(job_listings)

if __name__ == "__main__":
    main()
