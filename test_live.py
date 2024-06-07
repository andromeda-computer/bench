import time
import threading
from rich.console import Console
from rich.live import Live
from rich.table import Table

class LiveTableManager:
    def __init__(self, columns, title, refresh_rate=4):
        self.columns = ["Name"] + columns
        self.title = title
        self.rows = {}
        self.console = Console()
        self.lock = threading.Lock()
        self.update_flag = threading.Event()
        self.update_flag.set()
        self.refresh_rate = refresh_rate
        self.live = Live(self._generate_table(), refresh_per_second=refresh_rate)
        
        # Start live updates in a background thread
        self.update_thread = threading.Thread(target=self._run_updates)
        self.update_thread.start()
        with self.live:  # Start live context
            # self.update_thread.join()
            pass

    def _generate_table(self):
        table = Table(title=self.title, box=None)
        for column in self.columns:
            table.add_column(column)
        for row in self.rows.values():
            table.add_row(*[str(row.get(col, "")) for col in self.columns])
        return table

    def _refresh_table(self):
        with self.lock:
            self.live.update(self._generate_table())

    def add_row(self, row_name, data):
        with self.lock:
            self.rows[row_name] = {"Name": row_name, **data}

    def update_row(self, row_name, data):
        with self.lock:
            if row_name in self.rows:
                self.rows[row_name].update(data)

    def _run_updates(self):
        while self.update_flag.is_set():
            self._refresh_table()
            time.sleep(1 / self.refresh_rate)

    def stop(self):
        self.update_flag.clear()
        if self.update_thread.is_alive():
            self.update_thread.join()

# Example usage:
columns = ["Data1", "Data2"]
lm = LiveTableManager(columns, "Example Table")

lm.add_row("Row 1", {"Data1": "Value 1a", "Data2": "Value 1b"})
time.sleep(1)

lm.add_row("Row 2", {"Data1": "Value 2a", "Data2": "Value 2b"})
time.sleep(1)

lm.update_row("Row 1", {"Data1": "Updated 1a"})
time.sleep(1)

lm.update_row("Row 2", {"Data2": "Updated 2b"})
time.sleep(2)

lm.stop()

print("some other stuff")