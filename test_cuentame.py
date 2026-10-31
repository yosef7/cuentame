import io
import json
import unittest
from unittest.mock import patch

import cuentame


class FakeResponse:
    def __enter__(self):
        return io.BytesIO(json.dumps({"response": "¿Qué canción recuerdas?"}).encode())

    def __exit__(self, *_args):
        return False


class CuentameTests(unittest.TestCase):
    @patch("cuentame.urlopen", return_value=FakeResponse())
    def test_question_uses_loopback_and_existing_answers(self, send):
        question = cuentame.ask_question("Elena", [("¿Qué comía?", "Arroz")], "gemma4:e2b")
        self.assertEqual(question, "¿Qué canción recuerdas?")
        request = send.call_args.args[0]
        self.assertEqual(request.full_url, cuentame.OLLAMA_URL)
        self.assertIn("Arroz", json.loads(request.data)["prompt"])

    def test_memory_uses_exact_answers(self):
        content = cuentame.render_memory("Elena", [("¿Qué recuerdas?", "Arroz con coco\ny una canción")])
        self.assertIn("> Arroz con coco\n> y una canción", content)
        self.assertNotIn("era una gran cocinera", content)

    def test_rejects_invalid_model_question(self):
        class BadResponse(FakeResponse):
            def __enter__(self):
                return io.BytesIO(json.dumps({"response": "Pregunta uno\nPregunta dos"}).encode())

        with patch("cuentame.urlopen", return_value=BadResponse()):
            with self.assertRaises(RuntimeError):
                cuentame.ask_question("Elena", [], "gemma4:e2b")


if __name__ == "__main__":
    unittest.main()
