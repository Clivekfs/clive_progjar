from socket import *
import socket
import threading
import sys
from datetime import datetime

def proses_string(request_string):
    request_string = request_string.strip()
    balas = "ERROR: Unknown command\r\n"
    if (request_string == "TIME"):
        now = datetime.now()
        waktu = now.strftime("%H:%M:%S")
        balas = f"JAM {waktu}\r\n"
    elif (request_string == "QUIT"):
        balas = "QUIT_OK"
    return balas

class ProcessTheClient(threading.Thread):
    def __init__(self,connection,address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        rcv = ""
        try:
            while True:
                data = self.connection.recv(32)
                if not data:
                    break
                
                rcv += data.decode()
                
                while '\r\n' in rcv:
                    pos = rcv.find('\r\n')
                    command = rcv[:pos]
                    
                    rcv = rcv[pos+2:]
                    
                    hasil = proses_string(command)
                    
                    if hasil == "QUIT_OK":
                        self.connection.close()
                        return
                    
                    self.connection.sendall(hasil.encode())
        finally:
            self.connection.close()

class Server(threading.Thread):
    def __init__(self):
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread.__init__(self)

    def run(self):
        self.my_socket.bind(('0.0.0.0',45000))
        self.my_socket.listen(1)
        while True:
            self.connection, self.client_address = self.my_socket.accept()
            clt = ProcessTheClient(self.connection, self.client_address)
            clt.start()
            self.the_clients.append(clt)
    
def main():
    svr = Server()
    svr.start()

if __name__=="__main__":
    main()
