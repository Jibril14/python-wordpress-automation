import csv
from typing import List, Dict


def read_csv(file_path: str) -> List[Dict[str, str]]:
    """
    Reads CSV file and returns a list of dictionaries.
    """
    with open(file_path, mode="r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader]
