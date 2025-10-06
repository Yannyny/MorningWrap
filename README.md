# MorningWrap

### Examples

For job search:
```
uv run --env-file=.env python job_offers_review_main.py --keywords "grid, AI, ML, engineer" --location "canada, calgary" --max 5
```

For Orennia specific job search:
```
uv run --env-file=.env python main_orennia.py
```

For ENMAX specific job search:
```
uv run --env-file=.env python main_enmax.py
```

For article review:
```
uv run --env-file=.env python tech_morning_briefing_main.py --help
```
