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


# 1. Créer une commande
code, contenu = appel("POST", "/order", {"product": {"id": 1, "quantity": 1}})
order_id = contenu["order"]["id"]
chemin = f"/order/{order_id}"
print(f"Commande créée, id = {order_id}")

# 2. Ajouter l'adresse
appel("PUT", chemin, {
    "order": {
        "email": "jgnault@uqac.ca",
        "shipping_information": {
            "country": "Canada", "address": "201, rue Président-Kennedy",
            "postal_code": "G7X 3Y7", "city": "Chicoutimi", "province": "QC",
        }
    }
})
print("Adresse ajoutée")

# 3. Payer (carte valide) -> la commande doit être mise en cache
code, contenu = appel("PUT", chemin, {
    "credit_card": {
        "name": "John Doe", "number": "4242 4242 4242 4242",
        "expiration_year": 2026, "cvv": "123", "expiration_month": 9,
    }
})
print(f"Paiement -> code {code}, paid =", contenu.get("order", {}).get("paid"))

# 4. Consulter la commande -> doit venir du cache Redis
code, contenu = appel("GET", chemin)
print(f"Consultation -> code {code}")
print(json.dumps(contenu["order"], indent=2, ensure_ascii=False))