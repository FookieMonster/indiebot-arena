import random
import re
from datetime import datetime
from typing import List, Optional, Tuple, Dict

from bson import ObjectId

from indie_bot_arena.dao.mongo_dao import MongoDAO
from indie_bot_arena.model.domain_model import Model, Battle, LeaderboardEntry

INITIAL_RATING = 1000
K_FACTOR = 32


class ArenaService:
  def __init__(self, dao: MongoDAO):
    self.dao = dao

  # ---------- Model ----------

  def register_model(
      self,
      language: str,
      weight_class: str,
      model_name: str,
      runtime: str,
      quantization: str,
      file_format: str,
      file_size_gb: float,
      description: Optional[str] = None
  ) -> ObjectId:
    # Non-empty checks
    if not model_name.strip():
      raise ValueError("Model name cannot be empty.")
    if not runtime.strip():
      raise ValueError("Runtime cannot be empty.")
    if not quantization.strip():
      raise ValueError("Quantization cannot be empty.")
    if not file_format.strip():
      raise ValueError("File format cannot be empty.")

    # Validation
    if runtime!="transformers":
      raise ValueError("Runtime must be 'transformers'.")
    if quantization not in ("bnb", "none"):
      raise ValueError("Quantization must be 'bnb' or 'none'.")
    if file_format!="safetensors":
      raise ValueError("File format must be 'safetensors'.")
    if language not in ("ja", "en"):
      raise ValueError("Language must be 'ja' or 'en'.")
    if weight_class not in ("U-4GB", "U-8GB"):
      raise ValueError("Weight class must be 'U-4GB' or 'U-8GB'.")
    if file_size_gb <= 0:
      raise ValueError("File size must be greater than 0.")
    if weight_class=="U-4GB" and file_size_gb >= 4.0:
      raise ValueError("For U-4GB, file size must be less than 4.0.")
    if weight_class=="U-8GB" and file_size_gb >= 8.0:
      raise ValueError("For U-8GB, file size must be less than 8.0.")
    if not re.match(r"^[^/]+/[^/]+$", model_name):
      raise ValueError("Model name must be in 'xxxxx/xxxxxx' format.")

    # Description length check
    if description is not None and len(description) > 1024:
      raise ValueError("Description must be 1024 characters or less.")

    # Duplicate check
    if self.dao.find_one_model(language, weight_class, model_name) is not None:
      raise ValueError("A model with this language, weight class and model name already exists.")

    model = Model(
      model_name=model_name,
      runtime=runtime,
      quantization=quantization,
      file_format=file_format,
      file_size_gb=file_size_gb,
      language=language,
      weight_class=weight_class,
      description=description
    )
    return self.dao.insert_model(model)

  def get_one_model(
      self,
      language: str,
      weight_class: str,
      model_name: str
  ) -> Optional[Model]:
    return self.dao.find_one_model(language, weight_class, model_name)

  def get_two_random_models(
      self,
      language: str,
      weight_class: str
  ) -> Tuple[Model, Model]:
    models = self.dao.find_models(language, weight_class)
    if len(models) < 2:
      raise ValueError("Need at least 2 models for a battle.")
    return tuple(random.sample(models, 2))

  def get_model_dropdown_list(
      self,
      language: str,
      weight_class: str
  ) -> List[Dict[str, str]]:
    models = self.dao.find_models(language, weight_class)
    return [
      {"label": model.model_name, "value": model.model_name}
      for model in models if model.model_name
    ]

  # ---------- Battle ----------

  def record_battle(
      self,
      language: str,
      weight_class: str,
      model_a_id: ObjectId,
      model_b_id: ObjectId,
      winner_model_id: ObjectId,
      user_id: str
  ) -> ObjectId:
    # Validation
    if language not in ("ja", "en"):
      raise ValueError("Language must be 'ja' or 'en'.")
    if weight_class not in ("U-4GB", "U-8GB"):
      raise ValueError("Weight class must be 'U-4GB' or 'U-8GB'.")

    if model_a_id is None or model_b_id is None or winner_model_id is None:
      raise ValueError("All model IDs must be provided.")

    if model_a_id==model_b_id:
      raise ValueError("Model A and Model B must be different.")

    if winner_model_id!=model_a_id and winner_model_id!=model_b_id:
      raise ValueError("Winner model ID must be either model_a_id or model_b_id.")

    # Check model exists
    model_a = self.dao.get_model(model_a_id)
    model_b = self.dao.get_model(model_b_id)
    if model_a is None or model_b is None:
      raise ValueError("Both Model A and Model B must exist in the database.")

    battle = Battle(
      model_a_id=model_a_id,
      model_b_id=model_b_id,
      language=language,
      weight_class=weight_class,
      winner_model_id=winner_model_id,
      user_id=user_id,
    )
    battle_id = self.dao.insert_battle(battle)
    return battle_id

  # ---------- LeaderboardEntry ----------

  def get_leaderboard(
      self,
      language: str,
      weight_class: str
  ) -> List[LeaderboardEntry]:
    return self.dao.find_leaderboard_entries(language, weight_class)

  def update_leaderboard(
      self,
      language: str,
      weight_class: str
  ) -> bool:
    """
    Update the leaderboard using battle history.
    Each model starts at INITIAL_RATING and K is K_FACTOR.
    """
    models = self.dao.find_models(language, weight_class)
    if not models:
      return False

    ratings = {
      str(model._id): INITIAL_RATING for model in models if model._id is not None
    }

    battles = self.dao.find_battles(language, weight_class)
    battles.sort(key=lambda b: b.vote_timestamp)

    for battle in battles:
      model_a_id_str = str(battle.model_a_id)
      model_b_id_str = str(battle.model_b_id)

      if model_a_id_str not in ratings:
        ratings[model_a_id_str] = INITIAL_RATING
      if model_b_id_str not in ratings:
        ratings[model_b_id_str] = INITIAL_RATING

      if str(battle.winner_model_id)==model_a_id_str:
        score_a, score_b = 1, 0
      else:
        score_a, score_b = 0, 1

      exp_a = 1 / (1 + 10 ** ((ratings[model_b_id_str] - ratings[model_a_id_str]) / 400))
      exp_b = 1 / (1 + 10 ** ((ratings[model_a_id_str] - ratings[model_b_id_str]) / 400))

      ratings[model_a_id_str] += K_FACTOR * (score_a - exp_a)
      ratings[model_b_id_str] += K_FACTOR * (score_b - exp_b)

    for model in models:
      if model._id is None:
        continue
      model_id_str = str(model._id)
      new_rating = round(ratings.get(model_id_str, INITIAL_RATING))
      entry = self.dao.find_one_leaderboard_entry(language, weight_class, model._id)
      if entry:
        entry.elo_score = new_rating
        entry.last_updated = datetime.utcnow()
        self.dao.update_leaderboard_entry(entry)
      else:
        new_entry = LeaderboardEntry(
          model_id=model._id,
          language=language,
          weight_class=weight_class,
          elo_score=new_rating,
        )
        self.dao.insert_leaderboard_entry(new_entry)
    return True
