import heapq
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
from extractor import extract_data
from robots_handler import load_robot_parser, extract_sitemap_urls
import time
visited = set()
all_links = set()
from database import init_db, upsert_page, insert_link




init_db()

def normalize_url(url):
    """Clean URL: remove trailing slash, keep root '/' """
    parsed = urlparse(url)

    scheme = parsed.scheme.lower() or "http"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/") or "/"
    return f"{scheme}://{netloc}{path}"

def score_url(url, depth):
    """Higher score = more important. Priority queue uses negative score."""
    score = 0

    # 1. Depth priority (shallower = better)
    score += max(0, 6 - depth)

    # 2. Important sections 
    important = ["about", "docs", "blog", "download", "help", "tutorial"]
    if any(k in url.lower() for k in important):
        score += 3

    # 3. Bad/useless URLs
    ignore = ["login", "signup", "logout", "wp-", "admin", "cart", "checkout"]
    if any(k in url.lower() for k in ignore):
        score -= 8

    return score


def crawl_it(start_url, max_depth):
    main_domain = urlparse(start_url).netloc
    domain = f"{urlparse(start_url).scheme}://{main_domain}"

    rp = load_robot_parser(domain)
    sitemap_urls = extract_sitemap_urls(domain)

    queue = []
    if not sitemap_urls:
        print("No usable sitemap URLs found, falling back to seed URL")

    # Start from sitemap URLs if present
    seed_urls = sitemap_urls or [start_url]

    for url in seed_urls:
        u = normalize_url(url)
        s = score_url(u, 0)
        heapq.heappush(queue, (-s, u, 0))

    # Crawl loop (Priority-based)

    while queue:
        _, url, depth = heapq.heappop(queue)
        url = normalize_url(url)

        if url in visited or depth > max_depth:
            continue

        # Respect robots.txt
        if not rp.can_fetch("*", url):
            print(f"Blocked by robots.txt: {url}")
            continue

        # Fetch
        try:
            time.sleep(1)  # Be polite to servers
            resp = requests.get(url, timeout=6)
            if resp.status_code != 200:
                continue
            if "text/html" not in resp.headers.get("Content-Type", ""):
                print(f"Skipping non-HTML: {url}")
                continue
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            continue

        visited.add(url)
        print(f"\nVisited ({len(visited)}): {url}")

        soup = BeautifulSoup(resp.text, 'html.parser')
        title, desc, content = extract_data(soup, url)
        # print(f"title: {title}\ndesc: {desc}\ncontent preview: {content[:150]}\n")

        import hashlib

        content_hash = hashlib.sha256(
        content.encode("utf-8", errors="ignore")
        ).hexdigest()

        content_length = len(content)

# storing in DB
        page_id = upsert_page(
        url=url,
        domain=main_domain,
        title=title,
        desc=desc,
        content=content,
        content_hash=content_hash,
        content_length=content_length,
        depth=depth,
        status_code=resp.status_code,
        content_type=resp.headers.get("Content-Type", "")
        )   


        # save_page(
        # url=url,
        # domain=main_domain,
        # title=title,
        # desc=desc,
        # content=content,
        # links=all_links,
        # depth=depth,
        # status_code=resp.status_code,
        # content_type=resp.headers.get("Content-Type")
        # )

        # Extract internal links
        for link in soup.find_all("a", href=True):
            next_url = urljoin(url, link.get("href"))
            next_url = normalize_url(next_url)

            if urlparse(next_url).netloc != main_domain:
                continue

            if any(next_url.lower().endswith(ext) for ext in ['.pdf', '.jpg', '.png', '.doc', '.zip', '.mp4', '.css', '.js']):
                continue

    # -------- STEP 5.3 START --------

            child_page_id = upsert_page(
            url=next_url,
            domain=main_domain,
            title=None,
            desc=None,
            content="",
            content_hash=None,
            content_length=0,
            depth=depth + 1,
            status_code=None,
            content_type=None
            )

            insert_link(page_id, child_page_id)

    # -------- STEP 5.3 END --------

            all_links.add(next_url)

            s = score_url(next_url, depth + 1)
            heapq.heappush(queue, (-s, next_url, depth + 1))

# start_url = "https://leetcode.com/"
# start_url = "https://example.com/"
start_url = "https://www.python.org/"
crawl_it(start_url, 0)

print("\n----- Summary -----")
print(f"Total pages visited: {len(visited)}")
print(f"Total internal links found: {len(all_links)}")
