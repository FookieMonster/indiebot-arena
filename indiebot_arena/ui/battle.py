import concurrent.futures
import os
import random
import threading

import gradio as gr
import spaces
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from indiebot_arena.config import LOCAL_TESTING, MODEL_SELECTION_MODE, MAX_NEW_TOKENS
from indiebot_arena.service.arena_service import ArenaService

DESCRIPTION = "# チャットバトル"
MAX_INPUT_TOKEN_LENGTH = int(os.getenv("MAX_INPUT_TOKEN_LENGTH", "4096"))

_model_cache = {}
_model_lock = threading.Lock()


def get_cached_model_and_tokenizer(model_id: str):
  with _model_lock:
    if model_id not in _model_cache:
      tokenizer = AutoTokenizer.from_pretrained(model_id)
      model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", torch_dtype=torch.bfloat16)
      model.eval()
      _model_cache[model_id] = (model, tokenizer)
    return _model_cache[model_id]


@spaces.GPU(duration=30)
def generate(message: str, chat_history: list, model_id: str, max_new_tokens: int = MAX_NEW_TOKENS,
             temperature: float = 0.6, top_p: float = 0.9, top_k: int = 50, repetition_penalty: float = 1.2) -> str:
  if LOCAL_TESTING:
    # Avoid cannot copy out of meta tensor
    model, tokenizer = get_cached_model_and_tokenizer(model_id)
  else:
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", torch_dtype=torch.bfloat16)

  conversation = chat_history.copy()
  conversation.append({"role": "user", "content": message})
  input_ids = tokenizer.apply_chat_template(conversation, add_generation_prompt=True, return_tensors="pt")
  if input_ids.shape[1] > MAX_INPUT_TOKEN_LENGTH:
    input_ids = input_ids[:, -MAX_INPUT_TOKEN_LENGTH:]
    gr.Warning(f"Trimmed input as it exceeded {MAX_INPUT_TOKEN_LENGTH} tokens.")
  input_ids = input_ids.to(model.device)
  outputs = model.generate(
    input_ids=input_ids,
    max_new_tokens=max_new_tokens,
    do_sample=True,
    top_p=top_p,
    top_k=top_k,
    temperature=temperature,
    repetition_penalty=repetition_penalty,
  )
  response = tokenizer.decode(outputs[0][input_ids.shape[1]:], skip_special_tokens=True)
  return response


def format_chat_history(history):
  conversation = []
  for user_msg, assistant_msg in history:
    conversation.append({"role": "user", "content": user_msg})
    if assistant_msg:
      conversation.append({"role": "assistant", "content": assistant_msg})
  return conversation


def submit_message(message, history_a, history_b, model_a, model_b):
  history_a.append((message, ""))
  history_b.append((message, ""))
  conv_history_a = format_chat_history(history_a[:-1])
  conv_history_b = format_chat_history(history_b[:-1])
  with concurrent.futures.ThreadPoolExecutor() as executor:
    future_a = executor.submit(generate, message, conv_history_a, model_a)
    future_b = executor.submit(generate, message, conv_history_b, model_b)
    response_a = future_a.result()
    response_b = future_b.result()
  history_a[-1] = (message, response_a)
  history_b[-1] = (message, response_b)
  return history_a, history_b, "", gr.update(interactive=True), gr.update(interactive=True)


