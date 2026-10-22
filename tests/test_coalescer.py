import unittest
import time
import threading
from core.coalescer import MessageCoalescer


class TestCoalescer(unittest.TestCase):
    def test_debounce_coalescing(self):
        coalescer = MessageCoalescer()
        executed_payloads = []
        done_event = threading.Event()

        def mock_executor(session_id, payloads):
            executed_payloads.append(payloads)
            done_event.set()

        # Encolar 3 mensajes seguidos en menos de 100ms
        coalescer.schedule_turn("session_test", "msg1", mock_executor, debounce_ms=200.0)
        coalescer.schedule_turn("session_test", "msg2", mock_executor, debounce_ms=200.0)
        coalescer.schedule_turn("session_test", "msg3", mock_executor, debounce_ms=200.0)

        # Esperar a que el timer y thread de dispatch se completen determinísticamente
        success = done_event.wait(timeout=3.0)
        self.assertTrue(success, "El coalescer no ejecutó el turno en el tiempo límite")

        # Debe haber ejecutado 1 sola llamada con los 3 mensajes juntos
        self.assertEqual(len(executed_payloads), 1)
        self.assertEqual(executed_payloads[0], ["msg1", "msg2", "msg3"])


if __name__ == "__main__":
    unittest.main()
