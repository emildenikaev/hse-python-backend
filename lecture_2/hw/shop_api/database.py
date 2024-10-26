from uuid import uuid4
from .models import Item, Cart, CartItem

# Словари для хранения данных
items_db = {}
carts_db = {}

# Создание товара
def create_item(name: str, price: float) -> str:
    item_id = str(uuid4())
    items_db[item_id] = Item(id=item_id, name=name, price=price)
    return item_id

# Создание корзины
def create_cart() -> str:
    cart_id = str(uuid4())
    carts_db[cart_id] = Cart(id=cart_id, items=[], price=0.0)
    return cart_id

# Обновление общей стоимости корзины
def update_cart_price(cart: Cart) -> float:
    total_price = sum(
        item.quantity * items_db[item.id].price 
        for item in cart.items if item.id in items_db and not items_db[item.id].deleted
    )
    cart.price = total_price
    return total_price
