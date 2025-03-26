from typing import List, Optional, Tuple, Dict

from bson import ObjectId

from indie_bot_arena.dao.mongo_dao import MongoDAO
from indie_bot_arena.model.domain_model import Model, LeaderboardEntry


class ArenaService:
  def __init__(self, dao: MongoDAO):
    self.dao = dao

  # ---------- Model ----------

  def register_model(self, language: str, weight_class: str, model_name: str, description: Optional[str] = None) -> ObjectId:
    raise NotImplementedError("このメソッドは未実装です。")

  def get_two_random_models(self, language: str, weight_class: str) -> Tuple[Model, Model]:
    raise NotImplementedError("このメソッドは未実装です。")

  def get_model_dropdown_list(self, language: str, weight_class: str) -> List[Dict[str, str]]:
    raise NotImplementedError("このメソッドは未実装です。")

  # ---------- Battle ----------

  def record_battle(self, language: str, weight_class: str, model_a_id: ObjectId, model_b_id: ObjectId, winner_model_id: ObjectId, user_id: str) -> ObjectId:
    raise NotImplementedError("このメソッドは未実装です。")

  # ---------- LeaderboardEntry ----------

  def get_leaderboard(self, language: str, weight_class: str) -> List[LeaderboardEntry]:
    raise NotImplementedError("このメソッドは未実装です。")

  def update_leaderboard(self, language: str, weight_class: str) -> bool:
    raise NotImplementedError("このメソッドは未実装です。")
