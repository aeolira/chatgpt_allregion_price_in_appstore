import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os
from dotenv import load_dotenv


# =====================
# 加载国家代码和货币映射
# =====================
load_dotenv('countrycode.env')
country_codes = os.getenv('COUNTRY_CODES').split(',')

with open('currency_map.json', 'r', encoding='utf-8') as f:
    currency_map = json.load(f)


# =====================
# 定义格式化规则
# =====================
europe_countries = ['de', 'fr', 'it', 'es', 'nl', 'pt', 'fi']  # 欧洲格式
no_decimal_currencies = ['JPY', 'KRW', 'VND']                 # 无小数


# =====================
# 价格提取函数
# =====================
def parse_price(price_text, country_code, currency):
    """
    根据国家和货币规则，正确提取价格为float或int
    """
    if country_code in europe_countries:
        price_text = price_text.replace('.', '').replace(',', '.')
    else:
        price_text = price_text.replace(',', '')

    match = re.search(r'[\d\.]+', price_text)
    if not match:
        return None

    num_str = match.group()

    try:
        if currency in no_decimal_currencies:
            return int(float(num_str))
        else:
            return round(float(num_str), 2)
    except:
        return None


# =====================
# 爬取价格
# =====================
url_template = "https://apps.apple.com/{}/app/chatgpt/id6448311069"

results = []

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

for code in country_codes:
    code = code.strip().lower()
    url = url_template.format(code)
    currency = currency_map.get(code, 'Unknown')

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Failed to fetch {code}: HTTP {response.status_code}")
            results.append({
                "country_code": code,
                "currency": currency,
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
                price_value = parse_price(price_text, code, currency)
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
            "currency": currency,
            "price_detail": price_detail
        })

        print(f"{code.upper()} ✅ Done.")
        time.sleep(1)

    except Exception as e:
        print(f"Error fetching {code}: {e}")
        results.append({
            "country_code": code,
            "currency": currency,
            "price_detail": "Error"
        })


# =====================
# 保存为 JSON 文件
# =====================
os.makedirs('output', exist_ok=True)

with open('output/chatgpt_app_store_prices_structured.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print("🎉 完成，文件已保存到 output/chatgpt_app_store_prices_structured.json")
