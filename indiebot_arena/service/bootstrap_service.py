import logging

from indiebot_arena.dao.mongo_dao import MongoDAO
from indiebot_arena.service.arena_service import ArenaService


class BootstrapService:
  def __init__(self, dao: MongoDAO):
    self.dao = dao
    self.arena_service = ArenaService(dao);

  def provision_database(self):
    if self.dao.models_collection.count_documents({}) > 0:
      logging.info("Database already provisioned. Skipping initial data insertion.")
      return

    try:
      self.arena_service.register_model("ja", "U-5GB", "google/gemma-3-1b-it", "transformers", "none", "safetensors", 1.86)
      self.arena_service.register_model("ja", "U-5GB", "google/gemma-2-2b-it", "transformers", "none", "safetensors", 4.87)
      self.arena_service.register_model("ja", "U-5GB", "google/gemma-2-2b-jpn-it", "transformers", "none", "safetensors", 4.87)
      self.arena_service.register_model("ja", "U-5GB", "indiebot-community/gemma-3-1b-it-bnb-4bit", "transformers", "bnb", "safetensors", 0.93)
      self.arena_service.register_model("ja", "U-5GB", "indiebot-community/gemma-2-2b-it-bnb-4bit", "transformers", "bnb", "safetensors", 2.16)
      self.arena_service.register_model("ja", "U-5GB", "indiebot-community/gemma-2-2b-jpn-it-bnb-4bit", "transformers", "bnb", "safetensors", 2.16)
      self.arena_service.register_model("ja", "U-10GB", "google/gemma-3-4b-it", "transformers", "none", "safetensors", 8.01)
      self.arena_service.register_model("ja", "U-10GB", "indiebot-community/gemma-3-4b-it-bnb-4bit", "transformers", "bnb", "safetensors", 2.93)
      self.arena_service.register_model("ja", "U-10GB", "indiebot-community/gemma-3-12b-it-bnb-4bit", "transformers", "bnb", "safetensors", 7.51)
      self.arena_service.register_model("ja", "U-10GB", "indiebot-community/gemma-2-9b-it-bnb-4bit", "transformers", "bnb", "safetensors", 6.07)

      self.arena_service.update_leaderboard("ja", "U-5GB")
      self.arena_service.update_leaderboard("ja", "U-10GB")
    except Exception as e:
      logging.error(f"Error register_model: {e}")
