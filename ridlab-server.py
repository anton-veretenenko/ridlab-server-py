import socket
import select
from handler import SEHandler
 
ssocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
ssocket.bind(('127.0.0.1', 8181))
ssocket.listen(1)
ssocket.setblocking(0)

epoll = select.epoll()
epoll.register(ssocket.fileno(), select.EPOLLIN)
 
try:
    handlers = {}
    while True:
        events = epoll.poll(1)
        for fileno, event in events:
            if fileno == ssocket.fileno():
                connection, address = ssocket.accept()
                connection.setblocking(0)
                epoll.register(connection.fileno(), select.EPOLLIN)
                handlers[connection.fileno()] = SEHandler(connection, epoll)

            elif event & select.EPOLLIN:
                handlers[fileno].pollin()

            elif event & select.EPOLLOUT:
                handlers[fileno].pollout()
                    
            elif event & select.EPOLLHUP:
                handlers[fileno].pollhup()
                del handlers[fileno]
finally:
    epoll.unregister(ssocket.fileno())
    epoll.close()
    ssocket.close()