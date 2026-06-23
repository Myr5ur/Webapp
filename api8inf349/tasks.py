from .models import DATABASE, Order, CreditCard, Transaction
from .payment import pay
from .cache import set_cached_order

def get_tax_rate(province):
    """Retourne le taux de taxe basé sur la province (Exigences Partie 1)."""
    taxes = {
        "QC": 0.15,  
        "ON": 0.13,  
        "AB": 0.05,  
        "BC": 0.12,  
        "NS": 0.14   
    }
    return taxes.get(province, 0.0)

def order_to_dict(order):
    """Sérialise un objet Order en dictionnaire pour Redis et les réponses JSON."""
    rate = 0.0
    shipping_info = {}
    
    if order.shipping_information:
        si = order.shipping_information
        rate = get_tax_rate(si.province)
        shipping_info = {
            "country": si.country,
            "address": si.address,
            "postal_code": si.postal_code,
            "city": si.city,
            "province": si.province
        }

    cc_info = {}
    if order.credit_card:
        cc = order.credit_card
        cc_info = {
            "name": cc.name,
            "first_digits": str(cc.first_digits),
            "last_digits": str(cc.last_digits),
            "expiration_year": cc.expiration_year,
            "expiration_month": cc.expiration_month
        }

    tr_info = {}
    if order.transaction:
        tr = order.transaction
        tr_info = {
            "id": tr.remote_id if hasattr(tr, 'remote_id') else tr.id,
            "success": tr.success,
            "amount_charged": tr.amount_charged
        }
        if not tr.success:
            tr_info["error"] = {
                "code": getattr(tr, 'error_code', 'card-declined'),
                "name": getattr(tr, 'error_name', 'La carte de crédit a été déclinée.')
            }

    products_list = [
        {"id": op.product.id, "quantity": op.quantity}
        for op in order.items
    ]
           

    return {
        "id": order.id,
        "total_price": order.total_price,
        "total_price_tax": round(order.total_price * (1 + rate), 2),
        "email": order.email,
        "credit_card": cc_info,
        "shipping_information": shipping_info,
        "paid": order.paid,
        "transaction": tr_info,
        "products": products_list,
        "shipping_price": order.shipping_price
    }


def process_payment(order_id, credit_card):
    DATABASE.connect(reuse_if_open=True)
    try:
        order = Order.get_or_none(Order.id == order_id)
        if order is None:
            return

        rate = get_tax_rate(order.shipping_information.province) or 0
        montant = round(
            order.total_price * (1 + rate) + order.shipping_price, 2
        )

        succes, donnees = pay(credit_card, montant)

        if succes:
            cc_data = donnees["credit_card"]
            carte = CreditCard.create(
                name=cc_data["name"],
                first_digits=str(cc_data["first_digits"]),
                last_digits=str(cc_data["last_digits"]),
                expiration_year=cc_data["expiration_year"],
                expiration_month=cc_data["expiration_month"],
            )

            tr_data = donnees["transaction"]
            transaction = Transaction.create(
                remote_id=tr_data.get("id"),
                success=True,
                amount_charged=tr_data.get("amount_charged"),
            )

            order.credit_card = carte
            order.transaction = transaction
            order.paid = True
        else:
            erreur = (
                donnees.get("errors", {}).get("credit_card")
                or donnees.get("errors", {}).get("order")
                or {"code": "unknown-error", "name": "Erreur de paiement inconnue"}
            )
            transaction = Transaction.create(
                remote_id=None,
                success=False,
                amount_charged=montant,
                error_code=erreur.get("code"),
                error_name=erreur.get("name"),
            )
            order.transaction = transaction
            order.paid = False

        order.processing = False
        order.save()

        set_cached_order(order.id, order_to_dict(order))
    finally:
        if not DATABASE.is_closed():
            DATABASE.close()