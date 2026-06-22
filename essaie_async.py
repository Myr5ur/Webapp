import json
import time
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
            corps_rep = r.read()
            contenu = json.loads(corps_rep) if corps_rep else None
            return r.status, contenu
    except urllib.error.HTTPError as e:
        corps_rep = e.read()
        try:
            return e.code, json.loads(corps_rep)
        except json.JSONDecodeError:
            return e.code, None


code, contenu = appel("POST", "/order", {"product": {"id": 1, "quantity": 1}})
order_id = contenu["order"]["id"]
chemin = f"/order/{order_id}"
appel("PUT", chemin, {
    "order": {
        "email": "jgnault@uqac.ca",
        "shipping_information": {
            "country": "Canada", "address": "201, rue Président-Kennedy",
            "postal_code": "G7X 3Y7", "city": "Chicoutimi", "province": "QC",
        }
    }
})
print(f"Commande {order_id} créée avec adresse")

code, _ = appel("PUT", chemin, {
    "credit_card": {
        "name": "John Doe", "number": "4242 4242 4242 4242",
        "expiration_year": 2026, "cvv": "123", "expiration_month": 9,
    }
})
print(f"Paiement demandé -> code {code} (attendu : 202)")

code, _ = appel("GET", chemin)
print(f"Consultation immédiate -> code {code} (202 = en cours, 200 = déjà fini)")

print("Attente du worker...")
for i in range(10):
    time.sleep(1)
    code, contenu = appel("GET", chemin)
    if code == 200:
        print(f"-> code 200 après {i+1}s ! paid =", contenu["order"]["paid"])
        break
else:
    print("Toujours en cours après 10s (souci ?)")