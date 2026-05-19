import os
import time


class LogCollector:
    def __init__(self, file_path):
        self.file_path = file_path
        self.last_position = 0
        self.running = False

    def _validate_file(self):
        return os.path.exists(self.file_path)

    def _watch_file(self):
        with open(self.file_path, "r") as f:
            if self.last_position == 0:
                f.seek(0, 2)
                self.last_position = f.tell()
            else:
                f.seek(self.last_position)

            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue

                self.last_position = f.tell()

                yield line

    def start(self):
        if not self._validate_file():
            raise FileNotFoundError

        for new_line in self._watch_file():
            print(new_line.strip())
