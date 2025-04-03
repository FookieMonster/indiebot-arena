import hashlib
import os
import random
from collections.abc import Iterator
from threading import Thread

import gradio as gr
import spaces
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

from indiebot_arena.config import MODEL_SELECTION_MODE, MAX_NEW_TOKENS
from indiebot_arena.service.arena_service import ArenaService

DESCRIPTION = "### 💬 チャットバトル"

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
docs_path = os.path.join(base_dir, "docs", "battle_header.md")


@spaces.GPU(duration=30)
def generate(chat_history: list, model_id: str, max_new_tokens: int = MAX_NEW_TOKENS,
             temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2)-> Iterator[str]:
  tokenizer = AutoTokenizer.from_pretrained(model_id)
  model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype=torch.bfloat16,
    use_safetensors=True
  )
  model.eval()

  input_ids = tokenizer.apply_chat_template(chat_history, add_generation_prompt=True, return_tensors="pt")
  input_ids = input_ids.to(model.device)

  streamer = TextIteratorStreamer(tokenizer, timeout=20.0, skip_prompt=True, skip_special_tokens=True)
  generate_kwargs = dict(
    {"input_ids": input_ids},
    streamer=streamer,
    max_new_tokens=max_new_tokens,
    do_sample=True,
    top_p=top_p,
    top_k=top_k,
    temperature=temperature,
    num_beams=1,
    repetition_penalty=repetition_penalty,
  )
  t = Thread(target=model.generate, kwargs=generate_kwargs)
  t.start()

  outputs = []
  for text in streamer:
    outputs.append(text)
    yield "".join(outputs)


def update_user_message(user_message, history_a, history_b, weight_class_radio):
  new_history_a = history_a + [{"role": "user", "content": user_message}]
  new_history_b = history_b + [{"role": "user", "content": user_message}]
  return "", new_history_a, new_history_b, gr.update(interactive=False)


def bot1_response(history, model_id):
  history = history.copy()
  history.append({"role": "assistant", "content": ""})
  conv_history = history[:-1]
  for text in generate(conv_history, model_id):
    history[-1]["content"] = text
    yield history, gr.update(interactive=True), gr.update(interactive=True)


def bot2_response(history, model_id):
  history = history.copy()
  history.append({"role": "assistant", "content": ""})
  conv_history = history[:-1]
  for text in generate(conv_history, model_id):
    history[-1]["content"] = text
    yield history, gr.update(interactive=True), gr.update(interactive=True)


def get_random_values(model_labels):
  if MODEL_SELECTION_MODE=="random":
    return random.sample(model_labels, 2)
  if MODEL_SELECTION_MODE=="manual":
    return model_labels[0], model_labels[0]


