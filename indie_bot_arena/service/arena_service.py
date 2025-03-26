import random
from datetime import datetime
from typing import List, Optional, Tuple, Dict

from bson import ObjectId

from indie_bot_arena.dao.mongo_dao import MongoDAO
from indie_bot_arena.model.domain_model import Model, Battle, LeaderboardEntry


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
      raise ValueError("バトルに必要なモデルが2件以上存在しません")
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
    対戦履歴に基づき、Elo レーティングを再計算してリーダーボードを更新します。
    各モデルは初期レーティング 1000 から開始し、K=32 の Elo 更新式を適用します。
    """
    # 対象言語・階級のモデル一覧を取得
    models = self.dao.find_models(language, weight_class)
    if not models:
      return False

    # 各モデルの初期レーティング (1000) を設定
    ratings = {
      str(model._id): 1000 for model in models if model._id is not None
    }

    # 対戦履歴を取得し、時系列順に並べ替え
    battles = self.dao.find_battles(language, weight_class)
    battles.sort(key=lambda b: b.vote_timestamp)

    K = 32  # Elo の K ファクター
    for battle in battles:
      model_a_id_str = str(battle.model_a_id)
      model_b_id_str = str(battle.model_b_id)

      # 念のため、両モデルが ratings に存在しなければ初期値を設定
      if model_a_id_str not in ratings:
        ratings[model_a_id_str] = 1000
      if model_b_id_str not in ratings:
        ratings[model_b_id_str] = 1000

      # 勝者に応じたスコアを設定
      if str(battle.winner_model_id)==model_a_id_str:
        score_a, score_b = 1, 0
      else:
        score_a, score_b = 0, 1

      # 期待値の計算
      exp_a = 1 / (1 + 10 ** ((ratings[model_b_id_str] - ratings[model_a_id_str]) / 400))
      exp_b = 1 / (1 + 10 ** ((ratings[model_a_id_str] - ratings[model_b_id_str]) / 400))

      # Elo レーティングの更新
      ratings[model_a_id_str] += K * (score_a - exp_a)
      ratings[model_b_id_str] += K * (score_b - exp_b)

    # 各モデルの新たなレーティングでリーダーボードエントリを更新または新規作成
    for model in models:
      if model._id is None:
        continue
      model_id_str = str(model._id)
      new_rating = round(ratings.get(model_id_str, 1000))
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
