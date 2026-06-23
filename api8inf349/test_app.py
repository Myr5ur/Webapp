import pytest

from api8inf349 import create_app
from api8inf349.models import (
    DATABASE, Product, Order, ShippingInformation, CreditCard, Transaction,
    ALL_MODELS,
)


@pytest.fixture
def app():

    application = create_app(skip_product_load=True)

    DATABASE.connect(reuse_if_open=True)
    DATABASE.create_tables(ALL_MODELS)

    Product.insert(id=1, name="Brown eggs", description="Des oeufs",
                   price=28.1, in_stock=True, weight=400,
                   image="0.jpg").on_conflict_replace().execute()
    Product.insert(id=2, name="Produit en rupture", description="Indisponible",
                   price=10.0, in_stock=False, weight=100,
                   image="1.jpg").on_conflict_replace().execute()

    DATABASE.close()
    yield application

    DATABASE.connect(reuse_if_open=True)
    Order.delete().execute()
    Transaction.delete().execute()
    CreditCard.delete().execute()
    ShippingInformation.delete().execute()
    DATABASE.close()


@pytest.fixture
def client(app):
    return app.test_client()



def test_liste_produits(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "products" in data
    assert len(data["products"]) == 2


def test_creer_commande_sans_produit(client):
    resp = client.post("/order", json={})
    assert resp.status_code == 422
    assert resp.get_json()["errors"]["product"]["code"] == "missing-fields"


def test_creer_commande_quantite_invalide(client):
    resp = client.post("/order", json={"product": {"id": 1, "quantity": 0}})
    assert resp.status_code == 422
    assert resp.get_json()["errors"]["product"]["code"] == "missing-fields"


def test_creer_commande_produit_en_rupture(client):
    resp = client.post("/order", json={"product": {"id": 2, "quantity": 1}})
    assert resp.status_code == 422
    assert resp.get_json()["errors"]["product"]["code"] == "out-of-inventory"


def test_creer_commande_succes(client):
    resp = client.post("/order", json={"product": {"id": 1, "quantity": 2}})
    assert resp.status_code == 302
    assert "/order/" in resp.headers["Location"]


def test_consulter_commande(client):
    creation = client.post("/order", json={"product": {"id": 1, "quantity": 2}})
    location = creation.headers["Location"]

    resp = client.get(location)
    assert resp.status_code == 200
    order = resp.get_json()["order"]
    assert order["total_price"] == 56.2          
    assert order["shipping_price"] == 10          
    assert order["paid"] is False


def test_consulter_commande_inexistante(client):
    resp = client.get("/order/9999")
    assert resp.status_code == 404


def test_put_information_client(client):
    creation = client.post("/order", json={"product": {"id": 1, "quantity": 2}})
    location = creation.headers["Location"]

    resp = client.put(location, json={
        "order": {
            "email": "jgnault@uqac.ca",
            "shipping_information": {
                "country": "Canada",
                "address": "201, rue Président-Kennedy",
                "postal_code": "G7H 3Y7",
                "city": "Chicoutimi",
                "province": "QC",
            },
        }
    })
    assert resp.status_code == 200
    order = resp.get_json()["order"]
    assert order["email"] == "jgnault@uqac.ca"
    assert order["shipping_information"]["province"] == "QC"
    assert order["total_price_tax"] == 64.63


def test_put_champ_manquant(client):
    creation = client.post("/order", json={"product": {"id": 1, "quantity": 1}})
    location = creation.headers["Location"]

    resp = client.put(location, json={
        "order": {
            "email": "jgnault@uqac.ca",
            "shipping_information": {"country": "Canada", "province": "QC"},
        }
    })
    assert resp.status_code == 422
    assert resp.get_json()["errors"]["order"]["code"] == "missing-fields"


def test_put_carte_et_infos_ensemble(client):
    creation = client.post("/order", json={"product": {"id": 1, "quantity": 1}})
    location = creation.headers["Location"]

    resp = client.put(location, json={
        "order": {"email": "a@b.ca"},
        "credit_card": {"name": "John Doe"},
    })
    assert resp.status_code == 422
    assert resp.get_json()["errors"]["order"]["code"] == "missing-fields"


REPONSE_SUCCES = {
    "credit_card": {
        "name": "John Doe", "first_digits": "4242", "last_digits": "4242",
        "expiration_year": 2026, "expiration_month": 9,
    },
    "transaction": {
        "id": "test-transaction-123", "success": True, "amount_charged": 3731,
    },
}
REPONSE_REFUS = {
    "errors": {
        "credit_card": {
            "code": "card-declined",
            "name": "La carte de crédit a été déclinée",
        }
    }
}
CARTE = {
    "name": "John Doe", "number": "4242 4242 4242 4242",
    "expiration_year": 2026, "cvv": "123", "expiration_month": 9,
}


def _commande_avec_adresse(client):
    creation = client.post("/order", json={"product": {"id": 1, "quantity": 1}})
    location = creation.headers["Location"]
    client.put(location, json={
        "order": {
            "email": "jgnault@uqac.ca",
            "shipping_information": {
                "country": "Canada", "address": "201, rue Président-Kennedy",
                "postal_code": "G7X 3Y7", "city": "Chicoutimi", "province": "QC",
            }
        }
    })
    return location


def test_paiement_succes(client, monkeypatch):
    monkeypatch.setattr("api8inf349.routes.pay",
                        lambda cc, montant: (True, REPONSE_SUCCES))

    location = _commande_avec_adresse(client)
    resp = client.put(location, json={"credit_card": CARTE})

    assert resp.status_code == 200
    order = resp.get_json()["order"]
    assert order["paid"] is True
    assert order["transaction"]["id"] == "test-transaction-123"


def test_paiement_carte_refusee(client, monkeypatch):
    monkeypatch.setattr("api8inf349.routes.pay",
                        lambda cc, montant: (False, REPONSE_REFUS))

    location = _commande_avec_adresse(client)
    resp = client.put(location, json={"credit_card": CARTE})

    assert resp.status_code == 422
    assert resp.get_json()["errors"]["credit_card"]["code"] == "card-declined"


def test_paiement_sans_adresse(client, monkeypatch):
    monkeypatch.setattr("api8inf349.routes.pay",
                        lambda cc, montant: (True, REPONSE_SUCCES))

    creation = client.post("/order", json={"product": {"id": 1, "quantity": 1}})
    location = creation.headers["Location"]
    resp = client.put(location, json={"credit_card": CARTE})

    assert resp.status_code == 422
    assert resp.get_json()["errors"]["order"]["code"] == "missing-fields"


def test_paiement_deja_payee(client, monkeypatch):
    monkeypatch.setattr("api8inf349.routes.pay",
                        lambda cc, montant: (True, REPONSE_SUCCES))

    location = _commande_avec_adresse(client)
    client.put(location, json={"credit_card": CARTE})          
    resp = client.put(location, json={"credit_card": CARTE})    

    assert resp.status_code == 422
    assert resp.get_json()["errors"]["order"]["code"] == "already-paid"
