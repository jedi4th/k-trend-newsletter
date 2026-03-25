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
# 키워드 정의
# --------------------
TOPIC_KEYWORDS = {
    "kpop": ["kpop", "idol", "comeback", "concert"],
    "kdrama": ["drama", "netflix", "series", "episode"],
    "kbeauty": ["beauty", "skincare", "makeup", "cosmetic"],
    "kfood": [
        "food", "korean food", "kbbq", "ramen",
        "noodle", "kimchi", "snack", "restaurant",
        "cafe", "bbq", "cup", "eat"
    ],
    "korea": ["korea", "seoul", "travel", "culture"]
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

    except Exception as e:
        print("❌ RSS ERROR:", url)
        return []

# --------------------
# Google News
# --------------------
def fetch_google_news():
    query = urllib.parse.quote("kpop OR kdrama OR kbeauty OR korean food OR korean trend")
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    items = fetch_rss(url)

    for i in items:
        i["source"] = "google_news"

    return items

# --------------------
# Bing News
# --------------------
def fetch_bing_news():
    query = urllib.parse.quote("kpop kdrama kbeauty korean food trend")
    url = f"https://www.bing.com/news/search?q={query}&format=rss"

    items = fetch_rss(url)

    for i in items:
        i["source"] = "bing_news"

    return items

# --------------------
# 중복 제거
# --------------------
def is_duplicate(title, seen_titles):
    for t in seen_titles:
        if title[:40] == t[:40]:
            return True
    return False

# --------------------
# 점수 계산
# --------------------
def calculate_score(item):
    title = item["title"].lower()

    score = 1

    keywords = ["viral", "trend", "hot", "netflix", "tiktok"]
    for k in keywords:
        if k in title:
            score += 2

    return score

# --------------------
# 분류
# --------------------
def classify(item):
    title = item["title"].lower()

    best_topic = None
    best_score = 0

    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for k in keywords if k in title)

        if score > best_score:
            best_topic = topic
            best_score = score

    return best_topic

# --------------------
# 메인 실행
# --------------------
def main():
    print("📡 트렌드 수집 시작...")

    data = []
    data += fetch_google_news()
    data += fetch_bing_news()

    print(f"수집 완료: {len(data)}개")

    # fallback
    if len(data) == 0:
        print("⚠️ fallback 생성")
        data = [{
            "title": "Korean trend is rising globally",
            "url": "https://example.com",
            "source": "fallback",
            "score": 100,
            "created": time.time()
        }]

    # --------------------
    # 중복 제거
    # --------------------
    seen_titles = set()
    filtered = []

    for item in data:
        title = item["title"]

        if is_duplicate(title, seen_titles):
            continue

        seen_titles.add(title)
        filtered.append(item)

    print(f"중복 제거 후: {len(filtered)}개")

    # --------------------
    # 분류 + 점수
    # --------------------
    result = {k: [] for k in TOPIC_KEYWORDS.keys()}

    for item in filtered:
        topic = classify(item)
        if not topic:
            continue

        item["final_score"] = calculate_score(item)
        result[topic].append(item)

    # --------------------
    # TOP 5
    # --------------------
    for key in result:
        result[key] = sorted(
            result[key],
            key=lambda x: x["final_score"],
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
    # 뉴스레터
    # --------------------
    try:
        from newsletter import generate_newsletter
        generate_newsletter()
    except:
        print("⚠️ newsletter.py 없음")

    # --------------------
    # 카드뉴스
    # --------------------
    try:
        from card_news import generate_card_news
        generate_card_news()
    except:
        print("⚠️ card_news.py 없음")


if __name__ == "__main__":
    main()
