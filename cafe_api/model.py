from fastapi import HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import re
from typing import Literal

client = MongoClient()
db = client['test_database']


class Model(BaseModel):
    class Config:
        extra = 'forbid'

    @classmethod
    def get_collection(cls):
        collection_name = re.sub(r'([A-Z])', r'_\1', cls.__name__).lower()[1:]
        return db[collection_name]

    @classmethod
    def new_id(cls) -> int:
        max_doc = cls.get_collection().find_one({'$query': {}, '$orderby': {'id': -1}})
        max_id = max_doc['id'] if max_doc != None else 0
        return max_id + 1

    @classmethod
    def get_many(cls, query: dict = {}, sort_query: dict[str, Literal['asc', 'desc']] = {}):
        cursor = cls.get_collection().find(query, {'_id': 0})
        for key, direction in sort_query.items():
            cursor = cursor.sort(key, 1 if direction == 'asc' else -1)
        return list(cursor)

    @classmethod
    def get_one(cls, id: int):
        item = cls.get_collection().find_one({'id': id}, {'_id': 0})
        if item is None:
            raise HTTPException(status_code=404)
        return item

    @classmethod
    def put_one(cls, item_input_model: BaseModel):
        item_input = item_input_model.__dict__
        id = cls.new_id()
        item_input['id'] = id
        cls.get_collection().insert_one(item_input)
        return cls.get_one(id)

    @classmethod
    def patch_one(cls, id: int, item_patch_model: BaseModel):
        def without_nones(doc: dict) -> dict:
            return {k: v for k, v in doc.items() if v != None}

        item_patch = without_nones(item_patch_model.__dict__)
        cls.get_collection().update_one({'id': id}, {'$set': item_patch})
        return cls.get_one(id)
    
    @classmethod
    def patch_multiple(cls, query, item_patch_model: BaseModel):
        def without_nones(doc: dict) -> any:
            return {k: v for k, v in doc.items() if v != None}

        item_patch = without_nones(item_patch_model.__dict__)
        res = cls.get_collection().update_many(query, {'$set': item_patch})
        return res.modified_count

    @classmethod
    def delete_one(cls, id: int):
        item = cls.get_collection().find_one_and_delete({'id': id})
        if item is None:
            raise HTTPException(status_code=404)
