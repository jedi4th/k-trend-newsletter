import requests, json, time, urllib.parse, os
import xml.etree.ElementTree as ET

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# --------------------
# 공통 RSS 파서 (핵심)
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
                "created": time.time(),
                "score": 100
            })

        return items

    except Exception as e:
        print("RSS ERROR:", url)
        return []

# --------------------
# Reddit (JSON)
# --------------------
def fetch_reddit():
    try:
        url = "https://www.reddit.com/search.json?q=kpop&limit=50"
        res = requests.get(url, headers=HEADERS, timeout=10)
        data = res.json()

        return [{
            "title": p["data"]["title"],
            "url": "https://reddit.com" + p["data"]["permalink"],
            "score": p["data"]["ups"],
            "created": p["data"]["created_utc"]
        } for p in data["data"]["children"]]

    except:
        return []

# --------------------
# YouTube RSS
# --------------------
def fetch_youtube():
    query = urllib.parse.quote("kpop")
    url = f"https://www.youtube.com/feeds/videos.xml?search_query={query}"

    items = fetch_rss(url)

    for i in items:
        i["source"] = "youtube"

    return items

# --------------------
# Google Trends RSS
# --------------------
def fetch_trends():
    url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"

    items = fetch_rss(url)

    for i in items:
        i["source"] = "trends"

    return items

# --------------------
# 점수
# --------------------
def calculate_score(item):
    return item.get("score", 100) / 100

# --------------------
# 실행
# --------------------
def main():
    print("📡 강제 안정 수집 시작...")

    data = []
    data += fetch_reddit()
    data += fetch_youtube()
    data += fetch_trends()

    print(f"수집 완료: {len(data)}개")

    # 🔥 안전장치 (핵심)
    if len(data) == 0:
        print("⚠️ 데이터 없음 → fallback 생성")
        data = [{
            "title": "K-pop is trending
