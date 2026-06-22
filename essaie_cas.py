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
            c = r.read()
            return r.status, (json.loads(c) if c else None)
    except urllib.error.HTTPError as e:
        c = e.read()
        try:
            return e.code, json.loads(c)
        except json.JSONDecodeError:
            return e.code, None


def creer_commande():
    code, contenu = appel("POST", "/order", {"product": {"id": 1, "quantity": 1}})
    chemin = f"/order/{contenu['order']['id']}"
    appel("PUT", chemin, {
        "order": {
            "email": "jgnault@uqac.ca",
            "shipping_information": {
                "country": "Canada", "address": "201, rue Président-Kennedy",
                "postal_code": "G7X 3Y7", "city": "Chicoutimi", "province": "QC",
            }
        }
    })
    return chemin


CARTE_VALIDE = {
    "name": "John Doe", "number": "4242 4242 4242 4242",
    "expiration_year": 2026, "cvv": "123", "expiration_month": 9,
}
CARTE_REFUSEE = {
    "name": "John Doe", "number": "4000 0000 0000 0002",
    "expiration_year": 2026, "cvv": "123", "expiration_month": 9,
}


print("=== CAS 409 : re-payer pendant le traitement ===")
chemin = creer_commande()
code1, _ = appel("PUT", chemin, {"credit_card": CARTE_VALIDE})
code2, _ = appel("PUT", chemin, {"credit_card": CARTE_VALIDE})
print(f"1er paiement -> {code1} (attendu 202)")
print(f"2e paiement immédiat -> {code2} (attendu 409)")
time.sleep(2)  


print("\n=== CAS carte refusée : erreur persistée ===")
chemin = creer_commande()
code, _ = appel("PUT", chemin, {"credit_card": CARTE_REFUSEE})
print(f"Paiement (carte refusée) -> {code} (attendu 202)")

contenu = None
for i in range(10):
    time.sleep(1)
    code, contenu = appel("GET", chemin)
    if code == 200:
        break

print(f"GET après traitement -> {code} (attendu 200, PAS 422)")
if contenu:
    print("paid =", contenu["order"]["paid"], "(attendu False)")
    print("transaction :", json.dumps(contenu["order"]["transaction"], indent=2, ensure_ascii=False))