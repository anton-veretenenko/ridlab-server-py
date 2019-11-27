import select
import os
import socket

class FHandler:

    __socket = None
    __file = None
    __size = 0
    __pos = 0

    def __init__(self, request, socket):
        self.__socket = socket
        data = request.strip().split()
        if data[0].lower() == b'get':
            path = data[1].strip(b'\\').replace(b'..', b'').replace(b'./', b'').decode()
            path = os.path.dirname(os.path.realpath(__file__)) + '/files' + path
            if os.path.isfile(path):
                # file exists, open it
                try:
                    self.__file = open(path, 'rb')
                    self.__file.seek(0, os.SEEK_END)
                    self.__size = self.__file.tell()
                    self.__file.seek(0, os.SEEK_SET)
                except IOError:
                    self.__file = None
                    self.__size = 0

    @property
    def file(self):
        return self.__file
    
    @property
    def size(self):
        return self.__size
    
    def send(self):
        data = self.__file.read(32)
        end = False
        if self.__file.tell() == self.__size:
            end = True
        if data is not None:
            sent = self.__socket.send(data)
            if not end and sent < 32:
                self.__file.seek(0 - (32 - sent), os.SEEK_CUR)
            if end:
                return False
            else:
                return True
        else:
            self.__file.close()
            return False

class SEHandler:

    __resp_200 = b'HTTP/1.0 200 OK\r\n'
    __resp_404 = b'HTTP/1.0 404 Not Found\r\n\r\n'
    __resp_cont = b'Content-Type: application/octet-stream\r\nContent-Length: %d\r\n\r\n'

    def __init__(self, sock, epoll):
        self.__socket = sock
        self.__epoll = epoll
        self.__datain = b''
        self.__dataout = b''
        self.__fhandler = None
    
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
                self.__fhandler = FHandler(self.__datain, self.__socket)
                if self.__fhandler.file is None:
                    self.__dataout = self.__resp_404;
                else:
                    self.__dataout = self.__resp_200 + (self.__resp_cont % self.__fhandler.size)

    def pollout(self):
        if len(self.__dataout) > 0:
            # put out header
            written = self.__socket.send(self.__dataout)
            self.__dataout = self.__dataout[written:]
        elif self.__fhandler.file is not None:
            # send file if found
            if self.__fhandler.send() == False:
                # end transmission if file ended
                self._end()
        else:
            self._end()

    def pollhup(self):
        self.__epoll.unregister(self.__socket.fileno())
        self._close()
        self._del()
    
    def _end(self):
        self.__epoll.modify(self.__socket.fileno(), 0)
        self._close_force()

    def _close_force(self):
        self.__socket.shutdown(socket.SHUT_RDWR)

    def _close(self):
        self.__socket.close()
    
    def _del(self):
        del self.__socket