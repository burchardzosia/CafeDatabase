from http.client import HTTPException

import datetime
from fastapi import HTTPException
from fastapi import APIRouter, Response
import pydantic_partial
from pydantic import BaseModel
from typing import Optional, List, Any, Literal
from cafe_api.model import Model
from cafe_api.routers.games import Games, add_reservation_to_game
from cafe_api.parser import parse_tags_from_str
from datetime import datetime
import re

from cafe_api.routers.tables import Tables, add_reservation_to_table
from cafe_api.routers.menu import Menu, get_menu

router = APIRouter(
    prefix='/reservations',
    tags=['reservations'],
)


class OrderedFood(BaseModel):
    name: str
    quantity: int
    price: float | None

    def lookup_food(self) -> tuple[bool, float]:  # sprawdza czy jest w menu/jest dostępne, zwraca wynik + obecną cenę
        result_list = get_menu(name=self.name)
        if not result_list:
            return (False, 0)
        return (result_list[0]['available'], result_list[0]['price'])


class ReservationsInput(Model):
    startTime: datetime
    endTime: datetime
    games: list[dict] | None  # (id, nazwa)
    orderedFood: list[dict] | None  # id, nazwa, ilość, cena
    clients: int  # ile ludzi
    clientName: str  # na jakie nazwisko
    tables: list[int]  # id stołu


class Reservations(ReservationsInput):
    id: int


class ReservationsPatch(pydantic_partial.create_partial_model(ReservationsInput)):
    pass


@router.get('/', description='Get reservations')
def get_reservations(startNow: bool = False, clients: Optional[int] = None, clientName: Optional[str] = None,
                     gteStartTime: Optional[datetime] = None,
                     lteStartTime: Optional[datetime] = None, lteEndTime: Optional[datetime] = None,
                     gteEndTime: Optional[datetime] = None, gameList: Optional[str] = None,
                     sortByStart: Optional[Literal['asc', 'desc']] = None):
    query = {}
    if clients is not None:
        query['clients'] = clients
    if clientName is not None:
        query['clientName'] = re.compile(clientName, re.IGNORECASE)
    if gameList is not None:
        parsedList = parse_tags_from_str(gameList)
        query['games.name'] = {'$in': parsedList}
    sort_query = {}
    if startNow:
        query['endTime'] = {'$gte': datetime.now()}
        sort_query['startTime'] = 'asc'
    else:
        if gteStartTime is not None:
            query['startTime'] = {'$gte': gteStartTime}
        if lteStartTime is not None:
            query['startTime'] = {'$lte': lteStartTime}
        if gteEndTime is not None:
            query['endTime'] = {'$gte': gteEndTime}
        if lteEndTime is not None:
            query['endTime'] = {'$lte': lteEndTime}
    sort_query = {}
    if sortByStart is not None:
        sort_query['startTime'] = sortByStart
    return Reservations.get_many(query, sort_query)


@router.get('/{id}', description='Get one reservation item by id')
def get_reservation_item(id: int) -> dict:
    reservation = Reservations.get_one(id)
    return {'reservation': reservation, 'total_price': calculate_total_price(reservation)}


def calculate_total_price(reservation: Reservations) -> float:
    total = 0
    for food in reservation['orderedFood']:
        total += food['price'] * food['quantity']
    return total


