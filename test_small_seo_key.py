import requests

# Bearer 21263|XISNLBeQcUyaiAfhktPFMZvxhD03kcLbB0b3Sh4x
API_KEY = "21263|XISNLBeQcUyaiAfhktPFMZvxhD03kcLbB0b3Sh4x"  # your key here
TEXT = "This is just a small test sentence."

url = "https://pro.smallseotools.com/api/checkplag"
payload = {
    "token": API_KEY,
    "data": TEXT
}
headers = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "User-Agent": "python-requests/2.31.0",
    "Accept": "application/json"
}

response = requests.post(url, data=payload, headers=headers)
print(response.status_code, response.text)
