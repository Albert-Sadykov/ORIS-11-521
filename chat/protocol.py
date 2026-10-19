import struct

# Заголовок содержит длину команды и длину полезной нагрузки. Сама команда
# передаётся сразу после заголовка, поэтому больше не ограничена четырьмя
# символами (например, ERROR передаётся целиком).
HEADER_FORMAT = "!HI"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
MAX_MESSAGE_SIZE = 10 * 1024 * 1024
MAX_COMMAND_SIZE = 64


def recv_exact(sock, size):
    chunks = bytearray()
    while len(chunks) < size:
        chunk = sock.recv(size - len(chunks))
        if not chunk:
            raise ConnectionError("соединение закрыто до получения всех данных")
        chunks.extend(chunk)
    return bytes(chunks)


def send_message(sock, command, payload=b""):
    command_bytes = command.encode("utf-8")
    if not command_bytes:
        raise ValueError("команда не может быть пустой")
    if len(command_bytes) > MAX_COMMAND_SIZE:
        raise ValueError(f"команда слишком длинная: {len(command_bytes)} байт")
    if len(payload) > MAX_MESSAGE_SIZE:
        raise ValueError(f"payload слишком большой: {len(payload)} байт")
    header = struct.pack(HEADER_FORMAT, len(command_bytes), len(payload))
    sock.sendall(header + command_bytes + payload)


def recv_message(sock):
    try:
        header = recv_exact(sock, HEADER_SIZE)
    except ConnectionError:
        return None
    command_length, length = struct.unpack(HEADER_FORMAT, header)
    if not command_length:
        raise ValueError("получена пустая команда")
    if command_length > MAX_COMMAND_SIZE:
        raise ValueError(f"заявленная длина команды {command_length} превышает лимит")
    if length > MAX_MESSAGE_SIZE:
        raise ValueError(f"заявленная длина {length} превышает лимит")
    command_bytes = recv_exact(sock, command_length)
    payload = recv_exact(sock, length) if length else b""
    try:
        command = command_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("команда должна быть закодирована в UTF-8") from error
    return command, payload
