import gradio as gr

from indiebot_arena.config import MONGO_DB_URI, MONGO_DB_NAME, LANGUAGE
from indiebot_arena.dao.mongo_dao import MongoDAO
from indiebot_arena.service.bootstrap_service import BootstrapService
from indiebot_arena.ui.battle import battle_content
from indiebot_arena.ui.leaderboard import leaderboard_content
from indiebot_arena.ui.playground import playground_content
from indiebot_arena.ui.registration import registration_content

dao = MongoDAO(MONGO_DB_URI, MONGO_DB_NAME)
bootstrap_service = BootstrapService(dao)
bootstrap_service.provision_database()

with gr.Blocks(theme=gr.themes.Citrus(primary_hue="sky"), css_paths="style.css") as demo:
  with gr.Tabs():
    with gr.TabItem("🏆 リーダーボード"):
      leaderboard_content(dao, LANGUAGE)
    with gr.TabItem("⚔️ チャット対戦"):
      battle_content(dao, LANGUAGE)
    with gr.TabItem("📚️ モデルの登録"):
      registration_content(dao, LANGUAGE)
    with gr.TabItem("💬 Playground"):
      playground_content(dao, LANGUAGE)

if __name__=="__main__":
  demo.queue(max_size=20).launch()
