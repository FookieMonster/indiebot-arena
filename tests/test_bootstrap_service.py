import logging
import unittest

from indie_bot_arena.dao.mongo_dao import MongoDAO
from indie_bot_arena.service.bootstrap_service import provision_database


class TestBootstrapService(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.dao = MongoDAO()

  def setUp(self):
    self.dao.models_collection.delete_many({})
    self.dao.battles_collection.delete_many({})
    self.dao.leaderboard_collection.delete_many({})

  def test_provision_inserts_initial_models(self):
    provision_database()
    count = self.dao.models_collection.count_documents({})
    self.assertEqual(count, 3)

  def test_provision_is_idempotent(self):
    provision_database()
    count_first = self.dao.models_collection.count_documents({})
    provision_database()
    count_second = self.dao.models_collection.count_documents({})
    self.assertEqual(count_first, count_second)

  @classmethod
  def tearDownClass(cls):
    cls.dao.models_collection.delete_many({})
    cls.dao.battles_collection.delete_many({})
    cls.dao.leaderboard_collection.delete_many({})


if __name__=="__main__":
  logging.basicConfig(level=logging.INFO)
  unittest.main()
