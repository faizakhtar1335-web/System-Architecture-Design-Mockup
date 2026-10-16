"""
Week 2 Task: System Architecture Design & Mockup
Project: ShopEase - Modular E-commerce Platform

This is a standard-library Python console mockup that demonstrates the
high-level interaction of catalogue, cart, inventory, checkout, payment,
and notification modules. It uses in-memory sample data. No real payment
is taken and no external service or database is required.

Run:
    python shopease_architecture_mockup.py
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List
from uuid import uuid4


@dataclass
class Product:
    product_id: str
    name: str
    price: float
    stock: int


@dataclass
class CartLine:
    product_id: str
    quantity: int


class CatalogueModule:
    def __init__(self):
        self.products: Dict[str, Product] = {
            "P101": Product("P101", "Wireless Mouse", 799.00, 10),
            "P102": Product("P102", "USB-C Cable", 299.00, 20),
            "P103": Product("P103", "Laptop Stand", 1299.00, 5),
        }

    def list_products(self) -> List[Product]:
        return list(self.products.values())

    def get_product(self, product_id: str) -> Product:
        product = self.products.get(product_id)
        if product is None:
            raise ValueError(f"Product ID '{product_id}' was not found.")
        return product


class CartModule:
    def __init__(self, catalogue: CatalogueModule):
        self.catalogue = catalogue
        self.lines: Dict[str, int] = {}

    def add_item(self, product_id: str, quantity: int) -> None:
        self.catalogue.get_product(product_id)
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero.")
        self.lines[product_id] = self.lines.get(product_id, 0) + quantity

    def get_lines(self) -> List[CartLine]:
        return [CartLine(product_id, quantity)
                for product_id, quantity in self.lines.items()]

    def calculate_total(self) -> float:
        return sum(
            self.catalogue.get_product(pid).price * quantity
            for pid, quantity in self.lines.items()
        )

    def clear(self) -> None:
        self.lines.clear()


class InventoryModule:
    def __init__(self, catalogue: CatalogueModule):
        self.catalogue = catalogue

    def check_stock(self, lines: List[CartLine]) -> None:
        for line in lines:
            product = self.catalogue.get_product(line.product_id)
            if line.quantity > product.stock:
                raise ValueError(
                    f"Not enough stock for {product.name}. "
                    f"Available: {product.stock}; requested: {line.quantity}."
                )

    def deduct_stock(self, lines: List[CartLine]) -> None:
        self.check_stock(lines)
        for line in lines:
            self.catalogue.get_product(line.product_id).stock -= line.quantity


class PaymentIntegration:
    """Mock payment adapter; it never contacts a real payment provider."""

    def process_payment(self, order_id: str, amount: float) -> str:
        if amount <= 0:
            raise ValueError("Payment amount must be positive.")
        print("[Payment] Simulated payment approved.")
        return f"DEMO-PAY-{order_id}"


class NotificationModule:
    def send_confirmation(self, email: str, order_id: str, total: float) -> None:
        print(f"[Notification] Order confirmation prepared for {email}.")
        print(f"[Notification] Order {order_id}, total Rs. {total:.2f}.")


class CheckoutModule:
    def __init__(
        self,
        catalogue: CatalogueModule,
        inventory: InventoryModule,
        payment: PaymentIntegration,
        notifications: NotificationModule,
    ):
        self.catalogue = catalogue
        self.inventory = inventory
        self.payment = payment
        self.notifications = notifications

    def checkout(self, email: str, cart: CartModule) -> dict:
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError("Enter a valid email address.")
        lines = cart.get_lines()
        if not lines:
            raise ValueError("Your cart is empty.")

        total = round(cart.calculate_total(), 2)
        self.inventory.check_stock(lines)
        order_id = uuid4().hex[:8].upper()

        # Demonstration only. A real system would use durable transactions,
        # idempotency keys, provider verification, and stock reconciliation.
        self.inventory.deduct_stock(lines)
        try:
            payment_reference = self.payment.process_payment(order_id, total)
        except Exception:
            # Restore stock if the simulated payment step fails.
            for line in lines:
                self.catalogue.get_product(line.product_id).stock += line.quantity
            raise

        order = {
            "order_id": order_id,
            "email": email,
            "total": total,
            "status": "CONFIRMED",
            "payment_reference": payment_reference,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        cart.clear()
        self.notifications.send_confirmation(email, order_id, total)
        return order


def show_architecture():
    print("\nSHOP EASE - ARCHITECTURE MOCKUP")
    print("-" * 46)
    print("Customer UI -> API / Application Layer")
    print("API -> Catalogue | Cart | Checkout")
    print("Checkout -> Inventory -> Payment Adapter")
    print("Checkout -> Order Record -> Notification Adapter")
    print("Business modules -> Repository -> Database (planned)")
    print("Payment / Email adapters -> External providers (planned)")
    print("-" * 46)


def main():
    catalogue = CatalogueModule()
    cart = CartModule(catalogue)
    inventory = InventoryModule(catalogue)
    payment = PaymentIntegration()
    notifications = NotificationModule()
    checkout = CheckoutModule(catalogue, inventory, payment, notifications)

    show_architecture()

    print("\nPRODUCT CATALOGUE")
    for product in catalogue.list_products():
        print(
            f"{product.product_id} | {product.name:<18} | "
            f"Rs. {product.price:.2f} | Stock: {product.stock}"
        )

    print("\nAdd items to the demo cart.")
    print("Enter a product ID shown above, or press Enter to finish.")
    while True:
        product_id = input("Product ID: ").strip().upper()
        if not product_id:
            break
        try:
            quantity = int(input("Quantity: ").strip())
            cart.add_item(product_id, quantity)
            print("Item added.")
        except ValueError as error:
            print(f"Could not add item: {error}")

    if not cart.lines:
        print("No items were added. Exiting without checkout.")
        return

    print(f"\nCart total: Rs. {cart.calculate_total():.2f}")
    email = input("Customer email for the mock checkout: ").strip()

    try:
        order = checkout.checkout(email, cart)
        print("\nORDER SUMMARY")
        print(f"Order ID:          {order['order_id']}")
        print(f"Status:             {order['status']}")
        print(f"Total:              Rs. {order['total']:.2f}")
        print(f"Payment reference:  {order['payment_reference']}")
        print(f"Created at:         {order['created_at']}")
        print("\nUpdated inventory:")
        for product in catalogue.list_products():
            print(f"{product.name}: {product.stock} remaining")
    except ValueError as error:
        print(f"Checkout could not be completed: {error}")


if __name__ == "__main__":
    main()
