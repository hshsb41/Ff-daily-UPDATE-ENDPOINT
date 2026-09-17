from fastapi import FastAPI, Response
import httpx
from google_play_scraper import app as play_scraper
from bs4 import BeautifulSoup
import re
import asyncio
import json
import os

app = FastAPI()

FF_MANIA_URL = "https://www.freefiremania.com.br/free-fire-new-update.html"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def load_client_urls():
    file_path = 'clients_url.json'
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return {"error": "clients_url.json not found"}

async def get_api_update():
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: play_scraper('com.dts.freefireth', lang="bn", country='bd'))
        play_version = result['version']
        
        api_url = f'https://version.ggwhitehawk.com/live/ver.php?version={play_version}&lang=bn&device=android&channel=android&appstore=googleplay&region=BD&whitelist_version=1.3.0&whitelist_sp_version=1.0.0'
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(api_url)
            data = response.json()

        return {
            "status": "success",
            "remote_version": data.get('remote_version'),
            "server_url": data.get('server_url'),
            "latest_release_version": data.get('latest_release_version'),
            "play_store_version": play_version
        }
    except Exception as e:
        return {"error": str(e)}

async def get_scraping_update():
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=HEADERS) as client:
            r = await client.get(FF_MANIA_URL)
            r.raise_for_status()
        
        s = BeautifulSoup(r.content, 'html.parser')
        t = ' '.join(s.get_text().split())
        
        p = r'Free Fire will update on (.+?), that is, (.+?) left until the next update, when the game will move from version (OB\d+) to the new version (OB\d+)\.'
        m = re.search(p, t, re.IGNORECASE)
        
        if m:
            return {
                "status": "success",
                "NextUpdate_Date": m.group(1).strip(),
                "countdown": m.group(2).strip(),
                "from_version": m.group(3).strip(),
                "to_version": m.group(4).strip()
            }
        return {"error": "Scraping pattern not found"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def get_combined_update():
    region_urls = load_client_urls()
    api_task, web_task = await asyncio.gather(get_api_update(), get_scraping_update())

    # Professional Premium JSON Data Dictionary
    response_data = {
        "status": "success",
        "SourceUpdate_info": api_task,
        "GameUpdate_info": web_task,
        "Region_URLs": region_urls,
        "Credit": "Created by CKRPRO ON TOP",
        "YouTube": "ckr unknown"
    }

    # Pretty JSON string formatting (Indentation with 4 spaces)
    pretty_json = json.dumps(response_data, indent=4, ensure_ascii=False)

    # HTML template with custom Dark Theme styling so it opens line-by-line automatically without clicking anything
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CKRPRO - Free Fire Update API</title>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body {{
            background-color: #0F1117;
            color: #E2E8F0;
            font-family: 'Fira Code', monospace;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: #161B22;
            border: 1px solid #30363D;
            border-radius: 10px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.5);
            overflow: hidden;
        }}
        .header {{
            background: #21262D;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: 500;
            border-bottom: 1px solid #30363D;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .dot-container {{
            display: flex;
            gap: 6px;
        }}
        .dot {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        .dot-red {{ background: #FF5F56; }}
        .dot-yellow {{ background: #FFBD2E; }}
        .dot-green {{ background: #27C93F; }}
        pre {{
            margin: 0;
            padding: 20px;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 13px;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="dot-container">
                <div class="dot dot-red"></div>
                <div class="dot dot-yellow"></div>
                <div class="dot dot-green"></div>
            </div>
            <span>CKRPRO_API_RESPONSE.json</span>
        </div>
        <pre>{pretty_json}</pre>
    </div>
</body>
</html>"""

    return Response(content=html_content, media_type="text/html")
