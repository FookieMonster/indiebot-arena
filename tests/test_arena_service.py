import logging
import unittest

from bson import ObjectId

from indiebot_arena.dao.mongo_dao import MongoDAO
from indiebot_arena.model.domain_model import Model
from indiebot_arena.service.arena_service import ArenaService


class TestArenaService(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.dao = MongoDAO(uri="mongodb://localhost:27017", db_name="test_db_arena")
    cls.arena_service = ArenaService(cls.dao)

  def setUp(self):
    self.dao.models_collection.delete_many({})
    self.dao.battles_collection.delete_many({})
    self.dao.leaderboard_collection.delete_many({})

  def test_register_and_get_model(self):
    language = "ja"
    weight_class = "U-5GB"
    model_name = "testuser/test-model"
    runtime = "transformers"
    quantization = "bnb"
    file_format = "safetensors"
    file_size_gb = 3.0
    description = "A test model"

    inserted_id = self.arena_service.register_model(
      language=language,
      weight_class=weight_class,
      model_name=model_name,
      runtime=runtime,
      quantization=quantization,
      file_format=file_format,
      file_size_gb=file_size_gb,
      description=description
    )
    self.assertIsNotNone(inserted_id)

    model = self.arena_service.get_one_model(language, weight_class, model_name)
    self.assertIsNotNone(model)
    self.assertEqual(model.model_name, model_name)

  def test_get_two_random_models(self):
    language = "ja"
    weight_class = "U-5GB"
    model_names = ["testuser/model1", "testuser/model2", "testuser/model3"]

    for name in model_names:
      self.arena_service.register_model(
        language=language,
        weight_class=weight_class,
        model_name=name,
        runtime="transformers",
        quantization="bnb",
        file_format="safetensors",
        file_size_gb=3.0,
        description="Test model"
      )

    model_a, model_b = self.arena_service.get_two_random_models(language, weight_class)

    self.assertIsInstance(model_a, Model)
    self.assertIsInstance(model_b, Model)

    self.assertIsInstance(model_a._id, ObjectId)
    self.assertIsInstance(model_b._id, ObjectId)

    self.assertNotEqual(model_a._id, model_b._id)

  def test_get_model_dropdown_list(self):
    language = "en"
    weight_class = "U-10GB"
    model_names = ["user/modelA", "user/modelB"]

    for name in model_names:
      self.arena_service.register_model(
        language=language,
        weight_class=weight_class,
        model_name=name,
        runtime="transformers",
        quantization="none",
        file_format="safetensors",
        file_size_gb=7.0,
        description="Test model"
      )

    dropdown_list = self.arena_service.get_model_dropdown_list(language, weight_class)
    self.assertEqual(len(dropdown_list), len(model_names))
    for entry in dropdown_list:
      self.assertIn(entry["value"], model_names)
      self.assertEqual(entry["label"], entry["value"])

  def test_record_battle_and_leaderboard_update(self):
    """
    2つのモデルでバトルを記録し、リーダーボードの更新が正しく行われるかテストする
    """
    language = "ja"
    weight_class = "U-5GB"

    # 2つのモデルを登録
    model1_id = self.arena_service.register_model(
      language=language,
      weight_class=weight_class,
      model_name="testuser/battle-model1",
      runtime="transformers",
      quantization="bnb",
      file_format="safetensors",
      file_size_gb=3.0,
      description="Battle model 1"
    )
    model2_id = self.arena_service.register_model(
      language=language,
      weight_class=weight_class,
      model_name="testuser/battle-model2",
      runtime="transformers",
      quantization="bnb",
      file_format="safetensors",
      file_size_gb=3.0,
      description="Battle model 2"
    )

    # バトル記録（model1が勝利）
    battle_id = self.arena_service.record_battle(
      language=language,
      weight_class=weight_class,
      model_a_id=model1_id,
      model_b_id=model2_id,
      winner_model_id=model1_id,
      user_id="test_user"
    )
    self.assertIsNotNone(battle_id)

    # リーダーボードを更新
    update_result = self.arena_service.update_leaderboard(language, weight_class)
    self.assertTrue(update_result)

    leaderboard = self.arena_service.get_leaderboard(language, weight_class)
    self.assertEqual(len(leaderboard), 2)

    # model1のスコアがmodel2より高いことを確認（初期は1000、model1の勝利により変動するはず）
    model1_entry = next((entry for entry in leaderboard if entry.model_id==model1_id), None)
    model2_entry = next((entry for entry in leaderboard if entry.model_id==model2_id), None)
    self.assertIsNotNone(model1_entry)
    self.assertIsNotNone(model2_entry)
    self.assertGreater(model1_entry.elo_score, model2_entry.elo_score)

  @classmethod
  def tearDownClass(cls):
    cls.dao.models_collection.delete_many({})
    cls.dao.battles_collection.delete_many({})
    cls.dao.leaderboard_collection.delete_many({})
    cls.dao.client.close()


if __name__=="__main__":
  logging.basicConfig(level=logging.INFO)
  unittest.main()
