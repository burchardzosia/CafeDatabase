from fastapi import FastAPI
from cafe_api.routers import menu, games, tables, reservations, tags
from cafe_api.migrations import migrate

app = FastAPI()

app.include_router(menu.router)
app.include_router(games.router)
app.include_router(tables.router)
app.include_router(reservations.router)
app.include_router(tags.router)

@app.on_event('startup')
def startup_event():
    migrate()

@app.get('/', description='Greetings')
def get_greetings():
    return "Hello, welcome to the Gaming Cafe!"
