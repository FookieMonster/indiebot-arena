from dataclasses import dataclass, field
from datetime import datetime
from bson import ObjectId
from typing import Optional


@dataclass
class Model:
  model_name: str
  language: str
  file_size_gb: float
  file_size_category: str
  description: Optional[str] = None
  created_at: datetime = field(default_factory=datetime.utcnow)
  _id: Optional[ObjectId] = None


@dataclass
class Battle:
  model_a_id: ObjectId
  model_b_id: ObjectId
  language: str
  file_size_category: str
  winner_model_id: ObjectId
  user_id: str
  vote_timestamp: datetime = field(default_factory=datetime.utcnow)
  _id: Optional[ObjectId] = None


@dataclass
class LeaderboardEntry:
  model_id: ObjectId
  language: str
  file_size_category: str
  elo_score: int
  last_updated: datetime = field(default_factory=datetime.utcnow)
  _id: Optional[ObjectId] = None
