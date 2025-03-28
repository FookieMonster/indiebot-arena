import gradio as gr
import pandas as pd

from indie_bot_arena.service.arena_service import ArenaService


def leaderboard_content(dao, language):
  arena_service = ArenaService(dao)

  def fetch_leaderboard_data(weight_class):
    entries = arena_service.get_leaderboard(language, weight_class)
    data = []
    for entry in entries:
      model_obj = arena_service.dao.get_model(entry.model_id)
      model_name = model_obj.model_name if model_obj else "Unknown"
      file_size = model_obj.file_size_gb if model_obj else "N/A"
      desc = model_obj.description if model_obj else ""
      last_updated = entry.last_updated.strftime("%Y-%m-%d %H:%M:%S")
      data.append([model_name, entry.elo_score, file_size, desc, last_updated])
    if not data:
      data = [["No data available", "", "", "", ""]]
    return pd.DataFrame(data, columns=["Model Name", "Elo Score", "File Size (GB)", "Description", "Last Updated"])

  with gr.Blocks() as leaderboard_ui:
    gr.Markdown("## Leaderboard (Language: ja)")
    # ラジオボタンで重量区分を選択
    weight_class_radio = gr.Radio(choices=["U-4GB", "U-8GB"], label="Weight Class", value="U-4GB")
    leaderboard_table = gr.Dataframe(
      headers=["Model Name", "Elo Score", "File Size (GB)", "Description", "Last Updated"],
      value=fetch_leaderboard_data("U-4GB"),
      interactive=False
    )
    weight_class_radio.change(fn=fetch_leaderboard_data, inputs=weight_class_radio, outputs=leaderboard_table)
  return leaderboard_ui