def battle_content(dao, language):
  arena_service = ArenaService(dao)
  default_weight = "U-5GB"
  initial_models = arena_service.get_model_dropdown_list(language, default_weight)
  initial_choices = [m["label"] for m in initial_models]
  initial_value_a, initial_value_b = get_random_values(initial_choices)
  dropdown_visible = False if MODEL_SELECTION_MODE=="random" else True

  def fetch_model_dropdown(weight_class):
    models = arena_service.get_model_dropdown_list(language, weight_class)
    model_labels = [m["label"] for m in models]
    value_a, value_b = get_random_values(model_labels)
    update_obj_a = gr.update(choices=model_labels, value=value_a)
    update_obj_b = gr.update(choices=model_labels, value=value_b)
    return update_obj_a, update_obj_b, model_labels

  def submit_vote(vote_choice, weight_class, model_a_name, model_b_name, request: gr.Request):
    user_id = generate_anonymous_user_id(request)
    model_a = arena_service.get_one_model(language, weight_class, model_a_name)
    model_b = arena_service.get_one_model(language, weight_class, model_b_name)
    winner = model_a if vote_choice=="Chatbot A" else model_b
    try:
      arena_service.record_battle(language, weight_class, model_a._id, model_b._id, winner._id, user_id)
      arena_service.update_leaderboard(language, weight_class)
      return "投票が完了しました"
    except Exception as e:
      return f"エラー: {e}"

  def handle_vote(vote_choice, weight_class, model_a_name, model_b_name, request: gr.Request):
    msg = submit_vote(vote_choice, weight_class, model_a_name, model_b_name, request)
    return (
      gr.update(value=msg, visible=True),
      gr.update(interactive=False, value=model_a_name),
      gr.update(interactive=False, value=model_b_name),
      gr.update(visible=False),
      gr.update(visible=True, interactive=True)
    )

  def generate_anonymous_user_id(request: gr.Request):
    user_ip = request.headers.get('x-forwarded-for')
    if user_ip:
      user_id = "indiebot:" + user_ip
      hashed_user_id = hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:16]
      return hashed_user_id
    else:
      return "anonymous"

  def on_vote_a_click(weight, a, b, request: gr.Request):
    return handle_vote("Chatbot A", weight, a, b, request)

  def on_vote_b_click(weight, a, b, request: gr.Request):
    return handle_vote("Chatbot B", weight, a, b, request)

  def reset_battle(dropdown_options):
    value_a, value_b = get_random_values(dropdown_options)
    return (
      [],  # chatbot_aのリセット
      [],  # chatbot_bのリセット
      gr.update(value="", visible=True),  # user_inputのクリア＆表示
      gr.update(interactive=False, value="A is better"),  # vote_a_btnのリセット
      gr.update(interactive=False, value="B is better"),  # vote_b_btnのリセット
      gr.update(visible=False),  # vote_messageの非表示
      gr.update(visible=False, interactive=False),  # next_battle_btnの非表示
      gr.update(choices=dropdown_options, value=value_a),  # model_dropdown_a更新
      gr.update(choices=dropdown_options, value=value_b),  # model_dropdown_b更新
      gr.update(interactive=True)  # weight_class_radio を有効化
    )

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
    dropdown_options_state = gr.State(initial_choices)
    with gr.Row():
      model_dropdown_a = gr.Dropdown(
        choices=initial_choices,
        label="モデルAを選択",
        value=initial_value_a,
        visible=dropdown_visible
      )
      model_dropdown_b = gr.Dropdown(
        choices=initial_choices,
        label="モデルBを選択",
        value=initial_value_b,
        visible=dropdown_visible
      )
    weight_class_radio.change(
      fn=fetch_model_dropdown,
      inputs=weight_class_radio,
      outputs=[model_dropdown_a, model_dropdown_b, dropdown_options_state]
    )
    with gr.Row():
      chatbot_a = gr.Chatbot(label="Chatbot A", type="messages")
      chatbot_b = gr.Chatbot(label="Chatbot B", type="messages")
    with gr.Row():
      vote_a_btn = gr.Button("A is better", variant="primary", interactive=False)
      vote_b_btn = gr.Button("B is better", variant="primary", interactive=False)
    user_input = gr.Textbox(
      placeholder="日本語でメッセージを入力...",
      submit_btn=True,
      show_label=False
    )
    with gr.Row():
      with gr.Column(scale=3):
        vote_message = gr.Textbox(show_label=False, interactive=False, visible=False)
      with gr.Column(scale=1):
        next_battle_btn = gr.Button("次のバトルへ", variant="primary", interactive=False, visible=False, elem_id="next_battle_btn")
    user_event = user_input.submit(
      update_user_message,
      inputs=[user_input, chatbot_a, chatbot_b, weight_class_radio],
      outputs=[user_input, chatbot_a, chatbot_b, weight_class_radio],
      queue=False
    )
    user_event.then(
      bot1_response,
      inputs=[chatbot_a, model_dropdown_a],
      outputs=[chatbot_a, vote_a_btn, vote_b_btn],
      queue=True
    )
    user_event.then(
      bot2_response,
      inputs=[chatbot_b, model_dropdown_b],
      outputs=[chatbot_b, vote_a_btn, vote_b_btn],
      queue=True
    )
    vote_a_btn.click(
      fn=on_vote_a_click,
      inputs=[weight_class_radio, model_dropdown_a, model_dropdown_b],
      outputs=[vote_message, vote_a_btn, vote_b_btn, user_input, next_battle_btn]
    )
    vote_b_btn.click(
      fn=on_vote_b_click,
      inputs=[weight_class_radio, model_dropdown_a, model_dropdown_b],
      outputs=[vote_message, vote_a_btn, vote_b_btn, user_input, next_battle_btn]
    )
    next_battle_btn.click(
      fn=reset_battle,
      inputs=[dropdown_options_state],
      outputs=[
        chatbot_a, chatbot_b, user_input, vote_a_btn,
        vote_b_btn, vote_message, next_battle_btn,
        model_dropdown_a, model_dropdown_b, weight_class_radio
      ]
    )
  return battle_ui
