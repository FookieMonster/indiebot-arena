import gradio as gr


def leaderboard_content():
  with gr.Tabs():
    with gr.TabItem("4GB以下"):
      gr.Markdown("リーダーボード1")
    with gr.TabItem("8GB以下"):
      gr.Markdown("リーダーボード2")
    with gr.TabItem("その他"):
      gr.Markdown("リーダーボード3")
