import requests
from bs4 import BeautifulSoup
import json
import time
import re


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
# 定义格式化规则
# =====================
europe_countries = ["de", "fr", "it", "es"]
no_decimal_currencies = ["VND", "KRW", "JPY"]


# =====================
# 价格提取函数
# =====================
def parse_price(price_text, country_code, currency):
    """
    根据国家和货币规则，正确提取价格为float或int
    """
    # 欧洲（de, fr, it, es）用逗号作小数点，点作千位
    if country_code in europe_countries:
        price_text = price_text.replace(".", "").replace(",", ".")
    else:
        price_text = price_text.replace(",", "")

    # 提取数字部分
    match = re.search(r'[\d\.]+', price_text)
    if not match:
        return None

    num_str = match.group()

    try:
        # 无小数的国家（如JPY, VND, KRW）
        if currency in no_decimal_currencies:
            return int(float(num_str))
        else:
            return round(float(num_str), 2)
    except:
        return None


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
                "price_detail": "Error"
            })
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("li", class_="list-with-numbers__item")

        prices = []

        for item in items:
            price_tag = item.find("span", class_="list-with-numbers__item__price")

            if price_tag:
                price_text = price_tag.get_text(strip=True)
                price_value = parse_price(price_text, code, country_currency_map.get(code, "Unknown"))
                if price_value is not None:
                    prices.append(price_value)

        if len(prices) == 3:
            price_detail = {
                "plus_monthly": prices[0],
                "pro_monthly": prices[1],
                "plus_yearly": prices[2]
            }
        else:
            price_detail = "Not Found"

        results.append({
            "country_code": code,
            "currency": country_currency_map.get(code, "Unknown"),
            "price_detail": price_detail
        })

        print(f"{code} done.")
        time.sleep(1)

    except Exception as e:
        print(f"Error fetching {code}: {e}")
        results.append({
            "country_code": code,
            "currency": country_currency_map.get(code, "Unknown"),
            "price_detail": "Error"
        })

# =====================
# 保存为 JSON 文件
# =====================
with open('chatgpt_app_store_prices_structured.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print("完成，文件已保存为 chatgpt_app_store_prices_structured.json")
