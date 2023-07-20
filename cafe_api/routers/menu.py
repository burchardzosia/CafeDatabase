from fastapi import APIRouter, Response
import pydantic_partial
from typing import Optional, Literal
from cafe_api.model import Model, db
from fastapi import HTTPException
import re
from cafe_api.parser import parse_tags_from_str

router = APIRouter(
    prefix='/menu',
    tags=['menu'],
)

class MenuInput(Model):
    name: str
    price: float
    tags: list[str]
    available: bool = True

class Menu(MenuInput):
    id: int

class MenuPatch(pydantic_partial.create_partial_model(MenuInput)):
    pass

@router.get('/', description='Get menu')
def get_menu(name: Optional[str] = None, available: Optional[bool] = None, price: Optional[float] = None, price_lt: Optional[float] = None,
             price_gt: Optional[float] = None, price_lte: Optional[float] = None, price_gte: Optional[float] = None,
             tags: Optional[str] = None, sort_by_price: Optional[Literal['asc', 'desc']] = None) -> list[Menu]:
    query = {}
    if name is not None:
        query['name'] = re.compile(name, re.IGNORECASE)
    if available is not None:
        query['available'] = available
    if price is not None:
        query['price'] = price
    if price_lt is not None:
        query['price'] = {'$lt': price_lt}
    if price_gt is not None:
        query['price'] = {'$gt': price_gt}
    if price_lte is not None:
        query['price'] = {'$lte': price_lte}
    if price_gte is not None:
        query['price'] = {'$gte': price_gte}
    if tags is not None:
        query['tags'] = {'$all': parse_tags_from_str(tags)}
    sort_query = {}
    if sort_by_price is not None:
        sort_query['price'] = sort_by_price
    return Menu.get_many(query, sort_query)

@router.get('/{id}', description='Get menu item')
def get_menu_item(id: int) -> Menu:
    return Menu.get_one(id)

@router.put('/', status_code=201, description='Add menu item')
def put_menu_item(_input: MenuInput) -> Menu:
    query = {}
    if _input.name is not None:
        query['name'] = _input.name
    if Menu.get_many(query):
        raise HTTPException(status_code=400, detail="The item is already in menu")
    if _input.price < 0:
        raise HTTPException(status_code=400, detail="The price cannot be lower than 0")
    return Menu.put_one(_input)

@router.put('/multi', status_code=202, description='Add multiple menu items')
def put_multiple_menu_items(_input: list[MenuInput]) -> list[Menu]:
    query = {}
    q_list = []
    for i in _input:
        if i.name is not None:
            q_list.append(i.name)
    query['name'] = {'$in': q_list}
    q_res = Menu.get_many(query)
    _input2 = _input
    for q in q_res:
        for i in _input:
            if q['name'] == i.name:
                _input2.remove(i)
    res = []
    for i in _input2:
        if i.price < 0:
            raise HTTPException(status_code=400, detail="The price cannot be lower than 0")
        res.append(Menu.put_one(i))
    return res

@router.patch('/{id}', description='Update menu item')
def patch_menu_item(id: int, patch: MenuPatch) -> Menu:
    if 'price' in patch and patch.price < 0:
        raise HTTPException(status_code=400, detail="The price cannot be lower than 0")
    return Menu.patch_one(id, patch)

@router.patch('/', description='Update multiple menu items')
def patch_menu_items(patch: MenuPatch, name: Optional[str] = None, available: Optional[bool] = None, price: Optional[float] = None, price_lt: Optional[float] = None,
             price_gt: Optional[float] = None, price_lte: Optional[float] = None, price_gte: Optional[float] = None,
             tags: Optional[str] = None) -> int:
    query = {}
    if name is not None:
        query['name'] = re.compile(name, re.IGNORECASE)
    if available is not None:
        query['available'] = available
    if price is not None:
        query['price'] = price
    if price_lt is not None:
        query['price'] = {'$lt': price_lt}
    if price_gt is not None:
        query['price'] = {'$gt': price_gt}
    if price_lte is not None:
        query['price'] = {'$lte': price_lte}
    if price_gte is not None:
        query['price'] = {'$gte': price_gte}
    if tags is not None:
        query['tags'] = {'$all': parse_tags_from_str(tags)}
    return Menu.patch_multiple(query, patch)


@router.delete('/{id}', status_code=204, description='Delete menu item')
def delete_menu_item(id: int) -> Response:
    Menu.delete_one(id)
    return Response(status_code=204)
