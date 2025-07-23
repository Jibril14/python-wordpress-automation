class PlagiarismChecker:
    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def check(self, text: str) -> bool:
        """
        Dummy plagiarism checker — always returns True (no plagiarism).
        Replace with actual API calls later.
        """
        return True
    