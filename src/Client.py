#!/usr/bin/env python3
import atexit
from termios import tcflush, TCIFLUSH
import struct
import random
import sys
import threading
import socket
import termios
import tty
from select import select

PORT = 13117
BUFFER_SIZE = 4096
TEAM_NAME = f"Team_{random.randint(0, 1000)}\n"
UTF8_ENCODE = 'utf-8'
SOCKET_LIST = []

stop_threads = False

# # save the terminal settings
# fd = sys.stdin.fileno()
# new_term = termios.tcgetattr(fd)
# old_term = termios.tcgetattr(fd)
#
# # new terminal setting unbuffered
# new_term[3] = (new_term[3] & ~termios.ICANON & ~termios.ECHO)

# def getchar():
#     fd = sys.stdin.fileno()
#     old_settings = termios.tcgetattr(fd)
#     try:
#         tty.setraw(sys.stdin.fileno())
#         ch = sys.stdin.read(1)
#     finally:
#         termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
#     return ch

def send_input():
    kb = KBHit()
    while True:
        if stop_threads:
            break
        try:
            if kb.kbhit():
                SOCKET_LIST[0].sendall(str(kb.getch()).encode(UTF8_ENCODE))
        except:
            print('No Socket found')
            break


def Main():
    # team_name = input('Enter team name')
    team_name = TEAM_NAME

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as client_socket:
        # Enable broadcasting mode
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_socket.bind(("", PORT))

        # data_from_udp_server = Magic cookie (4byte) + Message port (1byte) + port (2bytes)
        data_from_udp_server, addr = client_socket.recvfrom(BUFFER_SIZE)
        #host_ip = addr[0]
        host_ip = '127.0.1.1'
        magic_cookie, message_type, tcp_server_port = struct.unpack('LBH', data_from_udp_server)
        if magic_cookie == 0xfeedbeef and message_type == 0x2:
            print(f'Received offer from {host_ip}, attempting to connect...')
            tcp_server_port = int(tcp_server_port)

            SEND_DATA_TO_SERVER_THREAD = threading.Thread(target=send_input,
                                                 name='Send Data To Server')

            Start_Client(tcp_server_port, team_name, host_ip,SEND_DATA_TO_SERVER_THREAD)


def Start_Client(tcp_server_port, team_name, host_ip,SEND_DATA_TO_SERVER_THREAD):
    global stop_threads
    print(f"stop thread condition before: {stop_threads}")
    stop_threads = False
    print(f"stop thread condition after: {stop_threads}")
    #try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        SOCKET_LIST.append(client_socket)
        client_socket.connect((host_ip, tcp_server_port))
        print('Connected')
        client_socket.sendall(team_name.encode(UTF8_ENCODE))

        welcoe_data = client_socket.recv(BUFFER_SIZE)
        print(welcoe_data.decode(UTF8_ENCODE))


        SEND_DATA_TO_SERVER_THREAD.start()


        game_over = client_socket.recv(BUFFER_SIZE)
        print(game_over.decode(UTF8_ENCODE))
        # KILL IW WITH FIRE

        stop_threads = True
        SEND_DATA_TO_SERVER_THREAD.join()


    print("Server disconnected, listening for offer requests...")
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
    print("Client started, listening for offer request...")
    Main()