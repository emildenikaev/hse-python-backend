from fastapi import APIRouter, HTTPException, Response, status, Query
from pydantic import BaseModel, NonNegativeInt, PositiveInt, NonNegativeFloat
from typing import List
from models import Item, Cart, CartItem
from database import items_db, carts_db, next_item_id, next_cart_id

def item_exists(item_id):
    return item_id in items_db and not items_db[item_id].deleted

def cart_exists(cart_id):
    return cart_id in carts_db

router = APIRouter()

@router.post('/item', status_code=status.HTTP_201_CREATED)
def create_item(item: Item, response: Response):
    global next_item_id
    item.id = next_item_id
    items_db[next_item_id] = item
    next_item_id += 1
    response.headers["Location"] = f'/item/{item.id}'
    return item

@router.get("/item/{id}")
def get_item(id: int):
    if not item_exists(id):
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[id]


@router.get("/item")
def list_items(
    offset: NonNegativeInt = 0,
    limit: PositiveInt = 10,
    min_price: NonNegativeFloat = None,
    max_price: NonNegativeFloat = None,
    show_deleted: bool = False
):
    items = [item for item in items_db.values() if show_deleted or not item.deleted]
    if min_price is not None:
        items = [item for item in items if item.price >= min_price]
    if max_price is not None:
        items = [item for item in items if item.price <= max_price]
    return items[offset:offset + limit]


@router.put("/item/{id}")
def update_item(id: int, item: Item):
    if not item_exists(id):
        raise HTTPException(status_code=404, detail="Item not found")
    item.id = id
    items_db[id] = item
    return item


@router.patch("/item/{id}")
def patch_item(id: int, item: dict):
    item_to_patch = items_db.get(id)
    if not item_to_patch or item_to_patch.deleted:
        raise HTTPException(status_code=304,
                            detail="Item not modified")

    for key, value in item.items():
        if key == "deleted" and value:
            raise HTTPException(status_code=422,
                                detail="Cannot delete item")
        if not hasattr(item_to_patch, key):
            raise HTTPException(status_code=422,
                                detail=f"Attribute '{key}' not found")
        setattr(item_to_patch, key, value)

    return item_to_patch

@router.delete("/item/{id}")
def delete_item(id: int):
    if id not in items_db:
        raise HTTPException(status_code=404,
                            detail="Item not found")
    item = items_db[id]
    item.deleted = True
    return item

@router.post("/cart", status_code=status.HTTP_201_CREATED)
def create_cart(response: Response):
    global next_cart_id
    cart = Cart(id=next_cart_id)
    carts_db[next_cart_id] = cart
    next_cart_id += 1
    response.headers["Location"] = f'/cart/{cart.id}'
    return {"id": cart.id}

@router.get("/cart/{id}")
def get_cart(id: int):
    if not cart_exists(id):
        raise HTTPException(status_code=404, detail="Cart not found")
    return carts_db[id]


@router.get("/cart")
def list_carts(
    offset: NonNegativeInt = 0,
    limit: PositiveInt = 10,
    min_price: NonNegativeFloat = None,
    max_price: NonNegativeFloat = None,
    min_quantity: NonNegativeInt = None,
    max_quantity: NonNegativeInt = None
):
    carts = list(carts_db.values())
    if min_price is not None:
        carts = [cart for cart in carts if cart.price >= min_price]
    if max_price is not None:
        carts = [cart for cart in carts if cart.price <= max_price]
    if min_quantity is not None:
        carts = [cart for cart in carts if sum(item.quantity for item in cart.items) >= min_quantity]
    if max_quantity is not None:
        carts = [cart for cart in carts if sum(item.quantity for item in cart.items) <= max_quantity]
    return carts[offset:offset + limit]


@router.post('/cart/{cart_id}/add/{item_id}')
def add_item_to_cart(cart_id: int, item_id: int):
    if not cart_exists(cart_id):
        raise HTTPException(status_code=404, detail="Cart not found")
    if not item_exists(item_id):
        raise HTTPException(status_code=404, detail="Item not found or deleted")

    cart = carts_db[cart_id]
    item = items_db[item_id]

    for cart_item in cart.items:
        if cart_item.id == item.id:
            cart_item.quantity += 1
            break
    else:
        cart.items.append(CartItem(id=item.id, name=item.name, quantity=1))

    cart.price += item.price
    return {"status": "Item added"}


@router.delete('/cart/{cart_id}/remove/{item_id}')
def remove_item_from_cart(cart_id: int, item_id: int):
    if not cart_exists(cart_id):
        raise HTTPException(status_code=404, detail="Cart not found")
    if not item_exists(item_id):
        raise HTTPException(status_code=404, detail="Item not found or deleted")

    cart = carts_db[cart_id]
    for cart_item in cart.items:
        if cart_item.id == item_id:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                cart.items.remove(cart_item)
            cart.price -= items_db[item_id].price
            return {"status": "Item removed"}

    raise HTTPException(status_code=404, detail="Item not found in cart")


@router.delete('/cart/{cart_id}')
def delete_cart(cart_id: int):
    if not cart_exists(cart_id):
        raise HTTPException(status_code=404, detail="Cart not found")
    del carts_db[cart_id]
    return {"status": "Cart deleted"}
