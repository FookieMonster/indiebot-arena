import os
import shutil
from typing import Tuple


def get_disk_space_gb(path: str) -> Tuple[float, float, float]:
  total, used, free = shutil.disk_usage(path)
  return total / (1024 ** 3), used / (1024 ** 3), free / (1024 ** 3)


def clear_huggingface_hub_cache() -> None:
  hf_home = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
  cache_path = os.path.join(hf_home, "hub")

  if os.path.exists(cache_path):
    shutil.rmtree(cache_path)
    print(f"Hugging Face のキャッシュをクリアしました: {cache_path}")
  else:
    print(f"キャッシュディレクトリが見つかりません: {cache_path}")


def clear_hf_cache_if_low_disk_space(threshold: float = 0.2, storage_path: str = "/data/") -> None:
  hf_home = os.environ.get("HF_HOME", "")
  if hf_home.startswith(storage_path):
    total, _, free = get_disk_space_gb(storage_path)
    print(f"空きディスク容量: {free:.2f} GB / {total:.2f} GB")
    if free < total * threshold:
      clear_huggingface_hub_cache()
