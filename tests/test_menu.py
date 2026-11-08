import threading
import time
import unittest
from unittest.mock import patch

import arcade

from sources.views import LoadingView, MenuView


class MenuTest(unittest.TestCase):
    def test_song_selection_loads_off_thread_then_fades_to_game(self):
        window = arcade.Window(1280, 720, visible=False)
        self.addCleanup(window.close)
        prepared = object()
        worker_threads = []

        def prepare(song_id, report):
            worker_threads.append(threading.get_ident())
            report(0.8, "Prepared")
            return prepared

        class FakeGame(arcade.View):
            def __init__(self, song_id, result):
                super().__init__()
                self.song_id = song_id
                self.result = result
                self._fade_alpha = 0
                self._ready = False

            def load_steps(self):
                yield "Step 1"
                yield "Step 2"

        with patch("sources.views.menu.prepare_song", side_effect=prepare), \
             patch("sources.views.menu.MainGameView", FakeGame):
            menu = MenuView("singularity")
            window.show_view(menu)
            menu.on_key_press(arcade.key.DOWN, 0)
            selected = menu.songs[menu.selected][0]
            menu.start()
            loading = window.current_view
            self.assertIsInstance(loading, LoadingView)
            for _ in range(100):
                loading.on_update(0.1)
                if window.current_view is not loading or loading.error:
                    break
                time.sleep(0.001)
            self.assertIsNone(loading.error)
            self.assertIsInstance(window.current_view, FakeGame)
            self.assertEqual(window.current_view.song_id, selected)
            self.assertIs(window.current_view.result, prepared)
            self.assertTrue(window.current_view._ready)
            self.assertEqual(window.current_view._fade_alpha, 255)
            self.assertNotEqual(worker_threads[0], threading.get_ident())
