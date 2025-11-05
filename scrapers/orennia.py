import time

from bs4 import BeautifulSoup

# from utils import fetch_job_page

def parse_orennia_job_list_from_html(html_str: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html_str, "html.parser")
    job_listings: list[dict] = []

    for section in soup.find_all('section'):
        h2 = section.find("h2")
        if h2 and h2.get_text(strip=True).lower() == "explore opportunities":
            category = section.find('h3')
            if category:
                category_name = category.get_text(strip=True)
                jobs = section.find_all('a', href=True)
                for job in jobs:
                    title = job.get_text(strip=True)
                    location = job.find_next('ul').get_text(separator=' ', strip=True) if job.find_next('ul') else 'Location not specified'
                    href = job.get('href')
                    time.sleep(0.6)
                    job_listings.append({
                        'category': category_name,
                        'title': title,
                        'location': location,
                        'url': href,
                    })
    return job_listings
