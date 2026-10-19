import queue
import socket
import threading
import protocol as proto

HOST = "127.0.0.1"
PORT = 5555
USERNAME_TIMEOUT = 15


def read_username_with_timeout():
    """Ждёт input ограниченное время, не опрашивая stdin в цикле."""
    result = queue.Queue(maxsize=1)

    def read_input():
        try:
            result.put((input("Введите имя: "), None))
        except EOFError as error:
            result.put((None, error))

    # Поток daemon не удерживает программу после истечения таймаута input().
    threading.Thread(target=read_input, daemon=True).start()
    try:
        username, error = result.get(timeout=USERNAME_TIMEOUT)
    except queue.Empty:
        print("Время на ввод имени истекло. Клиент завершает работу.")
        return None
    if error:
        print("Не удалось прочитать имя. Клиент завершает работу.")
        return None
    return username.strip()


def listen_loop(sock, stop_event):
    while not stop_event.is_set():
        try:
            msg = proto.recv_message(sock)
        except (ConnectionResetError, OSError, ValueError):
            msg = None
        if msg is None:
            print("\n[!] соединение с сервером потеряно")
            stop_event.set()
            break
        command, payload = msg
        text = payload.decode("utf-8", errors="replace")
        if command == "LIST":
            print(f"\n[пользователи онлайн]\n{text}\n> ", end="")
        elif command == "ERROR":
            print(f"\n[ошибка] {text}\n> ", end="")
        else:
            print(f"\n{text}\n> ", end="")


def main():
    username = read_username_with_timeout()
    if username is None:
        return
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
        proto.send_message(sock, "JOIN", username.encode())
    except (ConnectionRefusedError, OSError) as e:
        print(f"Не удалось подключиться: {e}")
        return

    stop_event = threading.Event()
    threading.Thread(target=listen_loop, args=(sock, stop_event), daemon=True).start()

    print("Команды: /list, /nick <новое_имя>, /quit. Остальной текст - сообщение в чат.")
    try:
        while not stop_event.is_set():
            line = input("> ")
            if line == "/quit":
                proto.send_message(sock, "QUIT")
                break
            elif line == "/list":
                proto.send_message(sock, "LIST")
            elif line == "/nick" or line.startswith("/nick "):
                # Пустое имя тоже отправляем: сервер вернёт понятный ERROR.
                new_username = line[5:].strip()
                proto.send_message(sock, "NICK", new_username.encode("utf-8"))
            elif line:
                proto.send_message(sock, "TEXT", line.encode())
    except (EOFError, KeyboardInterrupt, BrokenPipeError, OSError):
        pass
    finally:
        stop_event.set()
        sock.close()


if __name__ == "__main__":
    main()
