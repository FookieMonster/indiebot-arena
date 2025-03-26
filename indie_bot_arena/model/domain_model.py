from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from bson import ObjectId


@dataclass
class Model:
  language: str               # 言語区分 (例: "ja", "en")
  weight_class: str           # サイズ区分 (例: "U-8GB", "U-4GB")
  model_name: str             # 例: "fukugawa/gemma-2-9b-finetuned-bnb-4bit"
  runtime: str                # 実行環境 (例: "transformers", "llama.cpp")
  quantization: str           # 量子化方式 (例: "none", "bnb", "gptq")
  file_format: str            # 保存形式 (例: "safetensors", "gguf")
  file_size_gb: float         # ファイルサイズ（単位: GB）
  description: Optional[str] = None
  created_at: datetime = field(default_factory=datetime.utcnow)
  _id: Optional[ObjectId] = None


@dataclass
class Battle:
  language: str
  weight_class: str
  model_a_id: ObjectId
  model_b_id: ObjectId
  winner_model_id: ObjectId
  user_id: str
  vote_timestamp: datetime = field(default_factory=datetime.utcnow)
  _id: Optional[ObjectId] = None


@dataclass
class LeaderboardEntry:
  language: str
  weight_class: str
  model_id: ObjectId
  elo_score: int
  last_updated: datetime = field(default_factory=datetime.utcnow)
  _id: Optional[ObjectId] = None
