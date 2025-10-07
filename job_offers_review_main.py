# main.py
import argparse
import requests
import feedparser
import ollama
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

AI_MODEL = 'mistral'

def fetch_remoteok() -> List[Dict]:
    """Fetch the RemoteOK JSON feed (fallback if blocked)."""
    url = "https://remoteok.com/remote-jobs.json"  # RemoteOK exposes JSON / feed; adjust if changed
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent":"job-finder-bot/1.0"})
        resp.raise_for_status()
        data = resp.json()
        # the feed often includes metadata as the first item or with non-job entries; filter by having 'position' or 'company'
        jobs = [item for item in data if isinstance(item, dict) and item.get("position") or item.get("company")]
        return jobs
    except Exception as e:
        print(f"[remoteok] error: {e}")
        return []

def fetch_weworkremotely_rss() -> List[Dict]:
    """Fetch WeWorkRemotely RSS and convert into a simple dict list."""
    rss_url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
    try:
        feed = feedparser.parse(rss_url)
        jobs = []
        for entry in feed.entries:
            jobs.append({
                "title": entry.get("title"),
                "link": entry.get("link"),
                "summary": BeautifulSoup(entry.get("summary", ""), "html.parser").get_text(),
            })
        return jobs
    except Exception as e:
        print(f"[wwr] error: {e}")
        return []

def matches_criteria(title: str, summary: str, keywords: List[str], location: Optional[str]) -> bool:
    text = (title + " " + (summary or "")).lower()
    if keywords:
        if not any(k.lower().strip() in text for k in keywords):
            return False
    if location:
        # coarse location match — many remote jobs won't have a location, so treat "remote" specially
        if location.lower() not in text and "remote" not in location.lower() and "remote" not in text:
            return False
    return True

def generate_summary_with_ai(title: str, link: str, job_text: Optional[str]) -> str:
    prompt = f"""
You are a technical recruiter assistant. Summarize this job posting in 2 concise bullet points:
- core responsibilities and required skills
- why it might be interesting to a developer

TITLE: {title}
LINK: {link}
JOB_TEXT: {job_text or 'N/A'}
"""
    try:
        response = ollama.chat(
            model=AI_MODEL,
            messages=[{"role":"user", "content": prompt}]
        )
        return response['message']['content'].strip()
    except Exception as e:
        return f"AI summary error: {e}\n(Make sure Ollama is running and model {AI_MODEL} is available.)"

def normalize_remoteok_item(item: Dict) -> Dict:
    # map RemoteOK fields into a common shape
    return {
        "title": item.get("position") or item.get("title"),
        "company": item.get("company"),
        "link": item.get("url") or item.get("link"),
        "description": item.get("description") or item.get("tags") or "",
    }

def main():
    parser = argparse.ArgumentParser(description="AI job-finder (RemoteOK + WWR example)")
    parser.add_argument("--keywords", "-k", type=str, default="", help="Comma-separated keywords, e.g. 'python,backend'")
    parser.add_argument("--location", "-l", type=str, default="", help="Location or 'remote'")
    parser.add_argument("--max", "-m", type=int, default=10, help="Max results")
    parser.add_argument("--sources", "-s", type=str, default="remoteok,wwr", help="Comma list: remoteok,wwr")
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    sources = [s.strip().lower() for s in args.sources.split(",") if s.strip()]

    candidates = []

    if "remoteok" in sources:
        for item in fetch_remoteok():
            norm = normalize_remoteok_item(item)
            if matches_criteria(norm["title"], norm["description"], keywords, args.location):
                candidates.append(norm)
                if len(candidates) >= args.max:
                    break

    if "wwr" in sources and len(candidates) < args.max:
        for item in fetch_weworkremotely_rss():
            if matches_criteria(item["title"], item.get("summary",""), keywords, args.location):
                candidates.append({
                    "title": item["title"],
                    "company": None,
                    "link": item["link"],
                    "description": item.get("summary","")
                })
                if len(candidates) >= args.max:
                    break

    if not candidates:
        print("No job listings matched your criteria.")
        return

    for i, job in enumerate(candidates, start=1):
        print("==========================================")
        print(f"{i:02d}. {job['title']}")
        if job.get("company"):
            print(f"   Company: {job['company']}")
        print(f"   Link: {job['link']}")
        summary = generate_summary_with_ai(job['title'], job['link'], job.get("description"))
        print(f"   AI Summary:\n{summary}\n")

if __name__ == "__main__":
    main()
