import gradio as gr
import pandas as pd

from indie_bot_arena.service.arena_service import ArenaService

DESCRIPTION = "# リーダーボード"


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
    df = pd.DataFrame(data, columns=["Model Name", "Elo Score", "File Size (GB)", "Description", "Last Updated"])
    df.insert(0, "Rank", range(1, len(df) + 1))
    return df

  initial_weight_class = "U-4GB"
  with gr.Blocks(css="style.css") as leaderboard_ui:
    gr.Markdown(DESCRIPTION)
    weight_class_radio = gr.Radio(choices=["U-4GB", "U-8GB"], label="Weight Class", value=initial_weight_class)
    leaderboard_table = gr.Dataframe(
      headers=["Rank", "Model Name", "Elo Score", "File Size (GB)", "Description", "Last Updated"],
      value=fetch_leaderboard_data(initial_weight_class),
      interactive=False
    )
    refresh_btn = gr.Button("Refresh")
    weight_class_radio.change(fn=fetch_leaderboard_data, inputs=weight_class_radio, outputs=leaderboard_table)
    refresh_btn.click(fn=fetch_leaderboard_data, inputs=weight_class_radio, outputs=leaderboard_table)
  return leaderboard_ui
