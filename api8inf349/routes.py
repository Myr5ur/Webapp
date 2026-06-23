from flask import Blueprint, jsonify, request, redirect, url_for, Response

from .models import Product, Order, ShippingInformation, OrderProduct
from .tasks import process_payment, order_to_dict
from .cache import get_cached_order
from .extensions import payment_queue
from .tasks import process_payment

bp = Blueprint("bp", __name__)


def compute_shipping(total_weight):
    if total_weight <= 500:
        return 5
    elif total_weight < 2000:
        return 10
    else:
        return 25


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
    
    cached = get_cached_order(order_id)
    if cached is not None:
        return jsonify({"order": cached})

    order = Order.get_or_none(Order.id == order_id)
    if order is None:
        return error_response(
            "order", "not-found", "La commande n'existe pas", 404)

    if order.processing:
        return Response(status=202, mimetype="application/json")

    return jsonify({"order": order_to_dict(order)})


@bp.route("/order/<int:order_id>", methods=["PUT"])
def update_order(order_id):
    order = Order.get_or_none(Order.id == order_id)
    if order is None:
        return error_response(
            "order", "not-found", "La commande n'existe pas", 404)

    if order.processing:
        return Response(status=409, mimetype="application/json")

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

        order.processing = True
        order.save()

        payment_queue.enqueue(process_payment, order.id, data["credit_card"])

        return Response(status=202, mimetype="application/json")


    return error_response(
        "order", "missing-fields",
        "La requête doit contenir soit des informations client, soit une carte de crédit", 422)