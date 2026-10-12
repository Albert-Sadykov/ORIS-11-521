import socket
import threading

import protocol as proto


HOST = "0.0.0.0"
PORT = 5555

tasks = []
tasks_lock = threading.Lock()


def format_tasks():
    with tasks_lock:
        if not tasks:
            return "Список задач пуст."

        lines = []
        for number, task in enumerate(tasks, start=1):
            status = "x" if task["done"] else " "
            lines.append(f"{number}. [{status}] {task['text']}")
        return "\n".join(lines)


def add_task(text):
    with tasks_lock:
        tasks.append({"text": text, "done": False})
        return len(tasks)


def mark_task_done(task_number):
    with tasks_lock:
        if task_number < 1 or task_number > len(tasks):
            return False
        tasks[task_number - 1]["done"] = True
        return True


def send_text(client_socket, command, text):
    proto.send_message(client_socket, command, text.encode("utf-8"))


def handle_client(client_socket, address):
    print(f"[+] Подключился клиент {address}")

    try:
        send_text(
            client_socket,
            "TEXT",
            "Подключено. Команды: /add <текст>, /list, /done <номер>, /quit",
        )

        while True:
            message = proto.recv_message(client_socket)
            if message is None:
                break

            command, payload = message
            text = payload.decode("utf-8", errors="replace").strip()

            if command == "ADDT":
                if not text:
                    send_text(client_socket, "ERRO", "Укажите текст задачи: /add <текст>.")
                    continue
                task_number = add_task(text)
                send_text(client_socket, "TEXT", f"Задача №{task_number} добавлена.")

            elif command == "LIST":
                send_text(client_socket, "LIST", format_tasks())

            elif command == "DONE":
                try:
                    task_number = int(text)
                except ValueError:
                    send_text(client_socket, "ERRO", "Номер задачи должен быть целым числом.")
                    continue

                if mark_task_done(task_number):
                    send_text(client_socket, "TEXT", f"Задача №{task_number} отмечена выполненной.")
                else:
                    send_text(client_socket, "ERRO", "Задачи с таким номером нет.")

            elif command == "QUIT":
                send_text(client_socket, "TEXT", "До свидания!")
                break

            else:
                send_text(client_socket, "ERRO", f"Неизвестная команда: {command}")

    except (ConnectionError, ConnectionResetError, BrokenPipeError, OSError, ValueError) as error:
        print(f"[!] Ошибка клиента {address}: {error}")
    finally:
        client_socket.close()
        print(f"[-] Клиент {address} отключился")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"[*] Сервер запущен: {HOST}:{PORT}")

        while True:
            client_socket, address = server_socket.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, address),
                daemon=True,
            )
            client_thread.start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Сервер остановлен")
