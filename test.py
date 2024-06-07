import time
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.layout import Layout
from rich.table import Table
from rich.spinner import Spinner
from rich.panel import Panel

def generate_table(rows):
    table = Table(title="Language", box=None)
    table.add_column("Model")
    table.add_column("Run")
    for row in rows:
        table.add_row(*[str(item) for item in row])
    return table

rows = []

with Live(generate_table(rows), refresh_per_second=4) as live:
    for i in range(5):
        row_index = len(rows)
        rows.append(f"Row {row_index}, Col 0")
        for j in range(10):
            # Update the specific row
            rows[row_index] = [i, j] 
            # Refresh the live view with the new table
            live.update(generate_table(rows))
            time.sleep(0.1)

print("some other stuff")