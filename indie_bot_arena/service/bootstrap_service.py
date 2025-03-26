import logging
from datetime import datetime

from indie_bot_arena.dao.mongo_dao import MongoDAO
from indie_bot_arena.model.domain_model import Model


class BootstrapService:
  def __init__(self, dao: MongoDAO):
    self.dao = dao

  def provision_database(self):
    if self.dao.models_collection.count_documents({}) > 0:
      logging.info("Database already provisioned. Skipping initial data insertion.")
      return

    initial_models = [
      {
        "language": "ja",
        "weight_class": "U-4GB",
        "model_name": "fukugawa/gemma-2-9b",
        "runtime": "transformers",
        "quantization": "bnb",
        "file_format": "safetensors",
        "file_size_gb": 3.5,
        "description": "Japanese model in U-4GB category.",
        "created_at": datetime.utcnow()
      },
      {
        "language": "en",
        "weight_class": "U-8GB",
        "model_name": "openai/gpt-3",
        "runtime": "transformers",
        "quantization": "none",
        "file_format": "safetensors",
        "file_size_gb": 7.5,
        "description": "English model in U-8GB category.",
        "created_at": datetime.utcnow()
      },
      {
        "language": "ja",
        "weight_class": "U-8GB",
        "model_name": "example/ja-model",
        "runtime": "transformers",
        "quantization": "bnb",
        "file_format": "safetensors",
        "file_size_gb": 7.0,
        "description": "Another Japanese model for U-8GB category.",
        "created_at": datetime.utcnow()
      }
    ]

    for model_data in initial_models:
      try:
        model = Model(
          language=model_data["language"],
          weight_class=model_data["weight_class"],
          model_name=model_data["model_name"],
          runtime=model_data["runtime"],
          quantization=model_data["quantization"],
          file_format=model_data["file_format"],
          file_size_gb=model_data["file_size_gb"],
          description=model_data.get("description"),
          created_at=model_data["created_at"]
        )
        inserted_id = self.dao.insert_model(model)
        logging.info(f"Inserted model '{model_data['model_name']}' with id {inserted_id}.")
      except Exception as e:
        logging.error(f"Error inserting model '{model_data['model_name']}': {e}")
