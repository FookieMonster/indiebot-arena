import gradio as gr
import spaces
import torch
from huggingface_hub import hf_hub_url, get_hf_file_metadata, model_info
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig

DESCRIPTION = "# 登録済みモデル"


@spaces.GPU(duration=30)
def get_model_info(model_id):
  try:
    config = AutoConfig.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
      model_id,
      device_map="auto",
      torch_dtype=torch.bfloat16
    )
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    repo_info = model_info(model_id)
    weights_files = [
      file.rfilename for file in repo_info.siblings
      if file.rfilename.endswith('.bin') or file.rfilename.endswith('.safetensors')
    ]
    total_size = 0
    file_formats = set()
    for file_name in weights_files:
      file_formats.add(file_name.split('.')[-1])
      file_url = hf_hub_url(model_id, filename=file_name)
      metadata = get_hf_file_metadata(file_url)
      total_size += metadata.size or 0
    total_size_gb = total_size / (1024 ** 3)
    model_type = type(model).__name__
    quant_config = getattr(config, 'quantization_config', {})
    quant_method = quant_config.get('quant_method', 'None')
    info = {
      "Model ID": model_id,
      "Architecture": config.architectures,
      "Parameters": f"{round(sum(p.numel() for p in model.parameters()) / 1e9, 2)} Billion",
      "Model Type": model_type,
      "Weights File Size": f"{round(total_size_gb, 2)} GB",
      "Weights Format": ", ".join(file_formats),
      "Quantization": quant_method,
    }
    return "\n".join(f"{key}: {value}" for key, value in info.items())
  except Exception as e:
    return f"Error: {str(e)}"


def registration_content(dao, language):
  from indie_bot_arena.service.arena_service import ArenaService
  arena_service = ArenaService(dao)

  def fetch_models(weight_class):
    models = arena_service.dao.find_models(language, weight_class)
    data = []
    for m in models:
      created_at_str = m.created_at.strftime("%Y-%m-%d %H:%M:%S") if m.created_at else ""
      data.append([m.language, m.weight_class, m.model_name, m.runtime, m.quantization, m.file_format, m.file_size_gb,
                   m.description or "", created_at_str])
    return data

  def test_model(model_id):
    return get_model_info(model_id)

  def register_model(meta_info, weight_class, description):
    try:
      lines = meta_info.splitlines()
      meta_dict = {}
      for line in lines:
        parts = line.split(":", 1)
        if len(parts)==2:
          meta_dict[parts[0].strip()] = parts[1].strip()
      model_id = meta_dict.get("Model ID")
      weights_file_size_str = meta_dict.get("Weights File Size", "0 GB")
      try:
        file_size_gb = float(weights_file_size_str.replace("GB", "").strip())
      except:
        file_size_gb = 0.0
      quantization = "bnd" if meta_dict.get("Quantization", "none")=="bitsandbytes" else "none"
      weights_format = meta_dict.get("Weights Format", "")
      file_format = "safetensors" if "safetensors" in weights_format else weights_format
      architecture = meta_dict.get("Architecture", "")
      model_type = meta_dict.get("Model Type", "")
      parameters = meta_dict.get("Parameters", "")
      desc = description if description else f"Architecture: {architecture}, Model Type: {model_type}, Parameters: {parameters}"
      arena_service.register_model(language, weight_class, model_id, "transformers", quantization, file_format, file_size_gb, desc)
      return "登録完了"
    except Exception as e:
      return f"エラー: {str(e)}"

  with gr.Blocks(css="style.css") as ui:
    gr.Markdown(DESCRIPTION)
    weight_class_radio = gr.Radio(choices=["U-4GB", "U-8GB"], label="Weight Class", value="U-4GB")
    mdl_list = gr.Dataframe(
      headers=["Language", "Weight Class", "Model Name", "Runtime", "Quantization", "File Format", "File Size (GB)",
               "Description", "Created At"],
      value=fetch_models("U-4GB"),
      interactive=False
    )
    weight_class_radio.change(fn=fetch_models, inputs=weight_class_radio, outputs=mdl_list)
    with gr.Accordion("モデル登録", open=False):
      model_id_input = gr.Textbox(label="モデルID", max_lines=1)
      description_input = gr.Textbox(label="Description (オプション)", placeholder="任意の説明を入力", max_lines=1)
      test_btn = gr.Button("テスト")
      meta_info_box = gr.Textbox(label="Meta情報", lines=10)
      register_btn = gr.Button("登録")
      result_txt = gr.Textbox(label="結果")
      test_btn.click(fn=test_model, inputs=model_id_input, outputs=meta_info_box)
      register_btn.click(fn=register_model, inputs=[meta_info_box, weight_class_radio,
                                                    description_input], outputs=result_txt)
  return ui
