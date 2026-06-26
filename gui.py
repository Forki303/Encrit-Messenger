import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import traceback
from datetime import datetime
from crypto import encrypt, decrypt
from network import MessageServer, MessageClient


BG = "#1a1a2e"
BG_SECONDARY = "#16213e"
BG_INPUT = "#0f3460"
FG = "#e0e0e0"
FG_DIM = "#888888"
ACCENT = "#0ea5e9"
ACCENT_HOVER = "#38bdf8"
RED = "#ef4444"
GREEN = "#22c55e"
YELLOW = "#eab308"
CYAN = "#06b6d4"
FONT_MONO = ("Consolas", 12)
FONT_LABEL = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_SUBTITLE = ("Segoe UI", 9)


class EncritApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Encrit Messenger")
        self.root.geometry("950x620")
        self.root.minsize(700, 480)
        self.root.configure(bg=BG)

        self._server: MessageServer | None = None
        self._client: MessageClient | None = None
        self._password = "encrit_default_key"
        self._nickname = "User"
        self._is_server = False
        self._my_client_id: str = ""

        self._build_ui()

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Dark.TFrame", background=BG)
        style.configure("Secondary.TFrame", background=BG_SECONDARY)
        style.configure("Dark.TLabel", background=BG, foreground=FG, font=FONT_LABEL)
        style.configure("Dim.TLabel", background=BG, foreground=FG_DIM, font=FONT_SUBTITLE)
        style.configure("Title.TLabel", background=BG, foreground=FG, font=FONT_TITLE)
        style.configure("Green.TLabel", background=BG, foreground=GREEN, font=FONT_LABEL)
        style.configure("Red.TLabel", background=BG, foreground=RED, font=FONT_LABEL)

        style.configure("Accent.TButton", background=ACCENT, foreground="#fff",
                         font=("Segoe UI", 10, "bold"), borderwidth=0, padding=(12, 6))
        style.map("Accent.TButton", background=[("active", ACCENT_HOVER)])

        style.configure("Dark.TButton", background="#333", foreground=FG,
                         font=FONT_LABEL, borderwidth=0, padding=(12, 6))
        style.map("Dark.TButton", background=[("active", "#444")])

        style.configure("Dark.TEntry", fieldbackground=BG_INPUT, foreground=FG,
                         insertcolor=FG, borderwidth=1, relief="flat")

        sidebar = tk.Frame(self.root, bg=BG_SECONDARY, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="Encrit", bg=BG_SECONDARY, fg=FG,
                 font=("Segoe UI", 20, "bold")).pack(pady=(25, 2))
        tk.Label(sidebar, text="Encrypted Messenger", bg=BG_SECONDARY, fg=FG_DIM,
                 font=FONT_SUBTITLE).pack(pady=(0, 20))

        tk.Label(sidebar, text="Nickname:", bg=BG_SECONDARY, fg=FG_DIM,
                 font=FONT_LABEL, anchor="w").pack(padx=15, pady=(5, 2), fill="x")
        self._nick_entry = tk.Entry(sidebar, bg=BG_INPUT, fg=FG,
                                     insertbackground=FG, font=FONT_MONO,
                                     relief="flat", bd=0)
        self._nick_entry.pack(padx=15, pady=(0, 8), fill="x", ipady=5)
        self._nick_entry.insert(0, self._nickname)

        tk.Label(sidebar, text="Password:", bg=BG_SECONDARY, fg=FG_DIM,
                 font=FONT_LABEL, anchor="w").pack(padx=15, pady=(5, 2), fill="x")
        self._password_entry = tk.Entry(sidebar, bg=BG_INPUT, fg=FG,
                                         insertbackground=FG, font=FONT_MONO,
                                         show="*", relief="flat", bd=0)
        self._password_entry.pack(padx=15, pady=(0, 8), fill="x", ipady=5)
        self._password_entry.insert(0, self._password)

        tk.Label(sidebar, text="Host:", bg=BG_SECONDARY, fg=FG_DIM,
                 font=FONT_LABEL, anchor="w").pack(padx=15, pady=(5, 2), fill="x")
        self._host_entry = tk.Entry(sidebar, bg=BG_INPUT, fg=FG,
                                     insertbackground=FG, font=FONT_MONO,
                                     relief="flat", bd=0)
        self._host_entry.pack(padx=15, pady=(0, 8), fill="x", ipady=5)
        self._host_entry.insert(0, "0.0.0.0")

        tk.Label(sidebar, text="Port:", bg=BG_SECONDARY, fg=FG_DIM,
                 font=FONT_LABEL, anchor="w").pack(padx=15, pady=(5, 2), fill="x")
        self._port_entry = tk.Entry(sidebar, bg=BG_INPUT, fg=FG,
                                     insertbackground=FG, font=FONT_MONO,
                                     relief="flat", bd=0)
        self._port_entry.pack(padx=15, pady=(0, 8), fill="x", ipady=5)
        self._port_entry.insert(0, "9000")

        self._status_label = tk.Label(sidebar, text="Disconnected", bg=BG_SECONDARY,
                                       fg=RED, font=FONT_LABEL)
        self._status_label.pack(padx=15, pady=(15, 5))

        btn_frame = tk.Frame(sidebar, bg=BG_SECONDARY)
        btn_frame.pack(padx=15, pady=(5, 0), fill="x")

        self._server_btn = tk.Button(btn_frame, text="Start Server", bg=ACCENT, fg="#fff",
                                      activebackground=ACCENT_HOVER, activeforeground="#fff",
                                      font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                                      cursor="hand2", command=self._start_server)
        self._server_btn.pack(fill="x", ipady=5, pady=(0, 5))

        self._connect_btn = tk.Button(btn_frame, text="Connect", bg="#22c55e", fg="#fff",
                                       activebackground="#16a34a", activeforeground="#fff",
                                       font=("Segoe UI", 10, "bold"), relief="flat", bd=0,
                                       cursor="hand2", command=self._connect)
        self._connect_btn.pack(fill="x", ipady=5, pady=(0, 5))

        self._disconnect_btn = tk.Button(btn_frame, text="Disconnect", bg="#555", fg="#fff",
                                          activebackground="#666", activeforeground="#fff",
                                          font=FONT_LABEL, relief="flat", bd=0,
                                          cursor="hand2", command=self._disconnect)
        self._disconnect_btn.pack(fill="x", ipady=5, pady=(0, 5))

        self._clear_btn = tk.Button(btn_frame, text="Clear Chat", bg="#444", fg="#aaa",
                                     activebackground="#555", activeforeground="#fff",
                                     font=FONT_LABEL, relief="flat", bd=0,
                                     cursor="hand2", command=self._clear_chat)
        self._clear_btn.pack(fill="x", ipady=5, pady=(10, 0))

        chat_frame = tk.Frame(self.root, bg=BG)
        chat_frame.pack(side="right", fill="both", expand=True)

        self._chat_display = tk.Text(chat_frame, bg=BG, fg=FG, insertbackground=FG,
                                      font=FONT_MONO, wrap="word", relief="flat", bd=0,
                                      padx=12, pady=12, state="disabled",
                                      selectbackground=ACCENT, selectforeground="#fff")
        self._chat_display.pack(fill="both", expand=True, padx=(1, 0), pady=(5, 0))

        scrollbar = tk.Scrollbar(self._chat_display, command=self._chat_display.yview)
        scrollbar.pack(side="right", fill="y")
        self._chat_display.configure(yscrollcommand=scrollbar.set)

        self._chat_display.tag_configure("sender", foreground=ACCENT)
        self._chat_display.tag_configure("sys", foreground=FG_DIM)
        self._chat_display.tag_configure("err", foreground=RED)
        self._chat_display.tag_configure("ok", foreground=GREEN)
        self._chat_display.tag_configure("msg", foreground=FG)
        self._chat_display.tag_configure("time", foreground="#555")
        self._chat_display.tag_configure("you", foreground=YELLOW)

        input_frame = tk.Frame(chat_frame, bg=BG)
        input_frame.pack(fill="x", padx=5, pady=(2, 10))

        self._message_entry = tk.Entry(input_frame, bg=BG_INPUT, fg=FG,
                                        insertbackground=FG, font=("Segoe UI", 13),
                                        relief="flat", bd=0)
        self._message_entry.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))
        self._message_entry.bind("<Return>", lambda e: self._send_message())

        self._send_btn = tk.Button(input_frame, text="Send  >>", bg=ACCENT, fg="#fff",
                                    activebackground=ACCENT_HOVER, activeforeground="#fff",
                                    font=("Segoe UI", 11, "bold"), relief="flat", bd=0,
                                    cursor="hand2", command=self._send_message)
        self._send_btn.pack(side="right", ipady=4, padx=(0, 5))

    def _log(self, sender: str, text: str, tag: str = "msg"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._chat_display.configure(state="normal")
        self._chat_display.insert("end", f"[{timestamp}] ", "time")
        self._chat_display.insert("end", f"{sender}: ", "sender" if tag not in ("sys", "you") else tag)
        self._chat_display.insert("end", f"{text}\n", tag)
        self._chat_display.configure(state="disabled")
        self._chat_display.see("end")

    def _schedule(self, func, *args):
        self.root.after(0, func, *args)

    def _start_server(self):
        host = self._host_entry.get().strip() or "0.0.0.0"
        try:
            port = int(self._port_entry.get().strip() or "9000")
        except ValueError:
            self._status_label.configure(text="Invalid port!", fg=RED)
            return

        self._password = self._password_entry.get() or "encrit_default_key"
        self._nickname = self._nick_entry.get().strip() or "Server"
        self._is_server = True
        self._my_client_id = "SERVER"
        self._server = MessageServer(host, port, self._on_server_message)
        self._server.start()
        self._status_label.configure(text=f"Server: {host}:{port}", fg=GREEN)
        self._log("SYSTEM", f"Server started on {host}:{port} as \"{self._nickname}\"", "ok")

    def _on_server_message(self, client_id: str, nickname: str, sender_addr: str, raw: str):
        pwd = self._password
        try:
            decrypted = decrypt(bytes.fromhex(raw), pwd)
            self._schedule(self._log, f"{nickname}", decrypted)
        except Exception as e:
            self._schedule(self._log, "DEBUG", f"raw={raw[:80]}  err={e}", "err")
            self._schedule(self._log, f"{nickname} [{sender_addr}]", "[decryption failed]", "err")

        if self._server:
            try:
                self._server.broadcast(client_id, nickname, raw)
            except Exception:
                pass

    def _connect(self):
        host = self._host_entry.get().strip() or "127.0.0.1"
        try:
            port = int(self._port_entry.get().strip() or "9000")
        except ValueError:
            self._status_label.configure(text="Invalid port!", fg=RED)
            return

        self._password = self._password_entry.get() or "encrit_default_key"
        self._nickname = self._nick_entry.get().strip() or "User"
        self._is_server = False
        self._client = MessageClient(self._on_client_message)
        try:
            self._client.connect(host, port)
            self._my_client_id = self._client.client_id
            self._schedule(lambda: self._status_label.configure(text=f"Connected: {host}:{port}", fg=GREEN))
            self._schedule(self._log, "SYSTEM", f"Connected as \"{self._nickname}\" (id: {self._my_client_id})", "ok")
        except Exception as e:
            self._schedule(lambda: self._status_label.configure(text="Connection failed!", fg=RED))
            self._schedule(self._log, "SYSTEM", f"Connection failed: {e}", "err")

    def _on_client_message(self, sender_id: str, nickname: str, raw: str):
        if sender_id == self._my_client_id:
            return
        pwd = self._password
        try:
            decrypted = decrypt(bytes.fromhex(raw), pwd)
            self._schedule(self._log, nickname, decrypted)
        except Exception as e:
            self._schedule(self._log, "DEBUG", f"raw={raw[:80]}  err={e}", "err")
            self._schedule(self._log, f"{nickname}", "[decryption failed]", "err")

    def _send_message(self):
        msg = self._message_entry.get().strip()
        if not msg:
            return
        self._message_entry.delete(0, "end")

        self._password = self._password_entry.get() or "encrit_default_key"
        self._nickname = self._nick_entry.get().strip() or "User"
        encrypted = encrypt(msg, self._password)
        payload = encrypted.hex()

        self._log("You", msg, "you")

        try:
            if self._is_server and self._server:
                self._server.broadcast("SERVER", self._nickname, payload)
            elif self._client:
                self._client.send(self._nickname, payload)
        except Exception as e:
            self._log("SYSTEM", f"Send failed: {e}", "err")

    def _disconnect(self):
        if self._server:
            self._server.stop()
            self._server = None
        if self._client:
            self._client.disconnect()
            self._client = None
        self._my_client_id = ""
        self._status_label.configure(text="Disconnected", fg=RED)
        self._log("SYSTEM", "Disconnected", "sys")

    def _clear_chat(self):
        self._chat_display.configure(state="normal")
        self._chat_display.delete("1.0", "end")
        self._chat_display.configure(state="disabled")

    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _on_close(self):
        self._disconnect()
        self.root.destroy()


if __name__ == "__main__":
    app = EncritApp()
    app.run()
