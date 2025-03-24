import gradio as gr
import spaces


@spaces.GPU(duration=30)
def generate():
  pass


def battle_content():
  gr.Markdown("チャットバトル")
