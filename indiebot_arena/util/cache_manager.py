import os
import shutil


def get_free_space_gb(path):
  total, used, free = shutil.disk_usage(path)
  return total / (1024 ** 3), used / (1024 ** 3), free / (1024 ** 3)  # バイトからGBに変換


def clear_hf_cache():
  """
  HF_HOME 環境変数で指定されたディレクトリ内のキャッシュ（hubフォルダ）を削除する。
  HF_HOMEが設定されていない場合はデフォルトの "~/.cache/huggingface" を使用する。
  """
  hf_home = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
  cache_path = os.path.join(hf_home, "hub")

  if os.path.exists(cache_path):
    shutil.rmtree(cache_path)
    print(f"Hugging Faceのキャッシュ（{cache_path}）をクリアしました。")
  else:
    print(f"キャッシュディレクトリ {cache_path} は存在しません。")
