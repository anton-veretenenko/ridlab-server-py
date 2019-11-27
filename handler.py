import select
import os
import socket

class SEHandler:

    __resp_200 = b'HTTP/1.0 200 OK\r\n\r\n'
    __resp_404 = b'HTTP/1.0 404 Not Found\r\n\r\n'
    __resp_cont = b'Content-Type: application/octet-stream\r\nContent-Length: %d\r\n\r\n'

    def __init__(self, sock, epoll):
        self.__socket = sock
        self.__epoll = epoll
        self.__datain = b''
        self.__dataout = b''
    
    def pollin(self):
        datain = self.__socket.recv(1024)
        if not datain:
            # no data but pollin called, probably connection closed by client
            self.__epoll.modify(self.__socket.fileno(), select.EPOLLET)
            self._close_force()
        else:
            self.__datain += datain
            if b'\n\n' in self.__datain or b'\r\n\r\n' in self.__datain:
                # end of request detected, process and swith to output
                self.__epoll.modify(self.__socket.fileno(), select.EPOLLOUT)
                self.__dataout = self.__resp_cont % 2

    def pollout(self):
        # put out dataout
        written = self.__socket.send(self.__dataout)
        self.__dataout = self.__dataout[written:]
        # and check if there are any left
        if len(self.__dataout) == 0:
            self.__epoll.modify(self.__socket.fileno(), 0)
            self._close_force();

    def pollhup(self):
        self.__epoll.unregister(self.__socket.fileno())
        self._close()
        self._del()

    def _close_force(self):
        self.__socket.shutdown(socket.SHUT_RDWR)

    def _close(self):
        self.__socket.close()
    
    def _del(self) :
        del self.__socket