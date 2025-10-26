import re
import requests
from bs4 import BeautifulSoup

# --- CONFIG ---
url = "http://host.docker.internal:8000"  # target page
urlconfig = "http://host.docker.internal:8000/config.js"
# --- FETCH PAGE ---
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    html = response.text
    response2 = requests.get(urlconfig,timeout = 10)
    response2.raise_for_status()
    js = response2.text
except Exception as e:
    print(f"[!] Error fetching page: {e}")
    exit(1)

# print(js)

# --- PARSE TEXT (optional HTML cleanup) ---
soup = BeautifulSoup(html, "html.parser")
text = soup.get_text(" ", strip=True)
scripts = soup.find_all('script', src=True)

for script in scripts: 
    src = script.get('src')
    if 'config' in src: 
        config_url = 'http://host.docker.internal:8000/{src}'
        config_response = requests.get(config_url)
        config_content = config_response.text

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


# --- EXTRACT BUCKETS ---
found = {}
for name, pattern in patterns.items():
    matches = pattern.findall(html)
    if matches:
        found[name] = list(set(matches))

bucket_match = re.search(r'bucket:\s*"([^"]+)"',js)
s3_match = re.search(r's3:\s*"([^"]+)"',js)

if bucket_match and s3_match:
    found[s3_match.group(1)] = [bucket_match.group(1)]
# --- DISPLAY RESULTS ---
if found:
    print("\n[+] Possible Bucket Endpoints Found:")
    for service, buckets in found.items():
        print(f"\n{service}:")
        for b in buckets:
            print(f"  - {b}")
else:
    print("[-] No bucket endpoints found.")