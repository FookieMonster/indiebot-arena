from dataclasses import asdict
from typing import List, Optional

from bson import ObjectId
from pymongo import MongoClient

from indiebot_arena.model.domain_model import Model, Battle, LeaderboardEntry


class MongoDAO:
  def __init__(self, uri: str, db_name: str):
    self.client = MongoClient(uri)
    self.db = self.client[db_name]
    self.models_collection = self.db["models"]
    self.battles_collection = self.db["battles"]
    self.leaderboard_collection = self.db["leaderboard"]

    self.models_collection.create_index(
      [("language", 1), ("weight_class", 1), ("model_name", 1)], unique=True
    )
    self.leaderboard_collection.create_index(
      [("language", 1), ("weight_class", 1), ("model_id", 1)], unique=True
    )
    self.battles_collection.create_index(
      [("language", 1), ("weight_class", 1), ("vote_timestamp", 1)]
    )

  # ---------- Model ----------

  def insert_model(self, model: Model) -> ObjectId:
    data = asdict(model)
    if data.get("_id") is None:
      data.pop("_id")
    result = self.models_collection.insert_one(data)
    return result.inserted_id

  def get_model(self, model_id: ObjectId) -> Optional[Model]:
    data = self.models_collection.find_one({"_id": model_id})
    if data:
      return Model(**data)
    return None

  def update_model(self, model: Model) -> bool:
    data = asdict(model)
    if data.get("_id") is None:
      raise ValueError("model _id is required for updating.")
    result = self.models_collection.replace_one({"_id": data["_id"]}, data)
    return result.modified_count > 0

  def delete_model(self, model_id: ObjectId) -> bool:
    result = self.models_collection.delete_one({"_id": model_id})
    return result.deleted_count > 0

  def find_models(self, language: str, weight_class: str) -> List[Model]:
    query = {
      "language": language,
      "weight_class": weight_class
    }
    cursor = self.models_collection.find(query).sort("_id", 1)
    return [Model(**doc) for doc in cursor]

  def find_one_model(self, language: str, weight_class: str, model_name: str) -> Optional[Model]:
    query = {
      "language": language,
      "weight_class": weight_class,
      "model_name": model_name
    }
    data = self.models_collection.find_one(query)
    if data:
      return Model(**data)
    return None

  # ---------- Battle ----------

  def insert_battle(self, battle: Battle) -> ObjectId:
    data = asdict(battle)
    if data.get("_id") is None:
      data.pop("_id")
    result = self.battles_collection.insert_one(data)
    return result.inserted_id

  def get_battle(self, battle_id: ObjectId) -> Optional[Battle]:
    data = self.battles_collection.find_one({"_id": battle_id})
    if data:
      return Battle(**data)
    return None

  def update_battle(self, battle: Battle) -> bool:
    data = asdict(battle)
    if data.get("_id") is None:
      raise ValueError("battle _id is required for updating.")
    result = self.battles_collection.replace_one({"_id": data["_id"]}, data)
    return result.modified_count > 0

  def delete_battle(self, battle_id: ObjectId) -> bool:
    result = self.battles_collection.delete_one({"_id": battle_id})
    return result.deleted_count > 0

  def find_battles(self, language: str, weight_class: str) -> List[Battle]:
    query = {
      "language": language,
      "weight_class": weight_class
    }
    cursor = self.battles_collection.find(query)
    return [Battle(**doc) for doc in cursor]

  def find_last_battle(self) -> Optional[Battle]:
    battle_doc = self.battles_collection.find_one(sort=[("_id", -1)])
    if battle_doc:
      return Battle(**battle_doc)
    return None

  # ---------- LeaderboardEntry ----------

  def insert_leaderboard_entry(self, entry: LeaderboardEntry) -> ObjectId:
    data = asdict(entry)
    if data.get("_id") is None:
      data.pop("_id")
    result = self.leaderboard_collection.insert_one(data)
    return result.inserted_id

  def get_leaderboard_entry(self, entry_id: ObjectId) -> Optional[LeaderboardEntry]:
    data = self.leaderboard_collection.find_one({"_id": entry_id})
    if data:
      return LeaderboardEntry(**data)
    return None

  def update_leaderboard_entry(self, entry: LeaderboardEntry) -> bool:
    data = asdict(entry)
    if data.get("_id") is None:
      raise ValueError("leaderboard _id is required for updating.")
    result = self.leaderboard_collection.replace_one({"_id": data["_id"]}, data)
    return result.modified_count > 0

  def delete_leaderboard_entry(self, entry_id: ObjectId) -> bool:
    result = self.leaderboard_collection.delete_one({"_id": entry_id})
    return result.deleted_count > 0

  def find_leaderboard_entries(self, language: str, weight_class: str) -> List[LeaderboardEntry]:
    query = {
      "language": language,
      "weight_class": weight_class
    }
    cursor = self.leaderboard_collection.find(query).sort("elo_score", -1)
    return [LeaderboardEntry(**doc) for doc in cursor]

  def find_one_leaderboard_entry(self, language: str, weight_class: str, model_id: ObjectId) -> Optional[
    LeaderboardEntry]:
    data = self.leaderboard_collection.find_one({
      "language": language,
      "weight_class": weight_class,
      "model_id": model_id
    })
    if data:
      return LeaderboardEntry(**data)
    return None
