import re
import requests
from bs4 import BeautifulSoup, Tag

def extract_m3u8_from_vidcloud(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://multiembed.mov/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for video in soup.find_all('video'):
            if isinstance(video, Tag):
                src = video.get('src', '')
                if src and '.m3u8' in src:
                    return src
        for source in soup.find_all('source'):
            if isinstance(source, Tag):
                src = source.get('src', '')
                if src and '.m3u8' in src:
                    return src
        scripts = soup.find_all('script')
        for script in scripts:
            if script.text:
                match = re.search(r'(https?://[^\s"\']+\.m3u8[^\s"\']*)', script.text)
                if match:
                    return match.group(1)
        return None
    except Exception as e:
        return None 