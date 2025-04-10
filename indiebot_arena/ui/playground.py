import os

import gradio as gr

from indiebot_arena.config import LOCAL_TESTING
from indiebot_arena.service.arena_service import ArenaService
from indiebot_arena.ui.battle import generate, remove_chat_tokens
from indiebot_arena.util.cache_manager import get_free_space_gb, clear_hf_cache

DESCRIPTION = "### 💬 Playground"

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
docs_path = os.path.join(base_dir, "docs", "battle_header.md")


def update_user_message(user_message, history_a):
  if not LOCAL_TESTING:
    total, _, free = get_free_space_gb("/data")
    print(f"空きディスク容量: {free:.2f} GB / {total:.2f} GB")
    if free < (total * 0.2):
      clear_hf_cache()

  new_history_a = history_a + [{"role": "user", "content": user_message}]
  return "", new_history_a


def bot1_response(history, model_id):
  history = history.copy()
  history.append({"role": "assistant", "content": ""})
  conv_history = history[:-1]
  for text in generate(conv_history, model_id):
    cleaned_text = remove_chat_tokens(text)
    history[-1]["content"] = cleaned_text
    yield history


def playground_content(dao, language):
  arena_service = ArenaService(dao)
  default_weight = "U-5GB"
  initial_models = arena_service.get_model_dropdown_list(language, default_weight)
  initial_choices = [m["label"] for m in initial_models]
  initial_value = initial_choices[0]

  def fetch_model_dropdown(weight_class):
    models = arena_service.get_model_dropdown_list(language, weight_class)
    model_labels = [m["label"] for m in models]
    update_obj_a = gr.update(choices=model_labels, value=model_labels[0])
    return update_obj_a

  with gr.Blocks(css="style.css") as battle_ui:
    gr.Markdown(DESCRIPTION)
    with open(docs_path, "r", encoding="utf-8") as f:
      markdown_content = f.read()
    gr.HTML(markdown_content)
    weight_class_radio = gr.Radio(
      choices=["U-5GB", "U-10GB"],
      label="階級",
      value=default_weight
    )
    model_dropdown_a = gr.Dropdown(
      choices=initial_choices,
      label="モデルを選択",
      value=initial_value,
      visible=True
    )
    chatbot_a = gr.Chatbot(label="Chatbot A", type="messages")
    user_input = gr.Textbox(
      placeholder="日本語でメッセージを入力...",
      submit_btn=True,
      show_label=False
    )
    user_event = user_input.submit(
      update_user_message,
      inputs=[user_input, chatbot_a],
      outputs=[user_input, chatbot_a],
      queue=False
    )
    user_event.then(
      bot1_response,
      inputs=[chatbot_a, model_dropdown_a],
      outputs=[chatbot_a],
      queue=True
    )
    weight_class_radio.change(
      fn=fetch_model_dropdown,
      inputs=weight_class_radio,
      outputs=[model_dropdown_a]
    )
    weight_class_radio.change(
      fn=lambda _: [],
      inputs=weight_class_radio,
      outputs=chatbot_a,
      queue=False
    )
    model_dropdown_a.change(
      fn=lambda _: [],
      inputs=model_dropdown_a,
      outputs=chatbot_a,
      queue=False
    )
  return battle_ui
