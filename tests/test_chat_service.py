import unittest

from indiebot_arena.ui.battle import generate


class TestChatService(unittest.TestCase):
  def test_generate_response(self):
    model_id = "google/gemma-3-1b-it"
    user_message = "クッキーとビスケットの違いを教えて下さい。"
    chat_history = [{"role": "user", "content": user_message}]
    for text in generate(chat_history, model_id, max_new_tokens=20):
      final_text = text
    print("応答:", final_text)


if __name__=='__main__':
  unittest.main()
