import gradio as gr

from indie_bot_arena.ui.battle import battle_content
from indie_bot_arena.ui.leaderboard import leaderboard_content
from indie_bot_arena.ui.registration import registration_content

with gr.Blocks() as demo:
  with gr.Tabs():
    with gr.TabItem("リーダーボード"):
      leaderboard_content()
    with gr.TabItem("チャットバトル"):
      battle_content()
    with gr.TabItem("モデルの登録"):
      registration_content()

demo.launch()
