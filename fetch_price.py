import requests
from bs4 import BeautifulSoup
import json
import time


# =====================
# 国家代码和对应货币代码
# =====================
country_currency_map = {
    "us": "USD",
    "vn": "VND",
    "cn": "CNY",
    "hk": "HKD",
    "jp": "JPY",
    "kr": "KRW",
    "de": "EUR",
    "fr": "EUR",
    "it": "EUR",
    "es": "EUR",
    "ru": "RUB",
    "in": "INR",
    "id": "IDR",
    "th": "THB",
    "my": "MYR",
    "sg": "SGD",
    "ph": "PHP",
    "au": "AUD",
    "gb": "GBP",
    "ca": "CAD"
}

# =====================
# 爬取价格
# =====================
country_codes = list(country_currency_map.keys())
url_template = "https://apps.apple.com/{}/app/chatgpt/id6448311069"

results = []

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

for code in country_codes:
    url = url_template.format(code)
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Failed to fetch {code}: HTTP {response.status_code}")
            results.append({
                "country_code": code,
                "currency": country_currency_map.get(code, "Unknown"),
                "prices": "Error"
            })
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("li", class_="list-with-numbers__item")

        country_prices = []

        for item in items:
            title_tag = item.find("span", class_="list-with-numbers__item__title")
            price_tag = item.find("span", class_="list-with-numbers__item__price")

            if title_tag and price_tag:
                title = title_tag.get_text(strip=True)
                price = price_tag.get_text(strip=True)
                country_prices.append(f"{title}: {price}")

        if country_prices:
            results.append({
                "country_code": code,
                "currency": country_currency_map.get(code, "Unknown"),
                "prices": "; ".join(country_prices)
            })
        else:
            results.append({
                "country_code": code,
                "currency": country_currency_map.get(code, "Unknown"),
                "prices": "Not Found"
            })

        print(f"{code} done.")
        time.sleep(1)

    except Exception as e:
        print(f"Error fetching {code}: {e}")
        results.append({
            "country_code": code,
            "currency": country_currency_map.get(code, "Unknown"),
            "prices": "Error"
        })

# =====================
# 保存为 JSON 文件
# =====================
with open('chatgpt_app_store_prices_with_currency.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print("完成，文件已保存为 chatgpt_app_store_prices_with_currency.json")
