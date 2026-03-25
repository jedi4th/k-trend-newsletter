import requests, json, time, urllib.parse, os
from bs4 import BeautifulSoup

# --------------------
# 고급 토픽 키워드
# --------------------
TOPICS = {
    "kpop": [
        "kpop", "idol", "comeback", "debut",
        "stage", "performance", "dance", "fancam",
        "mv", "music video"
    ],
    "kdrama": [
        "kdrama", "netflix", "series", "episode",
        "scene", "plot", "ending", "actor", "actress"
    ],
    "kbeauty": [
        "kbeauty", "skincare", "glass skin", "routine",
        "makeup", "cosmetics", "dermatologist"
    ],
    "kfood": [
        "korean food", "kbbq", "kimchi", "ramen",
        "street food", "recipe", "mukbang"
    ],
    "korea": [
        "korea", "seoul", "k culture", "travel",
        "lifestyle", "street", "shopping"
    ]
}

# --------------------
# 바이럴 키워드 (핵심)
# --------------------
TREND_KEYWORDS = [
    "viral", "trending", "blowing up", "going viral",
    "insane", "crazy", "obsessed", "everyone is talking",
    "fans react", "reaction", "losing it",
    "challenge", "tiktok", "shorts", "reels",
    "must watch", "you need to see", "can't believe",
    "wtf", "omg"
]

# --------------------
# 소스 가중치
# --------------------
SOURCE_WEIGHT = {
    "reddit": 1.2,
    "youtube": 1.1,
    "twitter": 1.3
}

# --------------------
# 유틸
# --------------------
def safe_request(url, headers=None):
    try:
        return requests.get(url, headers=headers, timeout=10)
    except:
        return None

def is_recent(item, hours=24):
    now = time.time()
    created = item.get("created", now)
    return (now - created) <= hours * 3600

# --------------------
# Reddit
# --------------------
def fetch_reddit():
    url = "https://www.reddit.com/r/all/hot.json?limit=100"
    headers = {"User-Agent": "Mozilla/5.0"}

    res = safe_request(url, headers)
    if not res:
        return []

    data = res.json()
    results = []

    for p in data["data"]["children"]:
        d = p["data"]

        results.append({
            "source": "reddit",
            "title": d["title"],
            "url": "https://reddit.com" + d["permalink"],
            "score": d["ups"],
            "created": d["created_utc"]
        })

    return results

# --------------------
# YouTube
# --------------------
def fetch_youtube():
    query = urllib.parse.quote("kpop kdrama kbeauty korean viral tiktok")
    url = f"https://www.youtube.com/results?search_query={query}"

    res = safe_request(url)
    if not res:
        return []

    soup = BeautifulSoup(res.text, "html.parser")

    results = []

    for a in soup.select("a"):
        href = a.get("href", "")
        title = a.get("title", "")

        if "/watch" in href and title:
            results.append({
                "source": "youtube",
                "title": title,
                "url": "https://youtube.com" + href,
                "created": time.time()
            })

    return results[:50]

# --------------------
# Twitter (Nitter)
# --------------------
def fetch_twitter():
    query = urllib.parse.quote("kpop OR kdrama OR kbeauty viral")

    NITTERS = [
        "https://nitter.net",
        "https://nitter.it",
        "https://nitter.cz"
    ]

    for base in NITTERS:
        url = f"{base}/search?f=tweets&q={query}"
        res = safe_request(url)

        if not res:
            continue

        soup = BeautifulSoup(res.text, "html.parser")
        results = []

        for item in soup.select(".timeline-item"):
            try:
                text = item.select_one(".tweet-content").text.strip()
                link = item.select_one("a")["href"]

                results.append({
                    "source": "twitter",
                    "title": text,
                    "url": base + link,
                    "created": time.time()
                })
            except:
                continue

        if results:
            return results[:50]

    return []

# --------------------
# 점수 계산
# --------------------
def keyword_score(title, keywords):
    title = title.lower()
    return sum(1 for k in keywords if k in title)

def trend_score(title):
    title = title.lower()
    return sum(2 for k in TREND_KEYWORDS if k in title)

def classify(item):
    title = item["title"].lower()

    best_topic = None
    best_score = 0

    for topic, keywords in TOPICS.items():
        score = keyword_score(title, keywords)
        if score > best_score:
            best_topic = topic
            best_score = score

    return best_topic, best_score

def calculate_score(item):
    now = time.time()

    created = item.get("created", now)
    freshness = max(0, 1 - (now - created) / 86400)

    popularity = item.get("score", 100) / 1000
    trend = trend_score(item["title"])
    source_score = SOURCE_WEIGHT.get(item["source"], 0.5)

    return (
        popularity * 0.3 +
        freshness * 0.3 +
        trend * 0.3 +
        source_score * 0.1
    )

# --------------------
# 콘텐츠 필터
# --------------------
def is_valuable(title):
    bad_keywords = [
        "opens", "opening", "expands", "launch",
        "release", "apologizes", "collusion"
    ]

    title_lower = title.lower()

    for k in bad_keywords:
        if k in title_lower:
            return False

    return True

# --------------------
# 실행
# --------------------
def main():
    print("📡 SNS 기반 트렌드 수집 시작...")

    data = (
        fetch_reddit() +
        fetch_youtube() +
        fetch_twitter()
    )

    print(f"수집 완료: {len(data)}개")

    # 중복 제거
    seen = set()
    unique = []

    for i in data:
        if i["url"] not in seen:
            seen.add(i["url"])
            unique.append(i)

    print(f"중복 제거 후: {len(unique)}개")

    result = {}

    for item in unique:

        if not is_recent(item):
            continue

        if not is_valuable(item["title"]):
            continue

        topic, hit = classify(item)

        if not topic or hit < 1:
            continue

        item["topic"] = topic
        item["final_score"] = calculate_score(item)

        result.setdefault(topic, []).append(item)

    for t in result:
        result[t] = sorted(
            result[t],
            key=lambda x: x["final_score"],
            reverse=True
        )[:5]

    os.makedirs("data", exist_ok=True)

    with open("data/output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("✅ SNS 기반 output.json 생성 완료")

    from newsletter import generate_newsletter
    generate_newsletter()


if __name__ == "__main__":
    main()