@router.put('/', status_code=201, description='Add a reservation')
def put_reservation_item(_input: ReservationsInput, _food: list[OrderedFood]) -> Reservations:
    newGameList = []
    for game in _input.games:
        if 'id' in game:
            if not check_game_availability(game['id'], _input.startTime, _input.endTime):
                raise HTTPException(status_code=400,
                                    detail=f"Gra o ID {game['id']} ({game['name']}) nie jest dostępna w podanym czasie.")
            newGameList.append({'id': game['id'], 'name': game['name']})
    _input.games = newGameList
    tables = check_chairs_availability(_input.clients, _input.startTime,
                                       _input.endTime)
    _input.tables = tables
    newFoodList = []
    for f in _food:
        res = f.lookup_food()
        if res[0] > 0:
            f.price = res[1]
            newFoodList.append({'name': f.name, 'price': f.price, 'quantity': f.quantity})
        else:
            raise HTTPException(status_code=400,
                                detail=f"Jedzenie {f.name} nie istnieje/nie jest dostępne")
                                
    _input.orderedFood = newFoodList

    result = Reservations.put_one(_input)
    for game in _input.games:
        if 'id' in game:
            add_reservation_to_game(game['id'], result['id'], _input.startTime, _input.endTime)
    for table in tables:
        add_reservation_to_table(table, result['id'], _input.startTime, _input.endTime)
    result = Reservations.get_one(result['id'])
    return result


@router.patch('/{id}', description='Update a reservation')
def patch_reservation_item(id: int, patch: ReservationsPatch) -> Reservations:
    return Reservations.patch_one(id, patch)


@router.patch('/{id}/food', description='Order more food')
def add_reservation_food(id: int, _food: list[OrderedFood]):
    newFoodList = []
    for f in _food:
        res = f.lookup_food()
        if res[0] > 0:
            f.price = res[1]
            newFoodList.append({'name': f.name, 'price': f.price, 'quantity': f.quantity})
        else:
            raise HTTPException(status_code=400,
                                detail=f"Jedzenie {f.name} nie istnieje/nie jest dostępne")
    Reservations.get_collection().update_one({'id': id}, {'$push': {'orderedFood': {'$each': newFoodList}}})
    return Reservations.get_one(id)


@router.delete('/{id}', status_code=204, description='Delete a reservation')
def delete_reservation_item(id: int) -> Response:
    Reservations.delete_one(id)
    return Response(status_code=204)


def check_game_availability(game_id: int, start_time: datetime, end_time: datetime) -> bool:
    game = Games.get_one(game_id)
    counter = 0
    reservations = game.get('reservations', [])
    for index, reservation in enumerate(reservations):
        if index > 0:  # Pomijamy pierwszy element listy
            if (start_time.astimezone() <= reservation['start_time'].astimezone() <= end_time.astimezone()) or (
                    start_time.astimezone() <= reservation['end_time'].astimezone() <= end_time.astimezone()):
                counter += 1
    if counter < game.get('unitsInStock'):
        return True


def check_chairs_availability(clients: int, start_time: datetime, end_time: datetime) -> list[Any]:
    clients_tmp = clients
    tables = Tables.get_many()
    table_id = []

    for table in tables:
        flag = True
        if clients_tmp <= 0:
            break
        reservations = table.get('reservations')

        for index, reservation in enumerate(reservations):
            print(reservations)
            if index > 0:  # Pomijamy pierwszy element listy

                if (start_time.astimezone() <= reservation[1].astimezone() <= end_time.astimezone()) or (
                        start_time.astimezone() <= reservation[2].astimezone() <= end_time.astimezone()):
                    flag = False
                    break
        if flag:
            clients_tmp -= table.get('seats')
            table_id.append(table.get('id'))

    if clients_tmp > 0:
        raise HTTPException(status_code=400,
                            detail="Niestety nie ma wolnych stolików")

    return table_id

@router.get('/{id}/games', description='Get ordered games for reservation')
def get_reservation_games(id: int) -> list[Games]:
    reservation = Reservations.get_one(id)
    return Games.get_many({'id': {'$in': [g['id'] for g in reservation['games']]}})

@router.get('/{id}/tables', description='Get ordered tables for reservation')
def get_reservation_tables(id: int) -> list[Tables]:
    reservation = Reservations.get_one(id)
    return Tables.get_many({'id': {'$in': [tid for tid in reservation['tables']]}})

@router.get('/{id}/food', description='Get ordered food for reservation')
def get_reservation_food(id: int) -> list[OrderedFood]:
    reservation = Reservations.get_one(id)
    return reservation['orderedFood']
