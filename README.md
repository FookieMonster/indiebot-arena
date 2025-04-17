## 🚀 IndieBot Arena

**IndieBot Arena** は、オープンソースのAIチャットボットの評価とコンペを楽しめるプラットフォームです。GradioとMongoDBを使用して構築されており、Hugging Face Spaces上で動作します。

Chatbot Arenaにインスパイアされて開発しましたが、以下のような違いがあります。

- 誰でもモデルを登録してコンペに参加可能
- 重みのファイルサイズの階級別で戦う
- 階級別にチャットバトルとリーダーボードがある

### 🏟️ デモサイト

https://huggingface.co/spaces/fukugawa/indiebot-arena

### 主な機能
- **🏆️ リーダーボード機能**: モデルを階級（ファイルサイズ）別にランキング表示します。
- **⚔️ バトル機能**: チャットボットモデル同士の対戦を行い、ユーザー投票で勝敗を決定します。
- **📚️ モデル登録機能**: 誰でも簡単に自分のモデルを登録し、コンペに参加できます。
- **💬 Playground機能**: 登録済みのモデルを指定して直接チャットできます。

### 📁 フォルダ構成
```
indiebot-arena/
├── indiebot_arena/
│   ├── __init__.py
│   ├── config.py
│   ├── dao/         # MongoDBデータアクセス
│   ├── service/     # ビジネスロジック
│   ├── model/       # データモデル
│   └── ui/          # Gradio UIコンポーネント
├── app.py            # アプリケーションの起動ファイル
├── style.css         # カスタムスタイル
├── docs/             # ドキュメント
├── tests/            # テストコード
├── LICENSE
├── README.md
└── requirements.txt
```

### 🛠️ アーキテクチャ
- **Gradio** - Web UI
- **MongoDB** - データストレージ
- **Transformers, BitsAndBytes** - 推論ランタイム・量子化
- **Hugging Face Spaces** - ホスティング環境
- **ZeroGPU** - GPU環境

### ⚙️ セットアップ手順（ローカル環境）

#### 前提条件
- Python 3.10
- MongoDB 7.x 以上 (ローカル or Atlasクラウド)

```bash
# GitHubリポジトリをクローン
git clone https://github.com/FookieMonster/indiebot-arena
cd ./indiebot-arena
```

```bash
# 仮想環境を作成
python -m venv .venv
source .venv/bin/activate   # Windows は .venv\Scripts\activate
```

```bash
# 必要なPythonパッケージをインストール
pip install -r requirements.txt
```

```bash
# .env ファイルを作成して、以下の環境変数を記述してください
MONGO_DB_URI=mongodb://localhost:27017
MONGO_DB_NAME=test_db
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxx（READ権限）
LOCAL_TESTING=True
```

```bash
# アプリを起動
python app.py
```
ブラウザで http://localhost:7860 にアクセスして確認できます。

### ⚙️ セットアップ手順（Hugging Face Spaces環境）

#### 前提条件
- Python 3.10
- MongoDB 7.x 以上 (Atlasクラウド)
- Hugging Face SpacesのZeroGPU（月額9ドル）

```bash
# 以下の環境変数をSpacesのsettingsから設定してください
# MONGO_DB_URIとHF_TOKENは秘匿情報なので、必ずSecrets側の環境変数に設定してください。
MONGO_DB_URI=mongodb+srv://xxx:yyy@zzz/?aaa=bbb&ccc=ddd
MONGO_DB_NAME=indiebot_arena_db
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxx（READ権限）
HF_HOME=/data/.huggingface（永続化ディスクを使う場合）
```

#### GradioのSDKバージョンを指定

```
# README.md
title: IndieBot Arena Test
emoji: 💬
colorFrom: yellow
colorTo: yellow
sdk: gradio
sdk_version: 5.12.0
app_file: app.py
pinned: false
```

#### デプロイ

TODO: 現在は手動でファイルをSpacesにデプロイ

### 🤝 コントリビューション
バグ報告、機能リクエスト、プルリクエストを歓迎します！
