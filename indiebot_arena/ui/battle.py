import concurrent.futures
import os
import threading

import gradio as gr
import spaces
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from indiebot_arena.config import LOCAL_TESTING
from indiebot_arena.service.arena_service import ArenaService

DESCRIPTION = "# チャットバトル"
MAX_NEW_TOKENS = 100
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
  initial_choices = [m["label"] for m in initial_models] if initial_models else []

  def fetch_model_dropdown(weight_class):
    models = arena_service.get_model_dropdown_list(language, weight_class)
    model_labels = [m["label"] for m in models] if models else []
    update_obj = gr.update(choices=model_labels, value=model_labels[0] if model_labels else "")
    return update_obj, update_obj

  def submit_vote(vote_choice, weight_class, model_a_name, model_b_name):
    model_a = arena_service.get_one_model(language, weight_class, model_a_name)
    model_b = arena_service.get_one_model(language, weight_class, model_b_name)
    if model_a is None or model_b is None:
      return "Model not found. Vote not recorded."
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
      gr.update(value=msg, visible=True),  # vote_message を更新して表示
      gr.update(interactive=False, value=model_a_name),  # vote_a_btn のラベルを model_a_name に更新
      gr.update(interactive=False, value=model_b_name),  # vote_b_btn のラベルを model_b_name に更新
      gr.update(visible=False)  # user_input を非表示に
    )

  with gr.Blocks(css="style.css") as battle_ui:
    gr.Markdown(DESCRIPTION)
    weight_class_radio = gr.Radio(choices=["U-5GB", "U-10GB"], label="Select Weight Class", value=default_weight)
    with gr.Row():
      model_dropdown_a = gr.Dropdown(choices=initial_choices, label="Select Model A", value=initial_choices[
        0] if initial_choices else "")
      model_dropdown_b = gr.Dropdown(choices=initial_choices, label="Select Model B", value=initial_choices[
        0] if initial_choices else "")
    weight_class_radio.change(fn=fetch_model_dropdown, inputs=weight_class_radio, outputs=[model_dropdown_a,
                                                                                           model_dropdown_b])
    with gr.Row():
      chatbot_a = gr.Chatbot(label="Chatbot A")
      chatbot_b = gr.Chatbot(label="Chatbot B")
    with gr.Row():
      vote_a_btn = gr.Button("A is better", interactive=False)
      vote_b_btn = gr.Button("B is better", interactive=False)
    user_input = gr.Textbox(label="Your Message", submit_btn=True)
    vote_message = gr.Textbox(label="Vote Status", interactive=False, visible=False)
    user_input.submit(
      fn=submit_message,
      inputs=[user_input, chatbot_a, chatbot_b, model_dropdown_a, model_dropdown_b],
      outputs=[chatbot_a, chatbot_b, user_input, vote_a_btn, vote_b_btn]
    )
    vote_a_btn.click(
      fn=lambda weight, a, b: handle_vote("Chatbot A", weight, a, b),
      inputs=[weight_class_radio, model_dropdown_a, model_dropdown_b],
      outputs=[vote_message, vote_a_btn, vote_b_btn, user_input]
    )
    vote_b_btn.click(
      fn=lambda weight, a, b: handle_vote("Chatbot B", weight, a, b),
      inputs=[weight_class_radio, model_dropdown_a, model_dropdown_b],
      outputs=[vote_message, vote_a_btn, vote_b_btn, user_input]
    )
  return battle_ui
