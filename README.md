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

### 🤝 コントリビューション
バグ報告、機能リクエスト、プルリクエストを歓迎します！
