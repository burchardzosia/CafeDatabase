from fastapi import APIRouter, Response
import pydantic_partial
from typing import Optional
from cafe_api.model import Model
from cafe_api.parser import parse_tags_from_str
import re
from datetime import datetime
from fastapi import HTTPException

router = APIRouter(
    prefix='/games',
    tags=['games'],
)


class GamesInput(Model):
    name: str
    minPlayers: int
    maxPlayers: int
    unitsInStock: int
    tags: list[str]
    reservations: list[dict]  # (id rezerwacji,start rezerwacji gry, koniec rezerwacji gry)


class Games(GamesInput):
    id: int




class GamesPatch(pydantic_partial.create_partial_model(GamesInput)):
    pass


@router.get('/', description='Get games')
def get_games(name: Optional[str] = None, playersMin: Optional[int] = None, playersMax: Optional[int] = None,
              playersExact: Optional[int] = None,
              tags: Optional[str] = None):
    query = {}
    if name is not None:
        query['name'] = re.compile(name, re.IGNORECASE)
    if playersMax is not None:
        query['maxPlayers'] = {'$lte': playersMax}
    if playersMin is not None:
        query['minPlayers'] = {'$gte': playersMin}
    if playersExact is not None:
        query['minPlayers'] = {'$lte': playersExact}
        query['maxPlayers'] = {'$gte': playersExact}
    if tags is not None:
        query['tags'] = {'$all': parse_tags_from_str(tags)}
    return Games.get_many(query)


@router.get('/{id}', description='Get one game item by id')
def get_game_item(id: int) -> Games:
    return Games.get_one(id)


@router.put('/', status_code=201, description='Add a game')
def put_game_item(_input: GamesInput) -> Games:
    return Games.put_one(_input)

@router.put('/multi', status_code=202, description='Add multiple games')
def put_multiple_game_items(_input: list[GamesInput]) -> list[Games]:
    query = {}
    q_list = []
    for i in _input:
        if i.name is not None:
            q_list.append(i.name)
    query['name'] = {'$in': q_list}
    q_res = Games.get_many(query)
    _input2 = _input
    for q in q_res:
        for i in _input:
            if q['name'] == i.name:
                _input2.remove(i)
    res = []
    for i in _input2:
        res.append(Games.put_one(i))
    return res


@router.patch('/{id}', description='Update a game')
def patch_game_item(id: int, patch: GamesPatch) -> Games:
    return Games.patch_one(id, patch)

@router.patch('/', description='Update multiple games')
def patch_game_items(patch: GamesPatch, name: Optional[str] = None, playersMin: Optional[int] = None, playersMax: Optional[int] = None,
              playersExact: Optional[int] = None,
              tags: Optional[str] = None) -> int:
    query = {}
    if name is not None:
        query['name'] = re.compile(name, re.IGNORECASE)
    if playersMax is not None:
        query['maxPlayers'] = {'$lte': playersMax}
    if playersMin is not None:
        query['minPlayers'] = {'$gte': playersMin}
    if playersExact is not None:
        query['minPlayers'] = {'$lte': playersExact}
        query['maxPlayers'] = {'$gte': playersExact}
    if tags is not None:
        query['tags'] = {'$all': parse_tags_from_str(tags)}
    return Games.patch_multiple(query, patch)


@router.delete('/{id}', status_code=204, description='Delete a game')
def delete_game_item(id: int) -> Response:
    Games.delete_one(id)
    return Response(status_code=204)


@router.post('/{id}/reservations', status_code=201, description='Add a reservation to a game')
def add_reservation_to_game(id: int, reservation_id: int, start_time: datetime, end_time: datetime) -> Games:
    game = Games.get_one(id)
    reservation = {'reservation_id': reservation_id, 'start_time': start_time, 'end_time': end_time}
    game['reservations'].append(reservation)
    patch_data = GamesPatch(reservations=game['reservations'])
    updated_game = Games.patch_one(id, patch_data)
    return updated_game