def battle_content(dao, language):
  arena_service = ArenaService(dao)
  default_weight = "U-5GB"
  initial_models = arena_service.get_model_dropdown_list(language, default_weight)
  initial_choices = [m["label"] for m in initial_models]
  initial_value_a, initial_value_b = random.sample(initial_choices, 2)
  dropdown_visible = False if MODEL_SELECTION_MODE == "random" else True

  def fetch_model_dropdown(weight_class):
    models = arena_service.get_model_dropdown_list(language, weight_class)
    model_labels = [m["label"] for m in models]
    value_a, value_b = random.sample(model_labels, 2)
    update_obj_a = gr.update(choices=model_labels, value=value_a)
    update_obj_b = gr.update(choices=model_labels, value=value_b)
    return update_obj_a, update_obj_b, model_labels

  def submit_vote(vote_choice, weight_class, model_a_name, model_b_name):
    model_a = arena_service.get_one_model(language, weight_class, model_a_name)
    model_b = arena_service.get_one_model(language, weight_class, model_b_name)
    winner = model_a if vote_choice=="Chatbot A" else model_b
    try:
      arena_service.record_battle(language, weight_class, model_a._id, model_b._id, winner._id, "anonymous")
      arena_service.update_leaderboard(language, weight_class)
      return "Vote recorded."
    except Exception as e:
      return f"Error recording vote: {e}"

  def handle_vote(vote_choice, weight_class, model_a_name, model_b_name):
    msg = submit_vote(vote_choice, weight_class, model_a_name, model_b_name)
    return (
      gr.update(value=msg, visible=True),
      gr.update(interactive=False, value=model_a_name),
      gr.update(interactive=False, value=model_b_name),
      gr.update(visible=False),
      gr.update(visible=True, interactive=True)
    )

  def reset_battle(dropdown_options):
    value_a, value_b = random.sample(dropdown_options, 2)
    return (
      [],  # chatbot_aのリセット
      [],  # chatbot_bのリセット
      gr.update(value="", visible=True),  # user_inputのクリア＆表示
      gr.update(interactive=False, value="A is better"),  # vote_a_btnのリセット
      gr.update(interactive=False, value="B is better"),  # vote_b_btnのリセット
      gr.update(visible=False),  # vote_messageの非表示
      gr.update(visible=False, interactive=False),  # next_battle_btnの非表示
      gr.update(choices=dropdown_options, value=value_a),  # model_dropdown_a更新
      gr.update(choices=dropdown_options, value=value_b)  # model_dropdown_b更新
    )

  with gr.Blocks(css="style.css") as battle_ui:
    gr.Markdown(DESCRIPTION)
    weight_class_radio = gr.Radio(
      choices=["U-5GB", "U-10GB"],
      label="Select Weight Class",
      value=default_weight
    )
    dropdown_options_state = gr.State(initial_choices)
    with gr.Row():
      model_dropdown_a = gr.Dropdown(
        choices=initial_choices,
        label="Select Model A",
        value=initial_value_a,
        visible=dropdown_visible
      )
      model_dropdown_b = gr.Dropdown(
        choices=initial_choices,
        label="Select Model B",
        value=initial_value_b,
        visible=dropdown_visible
      )
    weight_class_radio.change(
      fn=fetch_model_dropdown,
      inputs=weight_class_radio,
      outputs=[model_dropdown_a, model_dropdown_b, dropdown_options_state]
    )
    with gr.Row():
      chatbot_a = gr.Chatbot(label="Chatbot A")
      chatbot_b = gr.Chatbot(label="Chatbot B")
    with gr.Row():
      vote_a_btn = gr.Button("A is better", interactive=False)
      vote_b_btn = gr.Button("B is better", interactive=False)
    user_input = gr.Textbox(
      placeholder="日本語でメッセージを入力...",
      value="日本の首都は？",
      submit_btn=True,
      show_label=False
    )
    with gr.Row():
      with gr.Column(scale=3):
        vote_message = gr.Textbox(show_label=False, interactive=False, visible=False)
      with gr.Column(scale=1):
        next_battle_btn = gr.Button("Next Battle", interactive=False, visible=False, elem_id="next_battle_btn")
    user_input.submit(
      fn=submit_message,
      inputs=[user_input, chatbot_a, chatbot_b, model_dropdown_a, model_dropdown_b],
      outputs=[chatbot_a, chatbot_b, user_input, vote_a_btn, vote_b_btn]
    )
    vote_a_btn.click(
      fn=lambda weight, a, b: handle_vote("Chatbot A", weight, a, b),
      inputs=[weight_class_radio, model_dropdown_a, model_dropdown_b],
      outputs=[vote_message, vote_a_btn, vote_b_btn, user_input, next_battle_btn]
    )
    vote_b_btn.click(
      fn=lambda weight, a, b: handle_vote("Chatbot B", weight, a, b),
      inputs=[weight_class_radio, model_dropdown_a, model_dropdown_b],
      outputs=[vote_message, vote_a_btn, vote_b_btn, user_input, next_battle_btn]
    )
    next_battle_btn.click(
      fn=reset_battle,
      inputs=[dropdown_options_state],
      outputs=[
        chatbot_a, chatbot_b, user_input, vote_a_btn,
        vote_b_btn, vote_message, next_battle_btn,
        model_dropdown_a, model_dropdown_b
      ]
    )
  return battle_ui
