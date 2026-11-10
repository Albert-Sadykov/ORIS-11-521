import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_URL = "http://127.0.0.1:5000"


def send_request(method, path, data=None):
    body = None if data is None else json.dumps(data).encode()
    headers = {} if body is None else {"Content-Type": "application/json"}
    request = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)

    try:
        with urlopen(request) as response:
            status = response.status
            response_body = response.read().decode()
    except HTTPError as error:
        status = error.code
        response_body = error.read().decode()

    try:
        result = json.loads(response_body)
    except json.JSONDecodeError:
        result = response_body
    print(f"{method} {path} -> {status}: {result}")
    return status, result


def main():
    send_request("GET", "/")
    send_request("POST", "/notes", {"text": "Без автора"})
    _, first_note = send_request("POST", "/notes", {"author": "Ivan", "text": "Первая заметка"})
    _, second_note = send_request("POST", "/notes", {"author": "Anna", "text": "Вторая заметка"})

    first_id = first_note["id"]
    second_id = second_note["id"]
    send_request("GET", "/notes?sort=id&order=asc")
    send_request("GET", "/notes?author=Ivan&limit=1&offset=0")
    send_request("GET", "/notes?sort=created")
    send_request("GET", "/notes/999999")
    send_request("GET", f"/notes/{first_id}")
    send_request("PUT", f"/notes/{first_id}", {"author": "Ivan"})
    send_request("PUT", f"/notes/{first_id}", {"author": "Petr", "text": "Заменённая заметка"})
    send_request("PATCH", f"/notes/{first_id}", {"author": "Ivan"})
    send_request("PATCH", f"/notes/{first_id}", {"text": "Частично обновлена"})
    send_request("POST", "/notes/999999/like")
    send_request("POST", f"/notes/{first_id}/like")
    send_request("POST", f"/notes/{first_id}/like")
    send_request("GET", "/notes?sort=likes&order=desc")
    send_request("GET", "/authors")
    send_request("DELETE", "/notes")
    send_request("DELETE", "/notes?author=Nobody")
    send_request("DELETE", f"/notes/{second_id}")
    send_request("DELETE", "/notes?author=Petr")
    send_request("GET", f"/notes/{first_id}")


if __name__ == "__main__":
    main()
