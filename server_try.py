import socket

s = socket.socket()
s.connect(("172.16.6.55", 9876))
s.sendall("\n100.87-40.97-1-京A7895".encode("utf-8"))
s.close()
