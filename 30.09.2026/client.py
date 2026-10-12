import socket
import threading

import protocol as proto


HOST = "127.0.0.1"
PORT = 5555


def listen_loop(sock, stop_event):
    while not stop_event.is_set():
        try:
            message = proto.recv_message(sock)
        except (ConnectionError, ConnectionResetError, OSError, ValueError):
            message = None

        if message is None:
            if not stop_event.is_set():
                print("\n[!] Соединение с сервером потеряно")
            stop_event.set()
            break

        command, payload = message
        text = payload.decode("utf-8", errors="replace")
        if command == "ERRO":
            print(f"\n[ошибка] {text}\n> ", end="")
        else:
            print(f"\n{text}\n> ", end="")


def send_command(sock, line):
    if line == "/list":
        proto.send_message(sock, "LIST")
    elif line == "/add" or line.startswith("/add "):
        text = line.removeprefix("/add").strip()
        proto.send_message(sock, "ADDT", text.encode("utf-8"))
    elif line == "/done" or line.startswith("/done "):
        number = line.removeprefix("/done").strip()
        proto.send_message(sock, "DONE", number.encode("utf-8"))
    else:
        print("Неизвестная команда. Используйте /add, /list, /done или /quit.")


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((HOST, PORT))
    except (ConnectionRefusedError, OSError) as error:
        print(f"Не удалось подключиться к серверу: {error}")
        sock.close()
        return

    stop_event = threading.Event()
    listener = threading.Thread(target=listen_loop, args=(sock, stop_event), daemon=True)
    listener.start()

    print("Команды: /add <текст>, /list, /done <номер>, /quit")
    try:
        while not stop_event.is_set():
            line = input("> ").strip()
            if line == "/quit":
                proto.send_message(sock, "QUIT")
                break
            if line:
                send_command(sock, line)
    except (EOFError, KeyboardInterrupt, BrokenPipeError, OSError):
        pass
    finally:
        stop_event.set()
        sock.close()


if __name__ == "__main__":
    main()
