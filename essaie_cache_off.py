import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:5000"

try:
    with urllib.request.urlopen(BASE + "/order/1") as r:
        print(f"GET /order/1 -> {r.status}")
        contenu = json.loads(r.read())
        print("Commande récupérée ! paid =", contenu["order"]["paid"])
        print("=> Elle vient de Redis (PostgreSQL est éteint)")
except urllib.error.HTTPError as e:
    print(f"GET /order/1 -> {e.code}")
    print("Erreur :", e.read().decode("utf-8", errors="replace")[:300])