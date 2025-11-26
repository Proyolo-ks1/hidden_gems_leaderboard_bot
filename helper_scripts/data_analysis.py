# helper_scripts/data_analysis.py

import os
import re
import requests
import pandas as pd
import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from pathlib import Path

from helper_scripts.globals import LOCAL_DATA_PATH_DIR

URL = "https://hiddengems.gymnasiumsteglitz.de/scrims"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
DATA_ROOT = LOCAL_DATA_PATH_DIR

LANG_MAP = {
    'python': 'Python', 'cpp': 'C++', 'c': 'C', 'csharp': 'C#',
    'ts': 'TypeScript', 'ruby': 'Ruby', 'java': 'Java', 'js': 'JavaScript', 'go': 'Go'
}

def parse_float(text: str):
    if not text: return None
    t = text.strip().replace('%', '').replace(',', '.')
    try:
        m = re.search(r'(-?\d+(.\d+)?)', t)
        if m: return float(m.group(1))
    except: pass
    return None

def scrape_data():
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(URL, headers=headers, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        return {"error": f"Webseite konnte nicht abgerufen werden: {e}"}
        
    soup = BeautifulSoup(resp.text, 'html.parser')

    target_table = None
    tables = soup.find_all('table')
    for tbl in tables:
        headers_text = [th.get_text(strip=True) for th in tbl.find_all('th')]
        if "Bot" in headers_text and "Score" in headers_text:
            target_table = tbl
            break

    if not target_table:
        return {"error": "Keine Leaderboard-Tabelle auf der Webseite gefunden."}

    rows = []
    tbody = target_table.find('tbody') or target_table
    for tr in tbody.find_all('tr'):
        if 'spacer' in (tr.get('class') or []): continue
        tds = tr.find_all('td')
        if len(tds) < 10: continue 

        def txt(i): return tds[i].get_text(strip=True) if i < len(tds) else ""

        rank_raw = txt(0)
        rank = int(re.sub(r'\D', '', rank_raw)) if re.search(r'\d', rank_raw) else None
        
        try: score = int(re.sub(r'[^\d\-]', '', txt(3)))
        except: score = 0
        
        gu_pct = parse_float(txt(4))
        cf_pct = parse_float(txt(5))
        fc_pct = parse_float(txt(6))
        
        author = txt(7)
        city = txt(8)
        
        lang = "Unknown"
        if len(tds) > 9:
            img = tds[9].find('img')
            if img and img.get('src'):
                src_base = os.path.basename(img.get('src').split('?')[0])
                m = re.match(r'([a-z0-9_\-]+)-logo', src_base, flags=re.I)
                if m:
                    key = m.group(1).lower()
                    lang = LANG_MAP.get(key, key.capitalize())

        rows.append({
            "rank": rank, "bot": txt(2), "score": score,
            "gu_pct": gu_pct, "cf_pct": cf_pct, "fc_pct": fc_pct,
            "author": author, "city": city, "language": lang
        })

    return pd.DataFrame(rows)

def generate_plots_images(df, folder):
    folder.mkdir(parents=True, exist_ok=True)
    
    metrics_to_plot = [
        ("Score Distribution", 'score', '#f59e0b', 'Higher', 'score_hist.png'),
        ("Gem Utilization (GU)", 'gu_pct', '#3b82f6', 'Higher', 'gu_pct_hist.png'),
        ("Chaos Factor (CF)", 'cf_pct', '#ef4444', 'Lower', 'cf_pct_hist.png'),
        ("Floor Coverage (FC)", 'fc_pct', '#10b981', 'Higher', 'fc_pct_hist.png'),
    ]

    for name, col, color, better, file_name in metrics_to_plot:
        fig, ax = plt.subplots(figsize=(6, 4))
        if col in df.columns:
            data = pd.to_numeric(df[col], errors='coerce').dropna()
            if not data.empty:
                ax.hist(data, bins=15, color=color, alpha=0.7)
                ax.set_xlabel(name.split('(')[0].strip())
                ax.set_ylabel("Count")
            else:
                ax.text(0.5, 0.5, "No data", transform=ax.transAxes)
        ax.set_title(f"{name}")
        fig.tight_layout()
        fig.savefig(folder / file_name)
        plt.close(fig)
        
    # Language bar chart
    fig, ax = plt.subplots(figsize=(6, 4))
    if 'language' in df.columns:
        df['language'].value_counts().plot(kind='bar', ax=ax, color="#3b82f6")
        ax.set_title("Bots per Language")
    fig.tight_layout()
    fig.savefig(folder / "lang_bar.png")
    plt.close(fig)

    # City bar chart
    fig, ax = plt.subplots(figsize=(6, 4))
    if 'city' in df.columns:
        df['city'].value_counts().head(15).plot(kind='bar', ax=ax, color="#10b981")
        ax.set_title("Top 15 Cities")
    fig.tight_layout()
    fig.savefig(folder / "city_bar.png")
    plt.close(fig)
    
    return folder