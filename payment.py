import json
import urllib.request
import urllib.error

PAYMENT_URL = "https://dimensweb.uqac.ca/~jgnault/shops/pay/"

def pay(credit_card, amount_charged):
    corps = json.dumps({
        "credit_card": credit_card,
        "amount_charged": amount_charged,
    }).encode("utf-8")

    request = urllib.request.Request(
        PAYMENT_URL,
        data=corps,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            donnees = json.loads(response.read().decode("utf-8"))
        return True, donnees
    except urllib.error.HTTPError as err:
        contenu = json.loads(err.read().decode("utf-8"))
        return False, contenu
    