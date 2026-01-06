def extract_data(soup, url):
    title = soup.title.string.strip() if soup.title else None
    meta = soup.find("meta", attrs={"name": "description"})
    desc = meta["content"].strip() if meta and meta.get("content") else None
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]
    content = " ".join(paragraphs[:20])
    return title, desc, content
