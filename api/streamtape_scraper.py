import re
import requests
from bs4 import BeautifulSoup

def extract_m3u8_from_streamtape(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://multiembed.mov/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script')
        for script in scripts:
            if script.text and 'document.getElementById' in script.text:
                match = re.search(r"'robotlink'\)\.innerHTML = '(.*?)';", script.text)
                if match:
                    video_url = match.group(1)
                    if video_url.startswith('//'):
                        video_url = 'https:' + video_url
                    return video_url
        return None
    except Exception as e:
        return None 