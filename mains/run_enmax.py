from utils import fetch_careers_html, log_jobs, logger
from scrapers.enmax import parse_enmax_job_list_from_html

URL = "https://enmax.wd3.myworkdayjobs.com/en-US/ENMAXCareers/jobs"
BASE = "https://enmax.wd3.myworkdayjobs.com"

def main():
    logger.info("Generating your daily ENMAX jobs review...")
    html = fetch_careers_html(URL, render=True)   # render True because this is Workday
    if not html:
        logger.error("Could not fetch %s", URL)
        return

    jobs = parse_enmax_job_list_from_html(html, base_url=BASE)

    logger.info("=============================================")
    logger.info("✨ ENMAX JOBS REVIEW ✨")
    logger.info("=============================================")
    logger.info("Found %d job(s)", len(jobs))

    log_jobs(jobs)

if __name__ == "__main__":
    main()

