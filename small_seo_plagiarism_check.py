
import csv
import requests
import time

class PlagiarismChecker:
    def __init__(self, api_key: str, skip_status: bool = None):
        self.api_key = api_key
        self.skip_status = skip_status

    def _start_check(self, text: str):
        """Send the initial plagiarism check request."""
        url = "https://pro.smallseotools.com/api/checkplag"
        payload = {
            "token": self.api_key,
            "data": text
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "python-requests/2.31.0",
            "Accept": "application/json"
        }
        resp = requests.post(url, data=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    def _poll_results(self, hash_value: str, key: int):
        """Poll until the plagiarism check is complete."""
        url_template = "https://pro.smallseotools.com/api/query-footprint/{hash}/{key}"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "python-requests/2.31.0",
            "Accept": "application/json"
        }

        while True:
            resp = requests.get(url_template.format(hash=hash_value, key=key), headers=headers)
            resp.raise_for_status()
            data = resp.json()

            if data.get("Recall") is True:
                # If still processing, update key if provided and retry
                if "Key" in data:
                    key = data["Key"]
                time.sleep(2)  # Avoid hammering the API
            else:
                return data

    def check(self, text: str, threshold: int = 5) -> bool:
        """
        Check plagiarism and return True if content passes the threshold.
        """
        if not self.skip_status:
            print("Skipping plagiarism check.")
            return True

        print("Starting plagiarism check with Small SEO Tools...")
        initial = self._start_check(text)

        hash_value = initial.get("Hash")
        key = initial.get("Key")
        recall = initial.get("Recall")

        if recall:
            final_data = self._poll_results(hash_value, key)
        else:
            final_data = initial

        plag_percent = final_data.get("PlagPercent", 0)
        print(f"Plagiarism detected: {plag_percent}%")

        if plag_percent > threshold:
            plag_parts = [
                d.get("Query") for d in final_data.get("Details", [])
                if not d.get("Unique", True)
            ]
            print("Plagiarized segments:", plag_parts)
            return False

        return True


def read_skip_status_from_csv(csv_path: str) -> bool:
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            skip_value = row.get("Skip Plagiarism", "").strip()
            return bool(skip_value)
    return False


if __name__ == "__main__":
    # 1. Read skip status from CSV
    skip_status = read_skip_status_from_csv("data.csv")

    # 2. Initialize checker
    checker = PlagiarismChecker(api_key="21263|XISNLBeQcUyaiAfhktPFMZvxhD03kcLbB0b3Sh4x", skip_status=skip_status)

    # 3. Example LLM content
    content = {
        "sections": [
            "This is my first section of generated content...",
            "Another test paragraph..."
        ]
    }

    # 4. Check each section
    for section in content["sections"]:
        if checker.check(section):
            print("[SUCCESS] Content passed plagiarism check")
        else:
            print("[WARNING] Plagiarism detected. Post not published.")
