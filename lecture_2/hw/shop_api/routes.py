from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from .models import Item, Cart, CartItem
from .database import items_db, carts_db, create_item, create_cart, update_cart_price

router = APIRouter()

# Роуты для управления товарами
@router.post("/item", response_model=Item, status_code=201)
def post_item(item: Item):
    if item.price <= 0:
        raise HTTPException(status_code=422, detail="Price must be positive")
    
    # Always create a new Item ID to ensure uniqueness
    item.id = create_item(item.name, item.price)

    return items_db[item.id]


@router.get("/item/{item_id}", response_model=Item)
def get_item(item_id: str):
    item = items_db.get(item_id)
    if not item or item.deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.delete("/item/{item_id}")
def delete_item(item_id: str):
    item = items_db.get(item_id)
    if item:
        item.deleted = True
    return {"detail": "Item deleted"}

@router.patch("/item/{item_id}")
def patch_item(item_id: str, item: Item):
    existing_item = items_db.get(item_id)
    if not existing_item or existing_item.deleted:
        raise HTTPException(status_code=404, detail="Item not found")

    if "deleted" in item.dict():
        raise HTTPException(status_code=422, detail="Cannot modify 'deleted' status")

    existing_data = existing_item.dict(exclude_unset=True)
    update_data = item.dict(exclude_unset=True)

    if field_difference := set(update_data.keys()) - set(existing_data.keys()):
        raise HTTPException(status_code=422, detail=f"Unexpected fields: {field_difference}")

    # Update fields
    if 'name' in update_data:
        existing_item.name = update_data['name']
    if 'price' in update_data:
        if update_data['price'] <= 0:
            raise HTTPException(status_code=422, detail="Price must be positive")
        existing_item.price = update_data['price']

    return existing_item


# Новый метод для получения списка товаров
@router.get("/item", response_model=List[Item])
def get_item_list(
    offset: Optional[int] = Query(default=0, ge=0),
    limit: Optional[int] = Query(default=10, gt=0),
    min_price: Optional[float] = Query(default=None, ge=0),
    max_price: Optional[float] = Query(default=None),
    show_deleted: Optional[bool] = Query(default=False)
):
    filtered_items = list(items_db.values())

    if not show_deleted:
        filtered_items = [item for item in filtered_items if not item.deleted]

    if min_price is not None:
        filtered_items = [item for item in filtered_items if item.price >= min_price]
    if max_price is not None:
        filtered_items = [item for item in filtered_items if item.price <= max_price]

    return filtered_items[offset:offset + limit]

# Новый метод для замены товара
@router.put("/item/{item_id}", response_model=Item)
def put_item(item_id: str, item: Item):
    existing_item = items_db.get(item_id)
    if not existing_item or existing_item.deleted:
        raise HTTPException(status_code=404, detail="Item not found")

    # Validate the entire item is being replaced without extra fields
    if set(item.dict().keys()) - {"name", "price", "id", "deleted"}:
        raise HTTPException(status_code=422, detail="Unexpected fields in the request body")

    # Replace all fields
    existing_item.name = item.name
    if item.price <= 0:
        raise HTTPException(status_code=422, detail="Price must be positive")
    existing_item.price = item.price

    return existing_item


# Роуты для управления корзинами
@router.post("/cart", response_model=dict, status_code=201)
def post_cart():
    cart_id = create_cart()
    return {"id": cart_id}

@router.get("/cart/{cart_id}", response_model=Cart)
def get_cart(cart_id: str):
    cart = carts_db.get(cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    update_cart_price(cart)  # Обновление цены корзины
    return cart

@router.post("/cart/{cart_id}/add/{item_id}", status_code=200)
def add_item_to_cart(cart_id: str, item_id: str):
    cart = carts_db.get(cart_id)
    item = items_db.get(item_id)

    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    if not item or item.deleted:
        raise HTTPException(status_code=404, detail="Item not found")

    item_in_cart = next((item for item in cart.items if item.id == item_id), None)

    if item_in_cart:
        item_in_cart.quantity += 1
    else:
        cart.items.append(CartItem(id=item_id, quantity=1))

    update_cart_price(cart)

    return {"detail": "Item added to cart"}



@router.get("/cart", response_model=List[Cart])
def get_cart_list(
    offset: Optional[int] = Query(default=0, ge=0),
    limit: Optional[int] = Query(default=10, ge=0),
    min_price: Optional[float] = Query(default=None, ge=0),
    max_price: Optional[float] = Query(default=None),
    min_quantity: Optional[int] = Query(default=None, ge=0),
    max_quantity: Optional[int] = Query(default=None, ge=0),
):
    filtered_carts = list(carts_db.values())
    
    if min_price is not None:
        filtered_carts = [cart for cart in filtered_carts if cart.price >= min_price]
    if max_price is not None:
        filtered_carts = [cart for cart in filtered_carts if cart.price <= max_price]
    
    total_quantity = sum(len(cart.items) for cart in filtered_carts)
    
    if min_quantity is not None and total_quantity < min_quantity:
        raise HTTPException(status_code=422, detail="Total quantity is less than min_quantity")
    if max_quantity is not None and total_quantity > max_quantity:
        raise HTTPException(status_code=422, detail="Total quantity is greater than max_quantity")

    return filtered_carts[offset:offset + limit]
