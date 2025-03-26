import logging

from indie_bot_arena.dao.mongo_dao import MongoDAO
from indie_bot_arena.service.arena_service import ArenaService


def provision_database():
  dao = MongoDAO()
  try:
    if dao.models_collection.count_documents({}) > 0:
      logging.info("Database already provisioned. Skipping initial data insertion.")
      return

    service = ArenaService(dao)
    initial_models = [
      {
        "language": "ja",
        "weight_class": "U-4GB",
        "model_name": "fukugawa/gemma-2-9b",
        "runtime": "transformers",
        "quantization": "bnb",
        "file_format": "safetensors",
        "file_size_gb": 3.5,
        "description": "Japanese model in U-4GB category."
      },
      {
        "language": "en",
        "weight_class": "U-8GB",
        "model_name": "openai/gpt-3",
        "runtime": "transformers",
        "quantization": "none",
        "file_format": "safetensors",
        "file_size_gb": 7.5,
        "description": "English model in U-8GB category."
      },
      {
        "language": "ja",
        "weight_class": "U-8GB",
        "model_name": "example/ja-model",
        "runtime": "transformers",
        "quantization": "bnb",
        "file_format": "safetensors",
        "file_size_gb": 7.0,
        "description": "Another Japanese model for U-8GB category."
      }
    ]
    for model_data in initial_models:
      try:
        inserted_id = service.register_model(
          language=model_data["language"],
          weight_class=model_data["weight_class"],
          model_name=model_data["model_name"],
          runtime=model_data["runtime"],
          quantization=model_data["quantization"],
          file_format=model_data["file_format"],
          file_size_gb=model_data["file_size_gb"],
          description=model_data.get("description")
        )
        logging.info(f"Inserted model '{model_data['model_name']}' with id {inserted_id}.")
      except Exception as e:
        logging.error(f"Error inserting model '{model_data['model_name']}': {e}")
  finally:
    dao.client.close()


if __name__=="__main__":
  provision_database()
