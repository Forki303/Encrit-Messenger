import socket
import struct
import threading
import uuid
from typing import Callable, Optional


def _send_msg(sock: socket.socket, data: bytes):
    header = struct.pack("!I", len(data))
    sock.sendall(header + data)


def _recv_msg(sock: socket.socket) -> Optional[bytes]:
    header = _recv_exact(sock, 4)
    if not header:
        return None
    length = struct.unpack("!I", header)[0]
    if length > 10 * 1024 * 1024:
        return None
    return _recv_exact(sock, length)


def _recv_exact(sock: socket.socket, n: int) -> Optional[bytes]:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


class MessageServer:
    def __init__(self, host: str, port: int, on_message: Callable[[str, str, str, str], None]):
        self.host = host
        self.port = port
        self.on_message = on_message  # (client_id, nickname, sender_addr, raw_hex)
        self._server_socket: Optional[socket.socket] = None
        self._clients: dict[str, socket.socket] = {}
        self._client_nicks: dict[str, str] = {}
        self._running = False

    def start(self):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(5)
        self._running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while self._running:
            try:
                client, addr = self._server_socket.accept()
                client_id = uuid.uuid4().hex[:8]
                self._clients[client_id] = client
                _send_msg(client, f"ID:{client_id}".encode())
                threading.Thread(
                    target=self._handle_client, args=(client, client_id, addr), daemon=True
                ).start()
            except OSError:
                break

    def _handle_client(self, client: socket.socket, client_id: str, addr):
        try:
            while self._running:
                raw = _recv_msg(client)
                if raw is None:
                    break
                decoded = raw.decode()
                sep = decoded.find("|")
                if sep == -1:
                    continue
                nickname = decoded[:sep]
                data = decoded[sep + 1:]
                self._client_nicks[client_id] = nickname
                self.on_message(client_id, nickname, f"{addr[0]}:{addr[1]}", data)
        except Exception:
            pass
        finally:
            self._clients.pop(client_id, None)
            self._client_nicks.pop(client_id, None)
            client.close()

    def broadcast(self, sender_id: str, nickname: str, data: str):
        payload = f"{sender_id}|{nickname}|{data}".encode()
        for cid, client in list(self._clients.items()):
            try:
                _send_msg(client, payload)
            except Exception:
                self._clients.pop(cid, None)
                client.close()

    def stop(self):
        self._running = False
        for client in self._clients.values():
            client.close()
        self._clients.clear()
        self._client_nicks.clear()
        if self._server_socket:
            self._server_socket.close()


class MessageClient:
    def __init__(self, on_message: Callable[[str, str, str], None]):
        self.on_message = on_message  # (sender_id, nickname, raw_hex)
        self._socket: Optional[socket.socket] = None
        self._running = False
        self.client_id: str = ""

    def connect(self, host: str, port: int):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((host, port))
        self._running = True

        id_msg = _recv_msg(self._socket)
        if id_msg:
            id_str = id_msg.decode()
            if id_str.startswith("ID:"):
                self.client_id = id_str[3:]

        threading.Thread(target=self._recv_loop, daemon=True).start()

    def _recv_loop(self):
        try:
            while self._running:
                raw = _recv_msg(self._socket)
                if raw is None:
                    break
                decoded = raw.decode()
                parts = decoded.split("|", 2)
                if len(parts) != 3:
                    continue
                sender_id, nickname, data = parts
                self.on_message(sender_id, nickname, data)
        except Exception:
            pass
        finally:
            self._running = False

    def send(self, nickname: str, data: str):
        if self._socket:
            payload = f"{nickname}|{data}"
            _send_msg(self._socket, payload.encode())

    def disconnect(self):
        self._running = False
        if self._socket:
            self._socket.close()
