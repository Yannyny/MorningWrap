from typing import List, Dict
import time
from utils import fetch_job_page, fetch_careers_html, print_jobs

def parse_orennia_job_list_from_html(html: str) -> List[Dict]:
    job_listings: List[Dict] = []

    for section in html.find_all('section'):
        category = section.find('h3')
        if category:
            category_name = category.get_text(strip=True)
            jobs = section.find_all('a', href=True)
            for job in jobs:
                title = job.get_text(strip=True)
                location = job.find_next('ul').get_text(separator=' ', strip=True) if job.find_next('ul') else 'Location not specified'
                href = job.get('href')
                job_soup = fetch_job_page(href) if href else None
                time.sleep(0.6)
                job_listings.append({
                    'category': category_name,
                    'title': title,
                    'location': location,
                    'href': href,
                    'soup': job_soup
                })
    return job_listings

def main():
    """Main function to generate and print the Orennia jobs review."""
    url = "https://orennia.com/careers"
    print("Generating your daily Orennia jobs review...")
    html = fetch_careers_html(url)
    job_listings = parse_orennia_job_list_from_html(html)
    print("\n=============================================")
    print("✨ ORENNIA JOBS REVIEW ✨")
    print("=============================================\n")
    print(f"Found {len(job_listings)} job(s).")
    print_jobs(job_listings)

if __name__ == "__main__":
    main()