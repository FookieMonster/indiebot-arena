import gradio as gr

from indie_bot_arena.dao.mongo_dao import MongoDAO
from indie_bot_arena.service.bootstrap_service import BootstrapService
from indie_bot_arena.ui.battle import battle_content
from indie_bot_arena.ui.leaderboard import leaderboard_content
from indie_bot_arena.ui.registration import registration_content

dao = MongoDAO("mongodb://localhost:27017", "indie_bot_arena_db")
bootstrap_service = BootstrapService(dao)
bootstrap_service.provision_database()

with gr.Blocks() as demo:
  with gr.Tabs():
    with gr.TabItem("リーダーボード"):
      leaderboard_content(dao)
    with gr.TabItem("チャットバトル"):
      battle_content(dao)
    with gr.TabItem("モデルの登録"):
      registration_content(dao)

demo.launch()
