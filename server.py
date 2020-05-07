"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports

welcome_message = 'Приветствую тебя мой друг из другой вселенной \nПредставься мне, Великому Разуму \nВведи login:ТвойЛогинТут'
login_already_exists_message = 'Логин {} занят, попробуйте другой'
qnt_last_messages = -11


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def send_history(self):
        if len(self.server.history) > 0:
            last_messages = self.server.history[:qnt_last_messages:-1]
            last_messages.reverse()
            last_tem_messages = ('То что ты пропустил\n' + '\n'.join(last_messages)).encode()
            self.transport.write(last_tem_messages)

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                tmp_login = decoded.replace("login:", "").replace("\r\n", "")
                if tmp_login in [client.login for client in self.server.clients]:
                    self.transport.write(login_already_exists_message.format(tmp_login).encode())
                    # self.transport.close()
                    self.transport.abort()
                else:
                    self.login = tmp_login
                    self.transport.write(
                        f"Привет, {self.login}!".encode()
                    )
                    self.send_history()
            else:
                self.transport.write(welcome_message.encode())

        else:
            self.server.history.append(f"<{self.login}> {decoded}")
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        self.transport.write(welcome_message.encode())
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
