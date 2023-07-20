from fastapi import APIRouter, Response
from cafe_api.routers.menu import Menu
from cafe_api.routers.games import Games

router = APIRouter(
    prefix='/tags',
    tags=['tags'],
)

@router.get('/menu', description='Get all menu tags')
def get_menu_tags():
    return Menu.get_collection().distinct('tags')

@router.get('/games', description='Get all games tags')
def get_games_tags():
    return Games.get_collection().distinct('tags')