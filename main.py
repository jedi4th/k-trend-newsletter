import requests
import json
from datetime import datetime
from collections import defaultdict

YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"

# =========================
# 🔥 트렌드 키워드 (핵심)
# =========================
TREND_KEYWORDS = {
    "KPOP": [
        "kpop comeback", "kpop viral", "kpop dance challenge"
    ],
    "KDRAMA": [
        "kdrama netflix", "kdrama trending", "korean drama viral"
    ],
    "KBEAUTY": [
        "kbeauty routine", "korean skincare trend", "glass skin"
    ],
    "KFOOD": [
        "korean food mukbang", "buldak ramen", "tteokbokki viral",
        "korean street food", "korean recipe viral"
    ],
    "KOREA": [
        "korea trend", "korean culture viral", "korean lifestyle"
    ]
}

# =========================
# 🔥 YouTube 트렌드 수집
# =========================
def get_youtube_trends():
    print("📺 YouTube 트렌드 수집 중...")
    results = []

    for category, keywords in TREND_KEYWORDS.items():
        for keyword in keywords:
            url = f"https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "order": "viewCount",
                "maxResults": 5,
                "key": YOUTUBE_API_KEY
            }

            try:
                res = requests.get(url, params=params).json()

                for item in res.get("items", []):
                    results.append({
                        "title": item["snippet"]["title"],
                        "summary": item["snippet"]["description"][:120],
                        "hook": f"{category} 🔥 {keyword}",
                        "link": f"https://youtube.com/watch?v={item['id']['videoId']}",
                        "category": category,
                        "source": "youtube"
                    })

            except:
                print("❌ YouTube API 오류")

    return results

# =========================
# 🔥 뉴스 (보조)
# =========================
def get_google_news():
    print("📰 뉴스 보조 수집...")
    url = "https://news.google.com/rss/search?q=korea+kpop+kbeauty+kfood&hl=en&gl=US&ceid=US:en"

    results = []

    try:
        res = requests.get(url).text
        items = res.split("<item>")[1:20]

        for item in items:
            title = item.split("<title>")[1].split("</title>")[0]
            link = item.split("<link>")[1].split("</link>")[0]

            category = "KOREA"

            if "food" in title.lower():
                category = "KFOOD"
            elif "beauty" in title.lower():
                category = "KBEAUTY"
            elif "drama" in title.lower():
                category = "KDRAMA"
            elif "kpop" in title.lower():
                category = "KPOP"

            results.append({
                "title": title,
                "summary": title,
                "hook": f"{category} 뉴스",
                "link": link,
                "category": category,
                "source": "news"
            })

    except:
        print("❌ 뉴스 오류")

    return results

# =========================
# 🔥 중복 제거 (핵심)
# =========================
def remove_duplicates(data):
    seen = set()
    unique = []

    for item in data:
        key = item["title"][:50].lower()

        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique

# =========================
# 🔥 KFOOD 강화
# =========================
def boost_kfood(data):
    kfood = [d for d in data if d["category"] == "KFOOD"]

    if len(kfood) < 5:
        print("⚠️ KFOOD 부족 → 강제 보강")

        extra = [
            {
                "title": "Buldak ramen challenge viral",
                "summary": "Spicy Korean ramen trend exploding globally",
                "hook": "KFOOD 🔥 viral",
                "link": "https://youtube.com",
                "category": "KFOOD",
                "source": "fallback"
            }
        ]

        data.extend(extra)

    return data

# =========================
# 🔥 뉴스레터 생성
# =========================
def generate_newsletter(data):
    print("📝 뉴스레터 생성...")

    grouped = defaultdict(list)
    for item in data:
        grouped[item["category"]].append(item)

    text = f"[K-TREND AI INPUT - {datetime.today().date()}]\n\n"

    for category in ["KPOP", "KDRAMA", "KBEAUTY", "KFOOD", "KOREA"]:
        text += f"\n=== {category} ===\n\n"

        for i, item in enumerate(grouped.get(category, [])[:5], 1):
            text += f"{i}.\n"
            text += f"TITLE: {item['title']}\n"
            text += f"SUMMARY: {item['summary']}\n"
            text += f"HOOK: {item['hook']}\n"
            text += f"SOURCE: {item['source']}\n"
            text += f"LINK: {item['link']}\n\n"

    with open("newsletter.txt", "w", encoding="utf-8") as f:
        f.write(text)

    print("✅ newsletter.txt 생성 완료")

# =========================
# 🔥 실행
# =========================
def main():
    print("🚀 트렌드 수집 시작")

    data = []

    yt = get_youtube_trends()
    news = get_google_news()

    data.extend(yt)
    data.extend(news)

    print(f"수집 완료: {len(data)}")

    data = remove_duplicates(data)
    data = boost_kfood(data)

    print(f"정제 후: {len(data)}")

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    generate_newsletter(data)


if __name__ == "__main__":
    main()
