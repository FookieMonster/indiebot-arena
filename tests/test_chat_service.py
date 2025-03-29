import unittest

from indiebot_arena.ui.battle import generate


class TestChatService(unittest.TestCase):
  def test_generate_response(self):
    model_id = "google/gemma-3-1b-it"
    message = "クッキーとビスケットの違いを教えて下さい。"
    chat_history = []
    response = generate(message, chat_history, model_id, max_new_tokens=20)

    self.assertIsInstance(response, str)
    self.assertTrue(response.strip())
    print("応答:", response)


if __name__=='__main__':
  unittest.main()
