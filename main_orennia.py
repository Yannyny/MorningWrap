from typing import Optional, List, Dict
import time
import requests
from bs4 import BeautifulSoup
from utils import generate_summary_with_ai, fetch_job_page

def main():
    """Main function to generate and print the Orennia jobs review."""
    url = "https://orennia.com/careers"
    print("Generating your daily Orennia jobs review...")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except requests.RequestException as e:
        print(f"Failed to fetch careers page %s: %s", url, e)
        return
    
    job_listings: List[Dict] = []

    for section in soup.find_all('section'):
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

    for job in job_listings:
        print(f"Category: {job['category']}, Title: {job['title']}, Location: {job['location']}, URL: {job['href']}")
        if job['soup']:
            print(f"Job page soup available with {len(job['soup'].text)} characters of text\n")

    print("\n=============================================")
    print("✨ ORENNIA JOBS REVIEW ✨")
    print("=============================================\n")

    job_nb = 1
    for job in job_listings:
        title = job['title']
        href = job['href']
        print(f"Job n°{job_nb}:")
        summary = generate_summary_with_ai(title, url, job['soup'])
        print(f"🔖 Category: {job['category']}")
        print(f"📰 Title: {title}")
        print(f"📍 Location: {job['location']}")
        print(f"🔗 Link: {href}")
        print(f"📝 AI Summary: {summary}\n")
        print("---------------------------------------------\n")
        job_nb += 1

if __name__ == "__main__":
    main()