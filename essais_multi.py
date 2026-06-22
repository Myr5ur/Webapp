import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:5000"


def appel(methode, chemin, corps=None):
    data = json.dumps(corps).encode() if corps else None
    req = urllib.request.Request(
        BASE + chemin, data=data,
        headers={"Content-Type": "application/json"}, method=methode)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8", errors="replace"))


print("=== Commande multi-produits ===")
code, contenu = appel("POST", "/order", {
    "products": [
        {"id": 1, "quantity": 2},
        {"id": 3, "quantity": 1},
    ]
})
order_id = contenu["order"]["id"]
print(f"Commande créée, id = {order_id}")
print(json.dumps(contenu["order"]["products"], indent=2))
print("total_price :", contenu["order"]["total_price"])
print("shipping_price :", contenu["order"]["shipping_price"])

print("\n=== Commande un seul produit (ancien format) ===")
code, contenu = appel("POST", "/order", {
    "product": {"id": 1, "quantity": 1}
})
print(f"Commande créée, id = {contenu['order']['id']}")
print(json.dumps(contenu["order"]["products"], indent=2))