from typing import Optional
import ollama
import logging
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

AI_MODEL = 'mistral'

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("morningwrap")

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "MorningWrap/1.0 (+https://github.com/Yannyny/MorningWrap)"})

def print_jobs(job_listings):
    for idx, job in enumerate(job_listings, start=1):
        print(f"Job n°{idx}:")
        title = job['title']
        href = job['href']
        summary = generate_summary_with_ai(title, href, job.get('soup'))
        print(f"📰 Title: {title}")
        print(f"📍 Location: {job['location']}")
        print(f"🔗 Link: {href}")
        if job.get('category'):
            print(f"🔖 Category: {job['category']}")
        if job.get('posted_on'):
            print(f"📅 Posted on: {job['posted_on']}")
        print(f"📝 AI Summary: {summary}\n")
        print("---------------------------------------------\n")

def fetch_careers_html(url, static=True) -> Optional[str]:
    """Either get static HTML from request or render the URL with Playwright before returning page HTML (rendered page)."""
    if static:
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            return soup
        except requests.RequestException as e:
            print(f"Failed to fetch careers page %s: %s", url, e)
            return
    else:
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
            print("Playwright render failed:", e)
            return None

def fetch_job_page(href: str, base_url: str = "") -> Optional[BeautifulSoup]:
    """Return BeautifulSoup or None. Ensures absolute URL using base_url."""
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

def safe_truncate_text(soup: Optional[BeautifulSoup], max_chars: int = 10000) -> str:
    if soup is None:
        return ""
    try:
        text = soup.get_text(separator=" ", strip=True)
        return text if len(text) <= max_chars else text[:max_chars] + " [TRUNCATED]"
    except Exception:
        return ""

def generate_summary_with_ai(title: str, url: str, soup: Optional[BeautifulSoup] = None, model: str = AI_MODEL) -> str:
    """
    Generate a concise, structured summary for a job posting using the local Ollama model.

    Returns a JSON string with keys:
      - summary: 2-3 concise sentences (what the job is and core skills)
      - skills: comma-separated list of required/important skills
      - fit: short assessment for the candidate (one sentence: why yes/no/maybe)
      - location_tags: short text about location/remote
    """
    job_text = ""
    if soup is not None:
        try:
            job_text = soup.get_text(separator=" ", strip=True)
            if len(job_text) > 10000:
                job_text = job_text[:10000] + " [TRUNCATED]"
        except Exception:
            job_text = ""

    prompt_system = (
"You are a concise, professional recruiter assistant tasked with representing a highly skilled engineer." \
"Core Profile:" \
"Title: Full-Stack Developer & Sports Technology Specialist" \
"Education: Dual Master’s degrees – European Engineering Program (focused on Systems and Data) with a strong emphasis on AI and Digital Innovation." \
"Domain Focus: Sports technology development, fan engagement platforms, data analytics for team performance, wearable technology integration, and e-commerce for sports goods." \
"Tech Stack & Skills:" \
"Programming: Python (Pandas, PyTorch, TensorFlow, OpenCV, Django), TypeScript, Java, R, SQL (relational & graph), HTML/CSS, React, Tailwind, Jenkins, Sonar, Git, Jira." \
"Data & AI: Machine learning & deep learning (reinforcement learning – DDDQN, PPO), advanced databases, data pipelines, ETL, PowerBI, Excel, Office 365, Adobe Creative Cloud (After Effects, Premiere Pro, Photoshop, OBS Studio)." \
"Project Management: Agile (Scrum), product ownership, requirement analysis, front-end development, stakeholder communication, workshops (Sports Tech Innovation)." \
"Experience Highlights:" \
"Previously worked on projects focused on data-driven insights for team performance, developing interactive fan engagement platforms, and integrating wearable technology for athlete monitoring." \
"Developed and implemented data pipelines for analyzing sports statistics, contributing to optimized training strategies and performance predictions." \
"Designed and built responsive web applications and mobile interfaces for sports e-commerce and fan communities." \
"Internship experience involved leveraging data science and AI techniques to improve game strategies and fan engagement." \
"Languages: Fluent in French and English, with a growing interest in Japanese." \
"Extracurricular & Soft Skills: Passionate about sports, particularly [Insert Generic Sport Here - e.g., ‘team sports’], enjoys active lifestyles, creative problem-solver, strong collaborator, and effective communicator." \
"Assistant Role:" \
"Provide concise, targeted summaries of the candidate’s qualifications for each opportunity." \
"Highlight the candidate’s versatility and ability to apply a broad range of technical skills to solve complex problems within the sports industry." \
"Emphasize their commitment to innovation and leveraging data-driven solutions to enhance the fan experience and optimize athletic performance." \
"Maintain a professional, direct, and value-focused communication style." \
"Tailor outreach to positions that align with the candidate's skills and interests."
)


    prompt_user = f"""
        Job title: {title}
        Job URL: {url}

        Job page excerpt (if available):
        {job_text or '[NO JOB TEXT PROVIDED]'}

        Task:
        Produce an answer with these keys:
            1) summary: a 2-3 sentence concise summary (what the role is and why it matters)
            2) skills: a short comma-separated list of the most important skills/technologies required
            3) fit: a grade (from 1 to 10 - respectively being a bad fit and a perfect fit - in the format "[x/10]", x being the chosen grade) and one concise sentence assessing match for the candidate described above (e.g. "Bad fit — does not leverage sport knowledge + does not include data skills")
            4) location_tags: short string describing location/remote (e.g. "Calgary, AB; Remote possible")

        Use short, precise phrases. Do not output markdown or explanation.
        """

    try:
        print(f"🤖 Generating structured summary for: {title}")
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": prompt_user}
            ]
        )
        return response['message']['content'].strip()
    except Exception as e:
        return (
            f"Could not generate summary. Error: {e}\n"
            f"Is the Ollama server running and is the model '{model}' available?"
        )