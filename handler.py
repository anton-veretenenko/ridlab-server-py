import select
import os
import socket

class SEHandler:

    __resp_200 = b'HTTP/1.0 200 OK\r\n\r\n'
    __resp_404 = b'HTTP/1.0 404 Not Found\r\n\r\n'
    __resp_cont = b'Content-Type: application/octet-stream\r\nContent-Length: %d\r\n\r\n'

    def __init__(self, sock):
        self.__socket = sock;
        self.__datain = b''
        self.__dataout = b'';
    
    def pollin(self, event):
        datain = self.__socket.recv(1024)
        if not datain:
            pass
        else:
            self.__datain += datain
            if b'\n\n' in self.__datain or b'\r\n\r\n' in self.__datain:
                # end of request detected
                select.epoll.modify(self.__socket.fileno(), select.EPOLLOUT);
        pass

    def pollout(self, event):
        pass

    def pollhup(self, event):
        pass

    def _close_force(self):
        self._socket.shutdown(socket.SHUT_RDWR)

    def _close(self):
        self._socket.close()
    
    def _del(self) :
        del self._socket