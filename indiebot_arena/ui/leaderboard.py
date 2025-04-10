import os

import gradio as gr
import pandas as pd

from indiebot_arena.service.arena_service import ArenaService

DESCRIPTION = "### 🏆️ リーダーボード"

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
docs_path = os.path.join(base_dir, "docs", "leaderboard_header.md")


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

    def add_emoji(row):
      if row['Rank']==1:
        return "🥇 " + row['Model Name']
      elif row['Rank']==2:
        return "🥈 " + row['Model Name']
      elif row['Rank']==3:
        return "🥉 " + row['Model Name']
      else:
        return row['Model Name']

    df["Model Name"] = df.apply(add_emoji, axis=1)

    def add_link(row):
      decorated_name = row["Model Name"]
      if decorated_name.startswith("🥇 ") or decorated_name.startswith("🥈 ") or decorated_name.startswith("🥉 "):
        emoji_part, pure_model_name = decorated_name.split(" ", 1)
        return f'{emoji_part} <a href="https://huggingface.co/{pure_model_name}" target="_blank">{pure_model_name}</a>'
      else:
        if decorated_name!="Unknown":
          return f'<a href="https://huggingface.co/{decorated_name}" target="_blank">{decorated_name}</a>'
        else:
          return decorated_name

    df["Model Name"] = df.apply(add_link, axis=1)
    return df

  initial_weight_class = "U-5GB"
  with gr.Blocks(css="style.css") as leaderboard_ui:
    with open(docs_path, "r", encoding="utf-8") as f:
      markdown_content = f.read()
    gr.Markdown(markdown_content)
    gr.Markdown(DESCRIPTION)
    weight_class_radio = gr.Radio(choices=["U-5GB", "U-10GB"], label="階級", value=initial_weight_class)
    leaderboard_table = gr.Dataframe(
      headers=["Rank", "Model Name", "Elo Score", "File Size (GB)", "Description", "Last Updated"],
      interactive=False,
      datatype="markdown"
    )
    refresh_btn = gr.Button("更新", variant="primary")
    refresh_btn.click(fn=fetch_leaderboard_data, inputs=weight_class_radio, outputs=leaderboard_table)
    weight_class_radio.change(fn=fetch_leaderboard_data, inputs=weight_class_radio, outputs=leaderboard_table)

  leaderboard_ui.load(fn=fetch_leaderboard_data, inputs=weight_class_radio, outputs=leaderboard_table)
  return leaderboard_ui
