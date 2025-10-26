import re
import requests
from bs4 import BeautifulSoup
from collections import deque
# --- CONFIG ---
MAX_DEPTH = 3
TIMEOUT = 10
url = "http://host.docker.internal:8000"  # target page
urlconfig = "http://host.docker.internal:8000/config.js"
# --- REGEX PATTERNS ---
patterns = {
    "AWS S3": re.compile(
        r"(?:https?://)?([a-zA-Z0-9.\-_]+)\.s3(?:[.-][a-z0-9-]+)?\.amazonaws\.com(?:/[\w\-/]*)?"
    ),
    "Google Cloud Storage": re.compile(
        r"(?:https?://)?storage\.googleapis\.com/([\w\-_]+)"
    ),
    "Azure Blob": re.compile(
        r"(?:https?://)?([a-z0-9\-]+)\.blob\.core\.windows\.net(?:/[\w\-/]*)?"
    ),
    "S3 URI": re.compile(r"s3://([\w.\-]+)"),
    "GCS URI": re.compile(r"gs://([\w.\-]+)"),
}

def fetch_page(url):
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[!] Failed to fetch {url}: {e}")
        return ""

def extract_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        if a['href'][0] == '/':
            links.add(url  + a['href'])
    return links


def extract_buckets(text):
    found = {}
    for service, pattern in patterns.items():
        matches = pattern.findall(text)
        if matches:
            found[service] = list(set(matches))
    return found
def crawl(start_url, max_depth=3):
    visited = set()
    queue = deque([(start_url, 0)])
    all_buckets = {}

    while queue:
        url, depth = queue.popleft()
        if url in visited or depth > max_depth:
            continue
        visited.add(url)

        print(f"\n[+] Crawling (depth {depth}): {url}")
        html = fetch_page(url)
        if not html:
            continue

        # extract buckets
        buckets = extract_buckets(html)
        for k, v in buckets.items():
            all_buckets.setdefault(k, set()).update(v)

        # extract links if not at max depth
        if depth < max_depth:
            for link in extract_links(html, url):
                if link not in visited:
                    queue.append((link, depth + 1))
    js = fetch_page(urlconfig)
    bucket_match = re.search(r'bucket:\s*"([^"]+)"',js)
    s3_match = re.search(r's3:\s*"([^"]+)"',js)

    if bucket_match and s3_match:
        all_buckets[s3_match.group(1)] = [bucket_match.group(1)]
    # print results
    
    return all_buckets


def print_buckets(all_buckets):
    print("\n--- SUMMARY ---")
    if all_buckets:
        for svc, names in all_buckets.items():
            print(f"\n{svc}:")
            for n in sorted(names):
                print(f"  - {n}")
    else:
        print("No buckets found.")

if __name__ == "__main__":
    all_buckets = crawl(url, MAX_DEPTH)
    print_buckets(all_buckets)


