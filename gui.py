import os
import sys
import threading
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QFrame, QSplitter,
    QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtGui import QFont, QColor, QTextCursor, QIcon

from crypto import encrypt, decrypt
from network import MessageServer, MessageClient


BG = "#1a1a2e"
BG_SECONDARY = "#16213e"
BG_INPUT = "#0f3460"
BG_INPUT_FOCUS = "#1a4a7a"
FG = "#e0e0e0"
FG_DIM = "#888888"
ACCENT = "#0ea5e9"
ACCENT_HOVER = "#38bdf8"
ACCENT_PRESSED = "#0284c7"
RED = "#ef4444"
GREEN = "#22c55e"
YELLOW = "#eab308"
CYAN = "#06b6d4"
BORDER_COLOR = "#1e3a5f"
SHADOW_COLOR = "rgba(0, 0, 0, 40)"

SIDEBAR_WIDTH = 260

STYLE_SHEET = f"""
QMainWindow {{
    background-color: {BG};
}}

QWidget#centralWidget {{
    background-color: {BG};
}}

QFrame#sidebar {{
    background-color: {BG_SECONDARY};
    border-right: 1px solid {BORDER_COLOR};
}}

QFrame#chatArea {{
    background-color: {BG};
}}

QLineEdit {{
    background-color: {BG_INPUT};
    color: {FG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 8px 12px;
    font-family: 'Segoe UI', 'Cantarell', sans-serif;
    font-size: 13px;
    selection-background-color: {ACCENT};
}}

QLineEdit:focus {{
    border: 1px solid {ACCENT};
    background-color: {BG_INPUT_FOCUS};
}}

QLineEdit#messageInput {{
    background-color: {BG_INPUT};
    border: 1px solid {BORDER_COLOR};
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 14px;
    font-family: 'Segoe UI', 'Cantarell', sans-serif;
}}

QLineEdit#messageInput:focus {{
    border: 1px solid {ACCENT};
    background-color: {BG_INPUT_FOCUS};
}}

QPushButton {{
    border: none;
    border-radius: 8px;
    font-family: 'Segoe UI', 'Cantarell', sans-serif;
    font-size: 13px;
    font-weight: bold;
    padding: 10px 16px;
}}

QPushButton#btnServer {{
    background-color: {ACCENT};
    color: #ffffff;
}}
QPushButton#btnServer:hover {{
    background-color: {ACCENT_HOVER};
}}
QPushButton#btnServer:pressed {{
    background-color: {ACCENT_PRESSED};
}}

QPushButton#btnConnect {{
    background-color: {GREEN};
    color: #ffffff;
}}
QPushButton#btnConnect:hover {{
    background-color: #16a34a;
}}
QPushButton#btnConnect:pressed {{
    background-color: #15803d;
}}

QPushButton#btnDisconnect {{
    background-color: #333333;
    color: {FG};
}}
QPushButton#btnDisconnect:hover {{
    background-color: #444444;
}}
QPushButton#btnDisconnect:pressed {{
    background-color: #555555;
}}

QPushButton#btnClear {{
    background-color: transparent;
    color: {FG_DIM};
    border: 1px solid {BORDER_COLOR};
}}
QPushButton#btnClear:hover {{
    background-color: {BG_INPUT};
    color: {FG};
    border-color: {FG_DIM};
}}

QPushButton#btnSend {{
    background-color: {ACCENT};
    color: #ffffff;
    font-size: 14px;
    font-weight: bold;
    padding: 10px 24px;
    border-radius: 10px;
}}
QPushButton#btnSend:hover {{
    background-color: {ACCENT_HOVER};
}}
QPushButton#btnSend:pressed {{
    background-color: {ACCENT_PRESSED};
}}

QTextEdit#chatDisplay {{
    background-color: {BG};
    color: {FG};
    border: none;
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 13px;
    padding: 16px;
    selection-background-color: {ACCENT};
}}

QScrollBar:vertical {{
    background-color: {BG_SECONDARY};
    width: 8px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: #2a3a5a;
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #3a4a6a;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QLabel#titleLabel {{
    color: {FG};
    font-family: 'Segoe UI', 'Cantarell', sans-serif;
    font-size: 24px;
    font-weight: bold;
}}

QLabel#subtitleLabel {{
    color: {FG_DIM};
    font-family: 'Segoe UI', 'Cantarell', sans-serif;
    font-size: 11px;
}}

QLabel#fieldLabel {{
    color: {FG_DIM};
    font-family: 'Segoe UI', 'Cantarell', sans-serif;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

QLabel#statusLabel {{
    color: {RED};
    font-family: 'Segoe UI', 'Cantarell', sans-serif;
    font-size: 12px;
    font-weight: bold;
}}
"""


class Signals(QObject):
    log_signal = Signal(str, str, str)
    status_signal = Signal(str, str)


class EncritApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setStyleSheet(STYLE_SHEET)
        self.app.setFont(QFont("Segoe UI", 10))

        self._server: MessageServer | None = None
        self._client: MessageClient | None = None
        self._password = "encrit_default_key"
        self._nickname = "User"
        self._is_server = False
        self._my_client_id: str = ""

        self._signals = Signals()
        self._signals.log_signal.connect(self._on_log)
        self._signals.status_signal.connect(self._on_status)

        self._build_ui()

    def _build_ui(self):
        self.window = QMainWindow()
        self.window.setWindowTitle("Encrit Messenger")
        self.window.setMinimumSize(780, 520)
        self.window.resize(1000, 650)

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, "Encrit.png")
        if os.path.exists(icon_path):
            self.window.setWindowIcon(QIcon(icon_path))

        central = QWidget()
        central.setObjectName("centralWidget")
        self.window.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(0)
        splitter.setStyleSheet("QSplitter::handle { background-color: transparent; }")

        sidebar = self._build_sidebar()
        chat = self._build_chat()

        splitter.addWidget(sidebar)
        splitter.addWidget(chat)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([SIDEBAR_WIDTH, 740])

        main_layout.addWidget(splitter)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(20, 24, 20, 20)
        layout.setSpacing(0)

        title = QLabel("Encrit")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        subtitle = QLabel("Encrypted Messenger")
        subtitle.setObjectName("subtitleLabel")
        layout.addWidget(subtitle)

        layout.addSpacing(28)

        for label_text, attr_name, default, is_password in [
            ("NICKNAME", "_nick_entry", "User", False),
            ("PASSWORD", "_password_entry", "encrit_default_key", True),
            ("HOST", "_host_entry", "0.0.0.0", False),
            ("PORT", "_port_entry", "9000", False),
        ]:
            lbl = QLabel(label_text)
            lbl.setObjectName("fieldLabel")
            layout.addWidget(lbl)
            layout.addSpacing(4)

            entry = QLineEdit()
            entry.setText(default)
            if is_password:
                entry.setEchoMode(QLineEdit.Password)
            setattr(self, attr_name, entry)
            layout.addWidget(entry)
            layout.addSpacing(12)

        self._status_label = QLabel("Disconnected")
        self._status_label.setObjectName("statusLabel")
        layout.addWidget(self._status_label)

        layout.addStretch()

        shadow_style = f"""
            QPushButton {{
                min-height: 38px;
            }}
        """

        self._server_btn = QPushButton("Start Server")
        self._server_btn.setObjectName("btnServer")
        self._server_btn.setCursor(Qt.PointingHandCursor)
        self._server_btn.clicked.connect(self._start_server)
        layout.addWidget(self._server_btn)
        layout.addSpacing(6)

        self._connect_btn = QPushButton("Connect")
        self._connect_btn.setObjectName("btnConnect")
        self._connect_btn.setCursor(Qt.PointingHandCursor)
        self._connect_btn.clicked.connect(self._connect)
        layout.addWidget(self._connect_btn)
        layout.addSpacing(6)

        self._disconnect_btn = QPushButton("Disconnect")
        self._disconnect_btn.setObjectName("btnDisconnect")
        self._disconnect_btn.setCursor(Qt.PointingHandCursor)
        self._disconnect_btn.clicked.connect(self._disconnect)
        layout.addWidget(self._disconnect_btn)
        layout.addSpacing(6)

        self._clear_btn = QPushButton("Clear Chat")
        self._clear_btn.setObjectName("btnClear")
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.clicked.connect(self._clear_chat)
        layout.addWidget(self._clear_btn)

        return sidebar

    def _build_chat(self) -> QFrame:
        chat_frame = QFrame()
        chat_frame.setObjectName("chatArea")

        layout = QVBoxLayout(chat_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._chat_display = QTextEdit()
        self._chat_display.setObjectName("chatDisplay")
        self._chat_display.setReadOnly(True)
        self._chat_display.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._chat_display.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._chat_display.setFrameShape(QFrame.NoFrame)
        layout.addWidget(self._chat_display, 1)

        input_frame = QFrame()
        input_frame.setStyleSheet("background-color: transparent;")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 8, 16, 16)
        input_layout.setSpacing(10)

        self._message_entry = QLineEdit()
        self._message_entry.setObjectName("messageInput")
        self._message_entry.setPlaceholderText("Type your message...")
        self._message_entry.returnPressed.connect(self._send_message)
        input_layout.addWidget(self._message_entry, 1)

        self._send_btn = QPushButton("Send  \u27a1")
        self._send_btn.setObjectName("btnSend")
        self._send_btn.setCursor(Qt.PointingHandCursor)
        self._send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self._send_btn)

        layout.addWidget(input_frame)

        return chat_frame

    def _log(self, sender: str, text: str, tag: str = "msg"):
        timestamp = datetime.now().strftime("%H:%M:%S")

        tag_colors = {
            "sender": ACCENT,
            "sys": FG_DIM,
            "err": RED,
            "ok": GREEN,
            "msg": FG,
            "time": "#555555",
            "you": YELLOW,
        }

        sender_color = tag_colors.get(tag, FG)
        if tag not in ("sys", "you"):
            sender_color = ACCENT

        time_html = f'<span style="color:#555555;">[{timestamp}] </span>'
        sender_html = f'<span style="color:{sender_color}; font-weight:bold;">{self._escape_html(sender)}: </span>'
        msg_html = f'<span style="color:{tag_colors.get(tag, FG)};">{self._escape_html(text)}</span>'

        self._chat_display.append(time_html + sender_html + msg_html)
        scrollbar = self._chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _escape_html(self, text: str) -> str:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")

    def _on_log(self, sender: str, text: str, tag: str):
        self._log(sender, text, tag)

    def _on_status(self, text: str, color: str):
        self._status_label.setText(text)
        self._status_label.setStyleSheet(f"color: {color}; font-family: 'Segoe UI', sans-serif; font-size: 12px; font-weight: bold;")

    def _schedule(self, func, *args):
        self._signals.log_signal.emit(*args) if func == self._log else None

    def _start_server(self):
        host = self._host_entry.text().strip() or "0.0.0.0"
        try:
            port = int(self._port_entry.text().strip() or "9000")
        except ValueError:
            self._signals.status_signal.emit("Invalid port!", RED)
            return

        self._password = self._password_entry.text() or "encrit_default_key"
        self._nickname = self._nick_entry.text().strip() or "Server"
        self._is_server = True
        self._my_client_id = "SERVER"
        self._server = MessageServer(host, port, self._on_server_message)
        self._server.start()
        self._signals.status_signal.emit(f"Server: {host}:{port}", GREEN)
        self._signals.log_signal.emit("SYSTEM", f"Server started on {host}:{port} as \"{self._nickname}\"", "ok")

    def _on_server_message(self, client_id: str, nickname: str, sender_addr: str, raw: str):
        pwd = self._password
        try:
            decrypted = decrypt(bytes.fromhex(raw), pwd)
            self._signals.log_signal.emit(f"{nickname}", decrypted, "msg")
        except Exception as e:
            self._signals.log_signal.emit("DEBUG", f"raw={raw[:80]}  err={e}", "err")
            self._signals.log_signal.emit(f"{nickname} [{sender_addr}]", "[decryption failed]", "err")

        if self._server:
            try:
                self._server.broadcast(client_id, nickname, raw)
            except Exception:
                pass

    def _connect(self):
        host = self._host_entry.text().strip() or "127.0.0.1"
        try:
            port = int(self._port_entry.text().strip() or "9000")
        except ValueError:
            self._signals.status_signal.emit("Invalid port!", RED)
            return

        self._password = self._password_entry.text() or "encrit_default_key"
        self._nickname = self._nick_entry.text().strip() or "User"
        self._is_server = False
        self._client = MessageClient(self._on_client_message)
        try:
            self._client.connect(host, port)
            self._my_client_id = self._client.client_id
            self._signals.status_signal.emit(f"Connected: {host}:{port}", GREEN)
            self._signals.log_signal.emit("SYSTEM", f"Connected as \"{self._nickname}\" (id: {self._my_client_id})", "ok")
        except Exception as e:
            self._signals.status_signal.emit("Connection failed!", RED)
            self._signals.log_signal.emit("SYSTEM", f"Connection failed: {e}", "err")

    def _on_client_message(self, sender_id: str, nickname: str, raw: str):
        if sender_id == self._my_client_id:
            return
        pwd = self._password
        try:
            decrypted = decrypt(bytes.fromhex(raw), pwd)
            self._signals.log_signal.emit(nickname, decrypted, "msg")
        except Exception as e:
            self._signals.log_signal.emit("DEBUG", f"raw={raw[:80]}  err={e}", "err")
            self._signals.log_signal.emit(f"{nickname}", "[decryption failed]", "err")

    def _send_message(self):
        msg = self._message_entry.text().strip()
        if not msg:
            return
        self._message_entry.clear()

        self._password = self._password_entry.text() or "encrit_default_key"
        self._nickname = self._nick_entry.text().strip() or "User"
        encrypted = encrypt(msg, self._password)
        payload = encrypted.hex()

        self._signals.log_signal.emit("You", msg, "you")

        try:
            if self._is_server and self._server:
                self._server.broadcast("SERVER", self._nickname, payload)
            elif self._client:
                self._client.send(self._nickname, payload)
        except Exception as e:
            self._signals.log_signal.emit("SYSTEM", f"Send failed: {e}", "err")

    def _disconnect(self):
        if self._server:
            self._server.stop()
            self._server = None
        if self._client:
            self._client.disconnect()
            self._client = None
        self._my_client_id = ""
        self._signals.status_signal.emit("Disconnected", RED)
        self._signals.log_signal.emit("SYSTEM", "Disconnected", "sys")

    def _clear_chat(self):
        self._chat_display.clear()

    def run(self):
        self.window.show()
        sys.exit(self.app.exec())


if __name__ == "__main__":
    app = EncritApp()
    app.run()
