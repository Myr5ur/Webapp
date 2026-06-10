
from flask import Blueprint, jsonify, request, redirect, url_for

from .models import Product, Order, ShippingInformation, CreditCard, Transaction, OrderProduct
from .payment import pay

bp = Blueprint("bp", __name__)

TAX_RATES = {
    "QC": 0.15,
    "ON": 0.13,
    "AB": 0.05,
    "BC": 0.12,
    "NS": 0.14,
}


def get_tax_rate(province):
    return TAX_RATES.get(province)


def compute_shipping(total_weight):
    if total_weight <= 500:
        return 5
    elif total_weight < 2000:
        return 10
    else:
        return 25


def order_to_dict(order):
    si = order.shipping_information
    cc = order.credit_card
    tr = order.transaction

    rate = get_tax_rate(si.province) if si else None
    total_price = order.total_price
    total_price_tax = round(total_price * (1 + rate), 2) if rate else total_price

    return {
        "id": order.id,
        "total_price": total_price,
        "total_price_tax": total_price_tax,
        "email": order.email,
        "paid": order.paid,
        "shipping_price": order.shipping_price,
        "products": [
            {"id": item.product.id,"quantity": item.quantity,
            }
            for item in order.items
        ],
        "shipping_information": {
            "country": si.country,
            "address": si.address,
            "postal_code": si.postal_code,
            "city": si.city,
            "province": si.province,
        } if si else {},
        "credit_card": {
            "name": cc.name,
            "first_digits": cc.first_digits,
            "last_digits": cc.last_digits,
            "expiration_year": cc.expiration_year,
            "expiration_month": cc.expiration_month,
        } if cc else {},
        "transaction": {
            "id": tr.id,
            "success": tr.success,
            "amount_charged": tr.amount_charged,
        } if tr else {},
    }


def error_response(category, code, name, status):
    return jsonify({"errors": {category: {"code": code, "name": name}}}), status



@bp.route("/", methods=["GET"])
def list_products():
    products = [
        {
            "id": p.id,
            "name": p.name,
            "in_stock": p.in_stock,
            "description": p.description,
            "price": p.price,
            "weight": p.weight,
            "image": p.image,
        }
        for p in Product.select()
    ]
    return jsonify({"products": products})


@bp.route("/order", methods=["POST"])
def create_order():
    data = request.get_json(silent=True) or {}
   
    if "products" in data:
        items = data["products"]
    elif "product" in data:
        items = [data["product"]]
    else:
        items = None

    if not items or not isinstance(items, list):
        return error_response(
            "product", "missing-fields",
            "La création d'une commande nécessite au moins un produit", 422)
    
    total_price = 0
    total_weight = 0
    produits_valides = []

    for item in items:
        if (not isinstance(item, dict)
                or "id" not in item or "quantity" not in item):
            return error_response(
                "product", "missing-fields",
                "La création d'une commande nécessite un produit", 422)

        quantity = item["quantity"]
        if not isinstance(quantity, int) or quantity < 1:
            return error_response(
                "product", "missing-fields",
                "La création d'une commande nécessite une quantité", 422)

        product = Product.get_or_none(Product.id == item["id"])
        if product is None:
            return error_response(
                "product", "missing-fields",
                "Le produit demandé n'existe pas", 422)

        if not product.in_stock:
            return error_response(
                "product", "out-of-inventory",
                "Le produit demandé n'est pas en inventaire", 422)

        total_price += product.price * quantity
        total_weight += product.weight * quantity
        produits_valides.append((product, quantity))
    
    order = Order.create(
        total_price=total_price,
        shipping_price=compute_shipping(total_weight),
    )

    for product, quantity in produits_valides:
        OrderProduct.create(order=order, product=product, quantity=quantity)

    return redirect(url_for("bp.get_order", order_id=order.id), code=302)


@bp.route("/order/<int:order_id>", methods=["GET"])
def get_order(order_id):
    order = Order.get_or_none(Order.id == order_id)
    if order is None:
        return error_response(
            "order", "not-found", "La commande n'existe pas", 404)
    return jsonify({"order": order_to_dict(order)})


@bp.route("/order/<int:order_id>", methods=["PUT"])
def update_order(order_id):
    order = Order.get_or_none(Order.id == order_id)
    if order is None:
        return error_response(
            "order", "not-found", "La commande n'existe pas", 404)

    data = request.get_json(silent=True) or {}


    if "order" in data and "credit_card" in data:
        return error_response(
            "order", "missing-fields",
            "Les informations du client et la carte de crédit doivent être "
            "envoyées dans deux requêtes distinctes", 422)

    if "order" in data:
        order_data = data["order"]
        email = order_data.get("email")
        shipping = order_data.get("shipping_information")

        if not email or not isinstance(shipping, dict):
            return error_response(
                "order", "missing-fields",
                "La mise à jour d'une commande nécessite un email et des informations de livraison", 422)
    
        champs_requis = ["country", "address", "postal_code", "city", "province"]
        for champ in champs_requis:
            if not shipping.get(champ):
                return error_response(
                    "order", "missing-fields",
                    "Il manque un ou plusieurs champs obligatoires", 422)

        info = ShippingInformation.create(
            country=shipping["country"],
            address=shipping["address"],
            postal_code=shipping["postal_code"],
            city=shipping["city"],
            province=shipping["province"],
        )
        order.email = email
        order.shipping_information = info
        order.save()
        return jsonify({"order": order_to_dict(order)})
    
    
    if "credit_card" in data:
        if not order.email or order.shipping_information is None:
            return error_response(
                "order", "missing-fields",
                "Le paiement d'une commande nécessite que les informations de livraison soient déjà complétées", 422)
        
        if order.paid:
            return error_response(
                "order", "already-paid",
                "Cette commande a déjà été payée", 422)
        
        rate = get_tax_rate(order.shipping_information.province) or 0
        montant = round(order.total_price * (1 + rate) + order.shipping_price,2)
        
        succes, donnees = pay(data["credit_card"], montant)

        if not succes:
            return jsonify(donnees), 422
        
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
        order.save()
        return jsonify({"order": order_to_dict(order)})
