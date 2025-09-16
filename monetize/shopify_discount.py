import os
import random
import string

import requests

STORE = os.getenv("SHOPIFY_STORE", "")  # yourshop.myshopify.com
TOKEN = os.getenv("SHOPIFY_ADMIN_TOKEN", "")  # Admin API access token


def gen_code(prefix="WAN"):
    return prefix + "-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def create_discount():
    if not STORE or not TOKEN:
        return ""
    code = gen_code()
    hdr = {"X-Shopify-Access-Token": TOKEN, "Content-Type": "application/json"}
    # 価格ルールをシンプルに10%OFF・即時・無期限で作成
    rule = {
        "price_rule": {
            "title": code,
            "target_type": "line_item",
            "target_selection": "all",
            "allocation_method": "across",
            "value_type": "percentage",
            "value": "-10.0",
            "customer_selection": "all",
            "starts_at": "2020-01-01T00:00:00Z",
        }
    }
    r = requests.post(
        f"https://{STORE}/admin/api/2023-10/price_rules.json", headers=hdr, json=rule, timeout=30
    )
    r.raise_for_status()
    rule_id = r.json()["price_rule"]["id"]
    r2 = requests.post(
        f"https://{STORE}/admin/api/2023-10/price_rules/{rule_id}/discount_codes.json",
        headers=hdr,
        json={"discount_code": {"code": code}},
        timeout=30,
    )
    r2.raise_for_status()
    return code


if __name__ == "__main__":
    print(create_discount())
