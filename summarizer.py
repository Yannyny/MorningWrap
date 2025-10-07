import json

import ollama
from bs4 import BeautifulSoup

from utils import logger, safe_truncate_text

AI_MODEL = "gemma3:4b"

PROMPT_SYSTEM = (
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

def generate_summary_with_ai(title: str, url: str, soup: BeautifulSoup | None = None, model: str = AI_MODEL) -> str:
    job_text = safe_truncate_text(soup, max_chars=10000)

    prompt_user = f"""
    Job title: {title}
    Job URL: {url}

    Job page excerpt (if available):
    {job_text or '[NO JOB TEXT PROVIDED]'}

    Task:
    Produce a JSON with these keys:
        1) summary: a 2-3 sentence concise summary (what the role is and why it matters)
        2) skills: a short comma-separated list of the most important skills/technologies required
        3) fit: a grade (from 1 to 10 - respectively being a bad fit and a perfect fit - in the format "[x/10]", x being the chosen grade) and one concise sentence assessing match for the candidate described above (e.g. "Bad fit — does not leverage sport knowledge + does not include data skills")
        4) location_tags: short string describing location/remote (e.g. "Calgary, AB; Remote possible")

    Use short, precise phrases. Do not output markdown or explanation.
    Output VALID JSON only.
    """

    try:
        logger.info("🤖 Generating summary...")
        resp = ollama.chat(
            model=model,
            messages=[
                {"role":"system", "content": PROMPT_SYSTEM},
                {"role":"user", "content": prompt_user}
                ]
        )
        raw = resp['message']['content'].strip()
        try:
            parsed = json.loads(raw)
            return json.dumps(parsed, ensure_ascii=False)
        except json.JSONDecodeError:
            logger.warning("Model did not return valid JSON for '%s'. Returning raw.", title)
            return raw
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        return f"LLM error: {e}"