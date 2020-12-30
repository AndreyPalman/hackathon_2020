#!/usr/bin/env python3
import atexit
import struct
import random
import sys
import threading
import socket
import termios
from select import select

PORT = 13117
BUFFER_SIZE = 4096
TEAM_NAME = f"2pack\n"
UTF8_ENCODE = 'utf-8'
SOCKET_LIST = []

stop_threads = False

import os

os.system("")

# Group of Different functions for different styles
class style():
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    PINK = '\033[95m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def send_input():
    kb = KBHit()
    while True:
        if stop_threads:
            break
        try:
            if kb.kbhit():
                try:
                    SOCKET_LIST[0].sendall(str(kb.getch()).encode(UTF8_ENCODE))
                except:
                    print(style.RED + f"Server closed socket - {SOCKET_LIST[0]}")
                    break
        except:
            break

def Main():

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as client_socket:
        # Enable broadcasting mode
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.bind(("", PORT))

        # data_from_udp_server = Magic cookie (4byte) + Message port (1byte) + port (2bytes)
        BUFFER_SIZE_FOR_FIRST_MESSAGE = 16
        #data_from_udp_server, addr = client_socket.recvfrom(BUFFER_SIZE)
        data_from_udp_server, addr = client_socket.recvfrom(BUFFER_SIZE_FOR_FIRST_MESSAGE)
        print(data_from_udp_server)
        print(len(data_from_udp_server))
        print(len(addr))
        host_ip = addr[0]
        #host_ip = '127.0.1.1'
        magic_cookie, message_type, tcp_server_port = struct.unpack('LBH', data_from_udp_server)
        if magic_cookie == 0xfeedbeef and message_type == 0x2:
            print(style.GREEN + f'Received offer from {host_ip}, attempting to connect...')
            tcp_server_port = int(tcp_server_port)

            SEND_DATA_TO_SERVER_THREAD = threading.Thread(target=send_input,
                                                 name='Send Data To Server')

            Start_Client(tcp_server_port, TEAM_NAME, host_ip,SEND_DATA_TO_SERVER_THREAD)


def Start_Client(tcp_server_port, team_name, host_ip,SEND_DATA_TO_SERVER_THREAD):
    global stop_threads
    stop_threads = False

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        SOCKET_LIST.append(client_socket)
        #  Trying to connect to server
        try:
            client_socket.connect((host_ip, tcp_server_port))
        except:
            print(style.RED + f"Couldn't connect to {host_ip}:{tcp_server_port}")
            Restart_Client()
        # Sending Team Name to Server
        try:
            client_socket.sendall(team_name.encode(UTF8_ENCODE))
        except:
            print(style.RED + f"Couldn't send to {host_ip}:{tcp_server_port}")
            Restart_Client()
        # Waiting to server send start game message
        try:
            welcome_data = client_socket.recv(BUFFER_SIZE)
            print(style.GREEN + welcome_data.decode(UTF8_ENCODE))
        except:
            print(style.RED + f"Couldn't receive from {host_ip}:{tcp_server_port}")
            print(style.WARNING + "Server disconnected, listening for offer requests...")
            Restart_Client()
        # Starting Listening to keyboard
        SEND_DATA_TO_SERVER_THREAD.start()
        # Waiting to to server send game over message
        try:
            game_over = client_socket.recv(BUFFER_SIZE)
            print(style.GREEN +game_over.decode(UTF8_ENCODE))
        except:
            print(style.RED + f"Couldn't receive from {host_ip}:{tcp_server_port}")
            print(style.WARNING + "Server disconnected, listening for offer requests...")
            stop_threads = True
            SEND_DATA_TO_SERVER_THREAD.join()
            Restart_Client()

        # KILL IT WITH FIRE#
        stop_threads = True
        SEND_DATA_TO_SERVER_THREAD.join()


    print(style.WARNING + "Server disconnected, listening for offer requests...")
    Restart_Client()


def Restart_Client():
    global SOCKET_LIST
    SOCKET_LIST.clear()
    Main()

class KBHit:

    def __init__(self):
        '''Creates a KBHit object that you can call to do various keyboard things.
        '''


        # Save the terminal settings
        self.fd = sys.stdin.fileno()
        self.new_term = termios.tcgetattr(self.fd)
        self.old_term = termios.tcgetattr(self.fd)

        # New terminal setting unbuffered
        self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)
        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)

        # Support normal-terminal reset at exit
        atexit.register(self.set_normal_term)


    def set_normal_term(self):
        ''' Resets to normal terminal.  On Windows this is a no-op.
        '''



        termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)


    def getch(self):
        ''' Returns a keyboard character after kbhit() has been called.
            Should not be called in the same program as getarrow().
        '''

        s = ''


        return sys.stdin.read(1)


    def getarrow(self):
        ''' Returns an arrow-key code after kbhit() has been called. Codes are
        0 : up
        1 : right
        2 : down
        3 : left
        Should not be called in the same program as getch().
        '''


        c = sys.stdin.read(3)[2]
        vals = [65, 67, 66, 68]

        return vals.index(ord(c.decode('utf-8')))


    def kbhit(self):
        ''' Returns True if keyboard character was hit, False otherwise.
        '''

        dr,dw,de = select([sys.stdin], [], [], 0)
        return dr != []

if __name__ == '__main__':
    print(style.WHITE + style.BOLD + "Client started, listening for offer request...")
    Main()