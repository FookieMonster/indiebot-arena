import gradio as gr

from indie_bot_arena.service.arena_service import ArenaService


def leaderboard_content(dao, language):
  arena_service = ArenaService(dao)

  def fetch_leaderboard_data(language, weight_class):
    entries = arena_service.get_leaderboard(language, weight_class)
    data = []
    for entry in entries:
      model_obj = arena_service.dao.get_model(entry.model_id)
      model_name = model_obj.model_name if model_obj else "Unknown"
      file_size = model_obj.file_size_gb if model_obj else "N/A"
      desc = model_obj.description if model_obj else ""
      last_updated = entry.last_updated.strftime("%Y-%m-%d %H:%M:%S")
      data.append([model_name, entry.elo_score, file_size, desc, last_updated])
    return data

  data_u4gb = fetch_leaderboard_data(language, "U-4GB")
  data_u8gb = fetch_leaderboard_data(language, "U-8GB")

  with gr.Blocks() as leaderboard_ui:
    gr.Markdown("## Leaderboard (Language: ja)")
    with gr.Tabs():
      with gr.TabItem("U-4GB"):
        refresh_u4gb = gr.Button("Refresh")
        leaderboard_table_u4gb = gr.Dataframe(
          headers=["Model Name", "Elo Score", "File Size (GB)", "Description", "Last Updated"],
          value=data_u4gb,
          interactive=False
        )
        refresh_u4gb.click(
          fn=lambda: fetch_leaderboard_data(language, "U-4GB"),
          inputs=[],
          outputs=leaderboard_table_u4gb
        )
      with gr.TabItem("U-8GB"):
        refresh_u8gb = gr.Button("Refresh")
        leaderboard_table_u8gb = gr.Dataframe(
          headers=["Model Name", "Elo Score", "File Size (GB)", "Description", "Last Updated"],
          value=data_u8gb,
          interactive=False
        )
        refresh_u8gb.click(
          fn=lambda: fetch_leaderboard_data(language, "U-8GB"),
          inputs=[],
          outputs=leaderboard_table_u8gb
        )
  return leaderboard_ui
