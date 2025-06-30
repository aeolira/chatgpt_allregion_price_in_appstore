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
# 格式化规则
# =====================
europe_countries = ['de', 'fr', 'it', 'es', 'nl', 'pt', 'fi']  # 欧洲格式
no_decimal_currencies = ['JPY', 'KRW', 'VND']                 # 无小数


# =====================
# 提取货币符号和数值
# =====================
def extract_currency_and_price(price_text):
    """
    提取货币符号（$、USD、€）和价格数字
    返回：(currency_symbol, number_string)
    """
    price_text = price_text.replace('\xa0', ' ').strip()

    # 修复潜在乱码
    price_text = price_text.encode('latin1', errors='ignore').decode('utf-8', errors='ignore')

    # 带货币代码：USD 19.99
    match = re.match(r'^([A-Z]{2,3})\s*([\d\.,]+)', price_text)
    if match:
        return match.group(1), match.group(2)

    # 带货币符号：$19.99, €19,99
    match = re.match(r'^([^\d\s]+)\s*([\d\.,]+)', price_text)
    if match:
        return match.group(1), match.group(2)

    # 没有货币符号，返回None
    return None, price_text


# =====================
# 数字标准化
# =====================
def parse_price(num_str, country_code, currency):
    """
    根据国家和货币规则，格式化价格
    """
    if country_code in europe_countries:
        num_str = num_str.replace('.', '').replace(',', '.')
    else:
        num_str = num_str.replace(',', '')

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
    default_currency = currency_map.get(code, 'Unknown')

    try:
        response = requests.get(url, headers=headers, timeout=15)

        # 🔥 修复乱码关键一行
        response.encoding = response.apparent_encoding

        if response.status_code != 200:
            print(f"❌ Failed {code}: HTTP {response.status_code}")
            results.append({
                "country_code": code,
                "currency": default_currency,
                "price_detail": "Error"
            })
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("li", class_="list-with-numbers__item")

        prices = []
        currencies_detected = []

        for item in items:
            price_tag = item.find("span", class_="list-with-numbers__item__price")
            if price_tag:
                price_text = price_tag.get_text(strip=True)

                currency_symbol, num_str = extract_currency_and_price(price_text)

                currency = currency_symbol if currency_symbol else default_currency
                price_value = parse_price(num_str, code, currency)

                if price_value is not None:
                    prices.append(price_value)
                    currencies_detected.append(currency)

        if len(prices) == 3:
            price_detail = {
                "plus_monthly": prices[0],
                "pro_monthly": prices[1],
                "plus_yearly": prices[2]
            }
        else:
            price_detail = "Not Found"

        currency_final = max(set(currencies_detected), key=currencies_detected.count) if currencies_detected else default_currency

        results.append({
            "country_code": code,
            "currency": currency_final,
            "price_detail": price_detail
        })

        print(f"✅ {code.upper()} Done.")
        time.sleep(1)

    except Exception as e:
        print(f"❌ Error {code}: {e}")
        results.append({
            "country_code": code,
            "currency": default_currency,
            "price_detail": "Error"
        })


# =====================
# 保存为 JSON 文件
# =====================
os.makedirs('output', exist_ok=True)

with open('output/chatgpt_app_store_prices_structured.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=4)

print("🎉 完成，文件已保存到 output/chatgpt_app_store_prices_structured.json")
