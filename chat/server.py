import socket
import threading
import protocol as proto

HOST = "0.0.0.0"
PORT = 5555

clients = {}
clients_lock = threading.Lock()


def broadcast(command, text, exclude=None):
    payload = text.encode("utf-8")
    with clients_lock:
        targets = [s for s in clients if s is not exclude]
    for sock in targets:
        try:
            proto.send_message(sock, command, payload)
        except (BrokenPipeError, ConnectionResetError, OSError):
            # Отключившийся клиент будет удалён своим обработчиком.
            continue


def decode_username(payload):
    """Проверяет имя из JOIN/NICK и возвращает его либо понятную ошибку."""
    try:
        username = payload.decode("utf-8").strip()
    except UnicodeDecodeError:
        return None, "username must be UTF-8"
    if not username:
        return None, "username must not be empty"
    return username, None


def handle_client(sock, addr):
    username = None
    try:
        first = proto.recv_message(sock)
        if first is None or first[0] != "JOIN":
            proto.send_message(sock, "ERROR", b"first command must be JOIN")
            return

        username, error = decode_username(first[1])
        with clients_lock:
            if error:
                proto.send_message(sock, "ERROR", error.encode())
                return
            if username in clients.values():
                proto.send_message(sock, "ERROR", b"username is already taken")
                return
            clients[sock] = username

        proto.send_message(sock, "TEXT", f"* вы вошли как {username}".encode())
        broadcast("TEXT", f"* {username} присоединился", exclude=sock)
        print(f"[+] {username} присоединился ({addr})")

        while True:
            msg = proto.recv_message(sock)
            if msg is None:
                print(f"[i] {username} отключился без QUIT")
                break

            command, payload = msg
            if command == "TEXT":
                text = payload.decode("utf-8", errors="replace")
                broadcast("TEXT", f"{username}: {text}", exclude=sock)
            elif command == "LIST":
                with clients_lock:
                    names = list(clients.values())
                proto.send_message(sock, "LIST", "\n".join(names).encode())
            elif command == "NICK":
                new_username, error = decode_username(payload)
                if error:
                    proto.send_message(sock, "ERROR", error.encode())
                    continue
                with clients_lock:
                    if new_username in clients.values():
                        error = "username is already taken"
                    else:
                        old_username = username
                        clients[sock] = new_username
                        username = new_username
                if error:
                    proto.send_message(sock, "ERROR", error.encode())
                    continue
                proto.send_message(sock, "TEXT", f"* ваше имя изменено на {username}".encode())
                broadcast("TEXT", f"* {old_username} теперь известен как {username}", exclude=sock)
                print(f"[*] {old_username} сменил имя на {username}")
            elif command == "QUIT":
                proto.send_message(sock, "TEXT", b"* bye")
                print(f"[-] {username} вышел через QUIT")
                break
            else:
                proto.send_message(sock, "ERROR", f"unknown command {command}".encode())

    except ConnectionResetError:
        print(f"[!] {username or addr} - соединение сброшено (RST)")
    except BrokenPipeError:
        print(f"[!] {username or addr} - не удалось отправить, соединение разорвано")
    except ValueError as error:
        # Некорректный заголовок не должен завершать поток сервера с traceback.
        try:
            proto.send_message(sock, "ERROR", str(error).encode("utf-8"))
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        print(f"[!] {username or addr} - ошибка протокола: {error}")
    finally:
        with clients_lock:
            clients.pop(sock, None)
        sock.close()
        if username:
            broadcast("TEXT", f"* {username} покинул чат")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print(f"[*] сервер слушает {HOST}:{PORT}")
        while True:
            client_sock, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] сервер остановлен")
