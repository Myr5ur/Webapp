
import json
import urllib.request

PRODUCTS_URL = "https://dimensweb.uqac.ca/~jgnault/shops/products/"


def fetch_products():
    try:
        with urllib.request.urlopen(PRODUCTS_URL, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data.get("products", [])
    except Exception as exc:  
        print(f"[AVERTISSEMENT] Impossible de récupérer les produits : {exc}")
        return []
