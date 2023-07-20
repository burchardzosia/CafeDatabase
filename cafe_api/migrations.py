from pymongo import MongoClient

client = MongoClient()
db = client['test_database']

# def fix_reservation_ids_in_games_and_tables():
#     for model in ['games', 'tables']:
#         for obj in db[model].find():
#             for i in range(len(obj['reservations'])):
#                 if isinstance(obj['reservations'][i][0], dict):
#                     obj['reservations'][i][0] = obj['reservations'][i][0]['id']
#             db[model].update_one({'id': obj['id']}, {'$set': obj})

def migrate():
    pass
    # fix_reservation_ids_in_games_and_tables()
