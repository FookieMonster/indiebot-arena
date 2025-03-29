from dataclasses import dataclass

import gradio as gr
import spaces
import torch
from huggingface_hub import hf_hub_url, get_hf_file_metadata, model_info
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig

from indiebot_arena.service.arena_service import ArenaService
from indiebot_arena.ui.battle import generate

DESCRIPTION = "# 登録済みモデル"


@dataclass
class ModelMeta:
  model_id: str
  architecture: list
  parameters: str
  model_type: str
  weights_file_size: float
  weights_format: str
  quantization: str


def format_model_meta(meta: ModelMeta) -> str:
  return (
    f"Model ID: {meta.model_id}\n"
    f"Architecture: {meta.architecture}\n"
    f"Parameters: {meta.parameters}\n"
    f"Model Type: {meta.model_type}\n"
    f"Weights File Size: {meta.weights_file_size} GB\n"
    f"Weights Format: {meta.weights_format}\n"
    f"Quantization: {meta.quantization}"
  )


@spaces.GPU(duration=30)
def get_model_meta(model_id: str):
  try:
    config = AutoConfig.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", torch_dtype=torch.bfloat16)
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    repo_info = model_info(model_id)
    weights_files = [file.rfilename for file in repo_info.siblings if
                     file.rfilename.endswith('.bin') or file.rfilename.endswith('.safetensors')]
    total_size = 0
    file_formats = set()
    for file_name in weights_files:
      file_formats.add(file_name.split('.')[-1])
      file_url = hf_hub_url(model_id, filename=file_name)
      metadata = get_hf_file_metadata(file_url)
      total_size += metadata.size or 0
    total_size_gb = round(total_size / (1024 ** 3), 2)
    model_type = type(model).__name__
    quant_config = getattr(config, 'quantization_config', {})
    quant_method = quant_config.get('quant_method', 'none')
    meta = ModelMeta(
      model_id=model_id,
      architecture=config.architectures if hasattr(config, 'architectures') else [],
      parameters=f"{round(sum(p.numel() for p in model.parameters()) / 1e9, 2)} Billion",
      model_type=model_type,
      weights_file_size=total_size_gb,
      weights_format=", ".join(file_formats),
      quantization=quant_method,
    )
    return meta
  except Exception as e:
    return f"Error: {str(e)}"


def registration_content(dao, language):
  arena_service = ArenaService(dao)

  def fetch_models(weight_class):
    models = arena_service.dao.find_models(language, weight_class)
    data = []
    for m in models:
      created_at_str = m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else ""
      data.append([m.weight_class, m.model_name, m.runtime, m.quantization, m.file_format, m.file_size_gb,
                   m.description or "", created_at_str])
    return data

  def load_test(model_id, weight_class, current_output):
    meta = get_model_meta(model_id)
    if isinstance(meta, str) and meta.startswith("Error:"):
      return (current_output + "\n" + meta, gr.update(interactive=False), None)
    if weight_class=="U-5GB" and meta.weights_file_size >= 5.0:
      err = f"Error: File size exceeds U-5GB limit. {meta.weights_file_size} GB"
      return (current_output + "\n" + err, gr.update(interactive=False), None)
    if weight_class=="U-10GB" and meta.weights_file_size >= 10.0:
      err = f"Error: File size exceeds U-10GB limit. {meta.weights_file_size} GB"
      return (current_output + "\n" + err, gr.update(interactive=False), None)
    if "safetensors" not in meta.weights_format.lower():
      err = "Error: Weights Format must include safetensors."
      return (current_output + "\n" + err, gr.update(interactive=False), None)
    if meta.quantization.lower() not in ["bitsandbytes", "none"]:
      err = "Error: Quantization must be bitsandbytes or none."
      return (current_output + "\n" + err, gr.update(interactive=False), None)
    display_str = format_model_meta(meta) + "\nロードテストが完了しました。チャットテストを実施してください。"
    return (current_output + "\n" + display_str, gr.update(interactive=True), meta)

  def chat_test(model_id, current_output):
    question = "日本の首都は？"
    expected_word = "東京"
    response = generate(question, [], model_id)
    result_text = f"チャットテストの質問: {question}\n応答: {response}\n"
    if expected_word in response:
      result_text += "チャットテスト合格: 応答に期待するワードが含まれています。"
      register_enabled = True
    else:
      result_text += "チャットテスト失敗: 応答に期待するワードが含まれていません。"
      register_enabled = False
    return (current_output + "\n" + result_text, gr.update(interactive=register_enabled))

  def register_model(meta, weight_class, description, current_output):
    try:
      if meta is None:
        raise ValueError("No meta info available. ロードテストを実施してください。")
      model_id_extracted = meta.model_id
      file_size_gb = meta.weights_file_size
      quantization = "bnd" if meta.quantization.lower()=="bitsandbytes" else "none"
      weights_format = meta.weights_format
      file_format = "safetensors" if "safetensors" in weights_format.lower() else weights_format
      desc = description if description else ""
      arena_service.register_model(language, weight_class, model_id_extracted, "transformers", quantization, file_format, file_size_gb, desc)
      result = "モデルの登録が完了しました。"
      disable = True
    except Exception as e:
      result = f"エラー: {str(e)}"
      disable = False
    new_output = current_output + "\n" + result
    if disable:
      btn_update = gr.update(interactive=False)
    else:
      btn_update = gr.update()
    return new_output, meta, btn_update, btn_update, btn_update

  def clear_all():
    initial_weight = "U-5GB"
    return "", initial_weight, "", "", gr.update(interactive=True), gr.update(interactive=False), gr.update(interactive=False), None

  with gr.Blocks(css="style.css") as ui:
    gr.Markdown(DESCRIPTION)
    weight_class_radio = gr.Radio(choices=["U-5GB", "U-10GB"], label="Weight Class", value="U-5GB")
    mdl_list = gr.Dataframe(
      headers=["Weight Class", "Model Name", "Runtime", "Quantization", "Weights Format",
               "Weights File Size", "Description", "Created At"],
      value=fetch_models("U-5GB"),
      interactive=False
    )
    weight_class_radio.change(fn=fetch_models, inputs=weight_class_radio, outputs=mdl_list)
    with gr.Accordion("モデルの登録", open=False):
      model_id_input = gr.Textbox(label="モデルID", max_lines=1)
      reg_weight_class_radio = gr.Radio(choices=["U-5GB", "U-10GB"], label="Weight Class", value="U-5GB")
      description_input = gr.Textbox(label="Description (オプション)", placeholder="任意の説明を入力", max_lines=1)
      output_box = gr.Textbox(label="結果出力", lines=10)
      meta_state = gr.State(None)
      with gr.Row():
        test_btn = gr.Button("ロードテスト")
        chat_test_btn = gr.Button("チャットテスト", interactive=False)
        register_btn = gr.Button("モデル登録", interactive=False)
        clear_btn = gr.Button("クリア")
      test_btn.click(fn=load_test, inputs=[model_id_input, reg_weight_class_radio, output_box], outputs=[output_box,
                                                                                                         chat_test_btn,
                                                                                                         meta_state])
      chat_test_btn.click(fn=chat_test, inputs=[model_id_input, output_box], outputs=[output_box, register_btn])
      register_btn.click(fn=register_model, inputs=[meta_state, reg_weight_class_radio, description_input,
                                                    output_box], outputs=[output_box, meta_state, test_btn,
                                                                          chat_test_btn, register_btn])
      clear_btn.click(fn=clear_all, inputs=[], outputs=[model_id_input, reg_weight_class_radio, description_input,
                                                        output_box, test_btn, chat_test_btn, register_btn, meta_state])
  return ui
