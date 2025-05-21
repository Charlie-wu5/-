import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QVBoxLayout, QHBoxLayout, QMessageBox, QFormLayout, QGroupBox)
from PyQt5.QtCore import pyqtSignal, Qt
import socket
import threading
from datetime import datetime

APP_STYLE = """
    QWidget {
        background-color: #e6f2ff;
        font-family: "Microsoft YaHei";
        font-size: 14px;
    }
    QLineEdit {
        border: 1px solid gray;
        border-radius: 5px;
        padding: 4px;
        background: white;
    }
    QPushButton {
        background-color: #4da6ff;
        color: white;
        border-radius: 5px;
        padding: 5px 10px;
    }
    QPushButton:hover {
        background-color: #3399ff;
    }
    QTextEdit {
        background-color: #ffffff;
        border: 1px solid #ccc;
        border-radius: 4px;
    }
    QGroupBox {
        border: 1px solid #87cefa;
        border-radius: 5px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 3px 0 3px;
    }
"""

class LoginWindow(QWidget):
    login_success = pyqtSignal()
    register_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("交管系统 - 登录")
        self.setFixedSize(400, 500)

        form_layout = QFormLayout()
        self.user_input = QLineEdit()
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("用户名:", self.user_input)
        form_layout.addRow("密码:", self.pwd_input)

        login_btn = QPushButton("登录")
        register_btn = QPushButton("注册")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(login_btn)
        btn_layout.addWidget(register_btn)

        layout = QVBoxLayout()
        layout.addStretch(1)
        layout.addLayout(form_layout)
        layout.addLayout(btn_layout)
        layout.addStretch(1)

        self.setLayout(layout)

        login_btn.clicked.connect(self.check_login)
        register_btn.clicked.connect(self.register_clicked)

    def check_login(self):
        if self.user_input.text() == "admin" and self.pwd_input.text() == "123456":
            self.login_success.emit()
            self.close()
        else:
            QMessageBox.warning(self, "错误", "账号或密码错误")

class RegisterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("交管系统 - 注册")
        self.setFixedSize(400, 500)

        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.id_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.code_input = QLineEdit()

        form_layout.addRow("姓名:", self.name_input)
        form_layout.addRow("身份证:", self.id_input)
        form_layout.addRow("手机号:", self.phone_input)
        form_layout.addRow("验证码:", self.code_input)

        register_btn = QPushButton("注册（展示用）")

        layout = QVBoxLayout()
        layout.addStretch(1)
        layout.addLayout(form_layout)
        layout.addWidget(register_btn)
        layout.addStretch(1)
        self.setLayout(layout)

        register_btn.clicked.connect(self.show_success)

    def show_success(self):
        QMessageBox.information(self, "提示", "这是一个展示用注册界面，不执行实际注册。")

class ServerWindow(QWidget):
    vehicle_signal = pyqtSignal(str, str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("交管系统 - 服务器端")
        self.setFixedSize(1200, 900)

        ip_label = QLabel("IP 地址:")
        port_label = QLabel("端口:")
        self.ip_input = QLineEdit("172.16.6.43")
        self.port_input = QLineEdit("8765")
        self.start_btn = QPushButton("启动服务器")

        ip_layout = QHBoxLayout()
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(self.ip_input)

        port_layout = QHBoxLayout()
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)

        control_layout = QHBoxLayout()
        control_layout.addLayout(ip_layout)
        control_layout.addLayout(port_layout)
        control_layout.addWidget(self.start_btn)

        self.output = QTextEdit()
        self.output.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addLayout(control_layout)
        layout.addWidget(QLabel("日志输出:"))
        layout.addWidget(self.output)
        self.setLayout(layout)

        self.start_btn.clicked.connect(self.start_server)

    def start_server(self):
        ip = self.ip_input.text()
        port = int(self.port_input.text())
        threading.Thread(target=self.run_server, args=(ip, port), daemon=True).start()

    def run_server(self, ip, port):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((ip, port))
        server.listen(5)
        self.output.append("服务器已启动，等待连接...")
        while True:
            client, _ = server.accept()
            threading.Thread(target=self.handle_client, args=(client,), daemon=True).start()

    def handle_client(self, client):
        while True:
            try:
                raw = client.recv(1024)
                if not raw:
                    break
                try:
                    data = raw.decode("utf-8")
                except UnicodeDecodeError:
                    try:
                        data = raw.decode("gbk")
                    except:
                        data = raw.decode("latin1")

                data = data.strip().replace('\x02', '').replace('\x03', '')
                self.output.append(f"收到: {data}")
                parts = data.strip().split("-")
                if len(parts) == 4 and parts[2] in ["1", "2"]:
                    try:
                        # 正确的速度计算：位置差
                        speed = float(parts[0]) - float(parts[1])
                        plate = parts[3].strip()
                        if plate == "0000" or plate == "皖A0000":
                            continue
                        violation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        if parts[2] == "1" and speed > 40:
                            print(f"超速判断通过: {plate}, 速度: {speed}")
                            self.vehicle_signal.emit("Overspeed", plate, violation_time)
                            response = f"{plate}-{speed:.2f}km/h-over speed\n"
                            client.send(response.encode("utf-8"))
                        elif parts[2] == "2" and speed > 0:
                            print(f"闯红灯判断通过: {plate}, 速度: {speed}")
                            self.vehicle_signal.emit("RedLight", plate, violation_time)
                            response = f"{plate}-{speed:.2f}km/h-run a light\n"
                            client.send(response.encode("utf-8"))
                    except Exception as e:
                        print("解析错误:", e)
            except:
                break
        client.close()

class ViolationWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("交管系统 - 违规车辆显示")
        self.setFixedSize(1200, 900)

        layout = QVBoxLayout()

        speed_group = QGroupBox("超速车辆")
        self.speed_text = QTextEdit()
        self.speed_text.setReadOnly(True)
        speed_layout = QVBoxLayout()
        speed_layout.addWidget(self.speed_text)
        speed_group.setLayout(speed_layout)

        light_group = QGroupBox("闯红灯车辆")
        self.light_text = QTextEdit()
        self.light_text.setReadOnly(True)
        light_layout = QVBoxLayout()
        light_layout.addWidget(self.light_text)
        light_group.setLayout(light_layout)

        layout.addWidget(speed_group)
        layout.addWidget(light_group)
        self.setLayout(layout)

    def update_display(self, type_, msg, time):
        if type_ == "Overspeed":
            self.speed_text.append(f"{time} - {msg}")
        elif type_ == "RedLight":
            self.light_text.append(f"{time} - {msg}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)

    login = LoginWindow()
    register = RegisterWindow()
    server = ServerWindow()
    display = ViolationWindow()

    def open_main():
        server.show()
        display.show()

    def show_register():
        register.show()

    login.login_success.connect(open_main)
    login.register_clicked.connect(show_register)
    server.vehicle_signal.connect(display.update_display)

    login.show()
    sys.exit(app.exec_())
