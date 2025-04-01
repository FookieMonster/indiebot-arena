## 登録可能なモデルの要件

登録可能なモデルは、Hugging Faceのモデルハブで公開されているPyTorchベースのモデルで、transformersライブラリのgenerate APIに対応している必要があります。
重みのファイル形式はsafetensorsのみで、量子化する場合はBitsAndBytesのバージョン0.44.1以降で量子化されている必要があります。
tokenizer_config.jsonで正しくchat_templateが設定されている必要があります。
パラメータ数ではなく、重みのファイルのサイズが5GB未満または10GB未満で階級ごとに分かれてリーダーボードが作れます。

- **GPU環境**: HF SpacesのZeroGPU A100(40GB)
- **LLM実行環境**: transformersライブラリ（4.50.0）
- **量子化**: BitsAndBytesのみ対応（0.44.1）
- **ファイル形式**: safetensorsのみ
- **ファイルサイズ**:　5GB又は10GB未満
- **チャットテンプレート**: chat_template設定が必要（tokenizer_config.json）

非量子化モデルでもファイルサイズ制限をクリアすれば登録可能ですが、サーバーの負荷低減のためにBitsAndBytesによる量子化を推奨します。
将来的には、llama.cppの実行環境でGGUF形式に対応する予定です。

## モデルの登録方法

このページの一番下にある、モデルの新規登録フォームから登録できます。
モデルIDとエントリーしたいファイルサイズ区分を選択してロードテストボタンを押して下さい。

### ① ロードテスト
ロードテストではファイル形式やサイズなどのチェックが行われます。

### ② チャットテスト 
チャットテストでは簡単な日本語応答が出来るかチェックが行われます。

### ③ 登録
ロードテストとチャットテストをクリアしたモデルだけ登録可能です。
登録が完了すると、登録済みモデル一覧にあなたのモデルが表示されます。

## 量子化サンプルコード

以下はBitsAndBytesで4bit量子化して自分のリポジトリにPushするまでのサンプルコードです。

```
# python 3.10
pip install bitsandbytes==0.44.1
pip install accelerate==1.2.1
pip install transformers==4.50.0
pip install huggingface_hub[cli]
```
```
# アクセストークンを入力してログイン
huggingface-cli login
```
```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

model_id = "google/gemma-2-2b-it" 
repo_id = "xxxxx/gemma-2-2b-it-bnb-4bit" 

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, quantization_config=bnb_config, device_map="auto")

tokenizer.push_to_hub(repo_id)
model.push_to_hub(repo_id)

```
量子化後のモデルIDは任意の名前が可能ですが、以下の形式を推奨します。

* BitsAndBytesの4bit量子化の場合
```
[量子化前のモデルID]-bnb-4bit
```