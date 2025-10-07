from utils import fetch_careers_html, log_jobs, logger
from scrapers.orennia import parse_orennia_job_list_from_html

URL = "https://orennia.com/careers"
BASE = "https://orennia.com"

def main():
    logger.info("Generating your daily Orennia jobs review...")
    html = fetch_careers_html(URL, render=False)   # static site, no JS render
    if not html:
        logger.error("Could not fetch %s", URL)
        return

    jobs = parse_orennia_job_list_from_html(html, base_url=BASE)

    logger.info("=============================================")
    logger.info("✨ ORENNIA JOBS REVIEW ✨")
    logger.info("=============================================")
    logger.info("Found %d job(s)", len(jobs))

    log_jobs(jobs)

if __name__ == "__main__":
    main()
