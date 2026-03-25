import requests
import json
import time
import urllib.parse
import os
import xml.etree.ElementTree as ET

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# --------------------
# RSS 파서 (안정)
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
        print("❌ RSS ERROR:", url)
        return []

# --------------------
# Reddit (JSON API)
# --------------------
def fetch_reddit():
    try:
        url = "https://www.reddit.com/search.json?q=kpop%20OR%20kdrama%20OR%20kbeauty&limit=50"
        res = requests.get(url, headers=HEADERS, timeout=10)
        data = res.json()

        results = []
        for p in data["data"]["children"]:
            results.append({
                "title": p["data"]["title"],
                "url": "https://reddit.com" + p["data"]["permalink"],
                "score": p["data"]["ups"],
                "created": p["data"]["created_utc"],
                "source": "reddit"
            })

        return results

    except Exception as e:
        print("❌ REDDIT ERROR")
        return []

# --------------------
# YouTube RSS
# --------------------
def fetch_youtube():
    query = urllib.parse.quote("kpop kdrama kbeauty korean")
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
# 점수 계산
# --------------------
def calculate_score(item):
    return item.get("score", 100) / 100

# --------------------
# 메인 실행
# --------------------
def main():
    print("📡 안정형 데이터 수집 시작...")

    data = []
    data += fetch_reddit()
    data += fetch_youtube()
    data += fetch_trends()

    print(f"수집 완료: {len(data)}개")

    # 🔥 fallback (절대 0 방지)
    if len(data) == 0:
        print("⚠️ 데이터 없음 → fallback 생성")
        data = [{
            "title": "K-pop is trending globally right now",
            "url": "https://example.com",
            "source": "fallback",
            "score": 100,
            "created": time.time()
        }]

    # --------------------
    # 결과 구성
    # --------------------
    result = {
        "kpop": [],
        "kdrama": [],
        "kbeauty": [],
        "kfood": [],
        "korea": []
    }

    # 👉 간단 분류 (초기 버전)
    for item in data:
        title = item["title"].lower()

        if "kpop" in title or "idol" in title:
            result["kpop"].append(item)
        elif "drama" in title or "netflix" in title:
            result["kdrama"].append(item)
        elif "beauty" in title or "skincare" in title:
            result["kbeauty"].append(item)
        elif "food" in title or "korean bbq" in title:
            result["kfood"].append(item)
        else:
            result["korea"].append(item)

    # 👉 각 카테고리 TOP 5
    for key in result:
        result[key] = sorted(
            result[key],
            key=lambda x: x.get("score", 100),
            reverse=True
        )[:5]

    # --------------------
    # 저장
    # --------------------
    os.makedirs("data", exist_ok=True)

    with open("data/output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("✅ output.json 생성 완료")

    # --------------------
    # 뉴스레터 생성
    # --------------------
    try:
        from newsletter import generate_newsletter
        generate_newsletter()
    except:
        print("⚠️ newsletter.py 없음 (스킵)")


if __name__ == "__main__":
    main()
