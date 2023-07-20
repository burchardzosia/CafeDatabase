from fastapi import APIRouter, Response
import pydantic_partial
from typing import Optional
from cafe_api.model import Model
from datetime import datetime

router = APIRouter(
    prefix='/tables',
    tags=['tables'],
)


class TablesInput(Model):
    seats: int
    reservations: list[
        tuple]  # jak w grach, jeszcze nie wiem jaki dokładnie dać format, pewnie coś w stylu (id, czas) lub (id, starttime, endtime, people)


class Tables(TablesInput):
    id: int


class TablesPatch(pydantic_partial.create_partial_model(TablesInput)):
    pass


@router.get('/', description='Get tables')
def get_tables():
    query = {}
    return Tables.get_many(query)


@router.get('/{id}', description='Get one table item by id')
def get_table_item(id: int) -> Tables:
    return Tables.get_one(id)


@router.put('/', status_code=201, description='Add a table')
def put_table_item(_input: TablesInput) -> Tables:
    return Tables.put_one(_input)


@router.patch('/{id}', description='Update a table')
def patch_table_item(id: int, patch: TablesPatch) -> Tables:
    return Tables.patch_one(id, patch)


@router.delete('/{id}', status_code=204, description='Delete a table')
def delete_table_item(id: int) -> Response:
    Tables.delete_one(id)
    return Response(status_code=204)


@router.post('/{id}/reservations', status_code=201, description='Add a reservation to a table')
def add_reservation_to_table(id: int, reservation_id: int, start_time: datetime, end_time: datetime) -> Tables:
    table = Tables.get_one(id)
    reservation = {'reservation_id': reservation_id, 'start_time': start_time, 'end_time': end_time}
    table['reservations'].append(tuple(reservation.values()))
    patch_data = TablesPatch(reservations=table['reservations'])
    updated_table = Tables.patch_one(id, patch_data)
    return updated_table
