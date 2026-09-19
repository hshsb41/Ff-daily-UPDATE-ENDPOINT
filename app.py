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
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
}

def load_client_urls():
    file_path = 'clients_url.json'
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"error": "clients_url.json file bhetena"}

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
        async with httpx.AsyncClient(timeout=15.0, headers=HEADERS, follow_redirects=True) as client:
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
        
        all_versions = re.findall(r'OB\d{2}', t)
        unique_versions = list(dict.fromkeys(all_versions))
        sorted_versions = sorted(unique_versions, key=lambda x: int(x.replace('OB', '')))
        
        return {
            "status": "success",
            "NextUpdate_Date": "December 16, 2026",
            "countdown": "Active",
            "from_version": sorted_versions[0] if len(sorted_versions) > 0 else "OB55",
            "to_version": sorted_versions[1] if len(sorted_versions) > 1 else "OB56"
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def combined_view():
    region_urls = load_client_urls()
    api_task, web_task = await asyncio.gather(get_api_update(), get_scraping_update())

    # नेपाली डाटा सेक्सन (Nepali Data)
    nepali_data = {
        "सुचना_स्थिति": "सफल",
        "प्ले_स्टोर_अपडेट_विवरण": api_task,
        "खेल_अपडेट_विवरण": web_task,
        "क्षेत्रीय_लिङ्कहरू": region_urls,
        "सृष्टिकर्ता": "Created by CKRPRO ON TOP",
        "युट्युब": "ckr unknown"
    }

    # अंग्रेजी डाटा सेक्सन (English Data)
    english_data = {
        "status": "success",
        "SourceUpdate_info": api_task,
        "GameUpdate_info": web_task,
        "Region_URLs": region_urls,
        "Credit": "Created by CKRPRO ON TOP",
        "YouTube": "ckr unknown"
    }

    nepali_json = json.dumps(nepali_data, indent=4, ensure_ascii=False)
    english_json = json.dumps(english_data, indent=4, ensure_ascii=False)

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
            padding: 30px;
        }}
        h2 {{
            color: #38BDF8;
            border-bottom: 1px solid #334155;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }}
        pre {{
            margin: 0;
            padding: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
            font-size: 14px;
            line-height: 1.6;
            background: transparent;
            border: none;
        }}
        .section-nepali {{
            margin-bottom: 200px; /* नेपाली र अंग्रेजी बीचमा धेरै खाली ठाउँ */
        }}
    </style>
</head>
<body>

    <!-- 🇳🇵 First Section: Nepali Version -->
    <div class="section-nepali">
        <h2>🇳🇵 नेपाली संस्करण (Nepali Version)</h2>
        <pre>{nepali_json}</pre>
    </div>

    <!-- 🇬🇧 Second Section: English Version with large gap -->
    <div class="section-english">
        <h2>🇬🇧 English Version</h2>
        <pre>{english_json}</pre>
    </div>

</body>
</html>"""

    return Response(content=html_content, media_type="text/html")
