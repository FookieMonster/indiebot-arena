import logging
from datetime import datetime

from indiebot_arena.dao.mongo_dao import MongoDAO
from indiebot_arena.model.domain_model import Model


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
        "model_name": "openai-community/gpt2",
        "runtime": "transformers",
        "quantization": "none",
        "file_format": "safetensors",
        "file_size_gb": 0.5,
        "description": "GPT-2 small 137M",
        "created_at": datetime.utcnow()
      },
      {
        "language": "ja",
        "weight_class": "U-4GB",
        "model_name": "EleutherAI/gpt-neo-125m",
        "runtime": "transformers",
        "quantization": "none",
        "file_format": "safetensors",
        "file_size_gb": 0.5,
        "description": "GPT-Neo 125M",
        "created_at": datetime.utcnow()
      },
      {
        "language": "ja",
        "weight_class": "U-4GB",
        "model_name": "rinna/japanese-gpt2-small",
        "runtime": "transformers",
        "quantization": "none",
        "file_format": "safetensors",
        "file_size_gb": 0.5,
        "description": "japanese-gpt2-small 123M",
        "created_at": datetime.utcnow()
      },
      {
        "language": "ja",
        "weight_class": "U-4GB",
        "model_name": "rinna/japanese-gpt-neox-small",
        "runtime": "transformers",
        "quantization": "none",
        "file_format": "safetensors",
        "file_size_gb": 0.6,
        "description": "japanese-gpt-neox-small 204M",
        "created_at": datetime.utcnow()
      },
      {
        "language": "ja",
        "weight_class": "U-4GB",
        "model_name": "fukugawa/gemma-2-2b-it-bnb-4bit",
        "runtime": "transformers",
        "quantization": "bnb",
        "file_format": "safetensors",
        "file_size_gb": 2.3,
        "description": "Google公式のgoogle/gemma-2-2b-itをBitsAndBytes(0.44.1)で4bitに量子化",
        "created_at": datetime.utcnow()
      },
      {
        "language": "ja",
        "weight_class": "U-4GB",
        "model_name": "fukugawa/gemma-2-2b-jpn-it-bnb-4bit",
        "runtime": "transformers",
        "quantization": "bnb",
        "file_format": "safetensors",
        "file_size_gb": 2.3,
        "description": "Google公式のgoogle/gemma-2-2b-jpn-itをBitsAndBytes(0.44.1)で4bitに量子化",
        "created_at": datetime.utcnow()
      },
      {
        "language": "ja",
        "weight_class": "U-8GB",
        "model_name": "fukugawa/gemma-2-9b-it-bnb-4bit",
        "runtime": "transformers",
        "quantization": "bnb",
        "file_format": "safetensors",
        "file_size_gb": 6.5,
        "description": "Google公式のgoogle/gemma-2-9b-itをBitsAndBytes(0.44.1)で4bitに量子化",
        "created_at": datetime.utcnow()
      },
      {
        "language": "ja",
        "weight_class": "U-8GB",
        "model_name": "fukugawa/gemma-2-9b-finetuned-bnb-4bit",
        "runtime": "transformers",
        "quantization": "bnb",
        "file_format": "safetensors",
        "file_size_gb": 6.5,
        "description": "fukugawa/gemma-2-9b-finetunedをBitsAndBytes(0.44.1)で4bitに量子化",
        "created_at": datetime.utcnow()
      },
      {
        "language": "ja",
        "weight_class": "U-8GB",
        "model_name": "rinna/japanese-gpt-neox-3.6b-instruction-sft",
        "runtime": "transformers",
        "quantization": "none",
        "file_format": "safetensors",
        "file_size_gb": 7.4,
        "description": "japanese-gpt-neox-3.6b-instruction-sft",
        "created_at": datetime.utcnow()
      },
      {
        "language": "ja",
        "weight_class": "U-8GB",
        "model_name": "rinna/japanese-gpt-neox-3.6b-instruction-sft-v2",
        "runtime": "transformers",
        "quantization": "none",
        "file_format": "safetensors",
        "file_size_gb": 7.4,
        "description": "japanese-gpt-neox-3.6b-instruction-sft-v2",
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
