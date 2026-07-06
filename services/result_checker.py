import csv
import os


async def check_finished_matches():
    signals_path = "logs/signals.csv"

    if not os.path.exists(signals_path):
        print("SIGNALS LOG MISSING:", signals_path)
        return

    with open(signals_path, newline="", encoding="utf-8") as signals_file:
        reader = csv.reader(signals_file)

        for row in reader:
            if len(row) < 2:
                continue

            print(row[1])
