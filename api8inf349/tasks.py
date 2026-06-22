from .models import Order, CreditCard, Transaction
from .payment import pay
from .cache import cache_order


def process_payment(order_id, credit_card):
    from .routes import order_to_dict, get_tax_rate

    order = Order.get_or_none(Order.id == order_id)
    if order is None:
        return

    rate = get_tax_rate(order.shipping_information.province) or 0
    montant = round(order.total_price * (1 + rate) + order.shipping_price, 2)

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
            id=tr_data["id"],
            success=bool(tr_data["success"]),
            amount_charged=tr_data["amount_charged"],
        )
        order.credit_card = carte
        order.transaction = transaction
        order.paid = True
    else:
        err = donnees["errors"]["credit_card"]
        transaction = Transaction.create(
            id=f"failed-{order_id}",
            success=False,
            amount_charged=montant,
            error_code=err["code"],
            error_name=err["name"],
        )
        order.transaction = transaction
        order.paid = False

    order.payment_in_progress = False
    order.save()

    if order.paid:
        cache_order(order.id, order_to_dict(order))