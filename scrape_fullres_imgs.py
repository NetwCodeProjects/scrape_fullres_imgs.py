import os
import re
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pathlib import Path

# === CONFIG ===
DOWNLOAD_DIR = "fullres_images"
SCROLL_PAUSE_TIME = 2.0
MAX_SCROLLS = 30  # Adjust as needed
TIMEOUT = 10
# ===============

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,3000")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scroll_to_bottom(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    scrolls = 0

    while scrolls < MAX_SCROLLS:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
        scrolls += 1

def extract_all_images(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    urls = set()
    lazy_attrs = [
        "src", "data-src", "data-original", "data-lazy", "data-lazy-src",
        "data-fullres", "data-hires"
    ]

    # (1) img tags with lazy-load
    for img in soup.find_all("img"):
        for attr in lazy_attrs:
            src = img.get(attr)
            if src and not src.startswith("data:"):
                urls.add(urljoin(base_url, src.strip()))

        srcset = img.get("srcset")
        if srcset:
            parts = [x.strip().split(" ")[0] for x in srcset.split(",")]
            for part in parts:
                if part and not part.startswith("data:"):
                    urls.add(urljoin(base_url, part.strip()))

    # (2) source tags
    for source in soup.find_all("source"):
        for attr in lazy_attrs + ["srcset"]:
            src = source.get(attr)
            if src and not src.startswith("data:"):
                urls.add(urljoin(base_url, src.strip()))

    # (3) background images in style attributes
    for tag in soup.find_all(style=True):
        style = tag["style"]
        if "background-image" in style:
            matches = re.findall(r"url\(['\"]?(.*?)['\"]?\)", style)
            for m in matches:
                if m and not m.startswith("data:"):
                    urls.add(urljoin(base_url, m.strip()))

    return list(urls)

def download_images(image_urls):
    Path(DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    seen = set()

    for url in image_urls:
        if url in seen:
            continue
        seen.add(url)

        try:
            r = session.get(url, stream=True, timeout=TIMEOUT)
            if r.status_code == 200:
                filename = os.path.basename(urlparse(url).path)
                if not filename or '.' not in filename:
                    filename = f"image_{len(seen)}.jpg"
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                with open(filepath, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                print(f"[+] Downloaded: {filename}")
            else:
                print(f"[!] Failed {url} - Status {r.status_code}")
        except Exception as e:
            print(f"[!] Error {url} - {e}")

def scrape_site(url):
    print(f"[*] Starting Selenium scrape: {url}")
    driver = init_driver()
    driver.get(url)
    scroll_to_bottom(driver)
    html = driver.page_source
    base_url = driver.current_url
    driver.quit()

    image_urls = extract_all_images(html, base_url)
    print(f"[*] Found {len(image_urls)} images.")
    download_images(image_urls)
    print(f"[✓] Done. Images saved in '{DOWNLOAD_DIR}'.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python scrape_images_selenium.py <url>")
        exit(1)
    scrape_site(sys.argv[1])
