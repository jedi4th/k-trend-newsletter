import requests
import json
import time
import os
import xml.etree.ElementTree as ET
import urllib.parse

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# --------------------
# RSS 파서
# --------------------
def fetch_rss(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        root = ET.fromstring(res.content)

        items = []
        for item in root.findall(".//item"):
            title = item.find("title").text if item.find("title") is not None else ""
            link = item.find("link").text if item.find("link") is not None else ""

            items.append({
                "title": title,
                "url": link,
                "score": 100,
                "created": time.time()
            })

        return items

    except:
        return []

# --------------------
# Google News (핵심)
# --------------------
def fetch_google_news():
    query = urllib.parse.quote("kpop OR kdrama OR kbeauty OR korean trend")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    items = fetch_rss(url)

    for i in items:
        i["source"] = "google_news"

    return items

# --------------------
# Bing News
# --------------------
def fetch_bing_news():
    query = urllib.parse.quote("kpop kdrama korean trend")
    url = f"https://www.bing.com/news/search?q={query}&format=rss"

    items = fetch_rss(url)

    for i in items:
        i["source"] = "bing_news"

    return items

# --------------------
# 점수
# --------------------
def calculate_score(item):
    title = item["title"].lower()

    score = 1

    keywords = ["viral", "trending", "hot", "netflix", "tiktok"]
    for k in keywords:
        if k in title:
            score += 2

    return score

# --------------------
# 실행
# --------------------
def main():
    print("📡 뉴스 기반 트렌드 수집 시작...")

    data = []
    data += fetch_google_news()
    data += fetch_bing_news()

    print(f"수집 완료: {len(data)}개")

    # fallback
    if len(data) == 0:
        print("⚠️ fallback 생성")
        data = [{
            "title": "K-pop global trend rising",
            "url": "https://example.com",
            "source": "fallback",
            "score": 100,
            "created": time.time()
        }]

    result = {
        "kpop": [],
        "kdrama": [],
        "kbeauty": [],
        "kfood": [],
        "korea": []
    }

    for item in data:
        title = item["title"].lower()
        item["final_score"] = calculate_score(item)

        if "kpop" in title:
            result["kpop"].append(item)
        elif "drama" in title or "netflix" in title:
            result["kdrama"].append(item)
        elif "beauty" in title:
            result["kbeauty"].append(item)
        elif "food" in title:
            result["kfood"].append(item)
        else:
            result["korea"].append(item)

    for key in result:
        result[key] = sorted(
            result[key],
            key=lambda x: x["final_score"],
            reverse=True
        )[:5]

    os.makedirs("data", exist_ok=True)

    with open("data/output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("✅ output.json 생성 완료")

    from newsletter import generate_newsletter
    generate_newsletter()

if __name__ == "__main__":
    main()
