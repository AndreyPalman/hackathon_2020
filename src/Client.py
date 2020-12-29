import struct
import random
import threading
import socket

from pynput.keyboard import Listener

PORT = 13117
BUFFER_SIZE = 4096
TEAM_NAME = f"Team_{random.randint(0, 1000)}\n"
UTF8_ENCODE = 'utf-8'
SOCKET_LIST = []

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
        host_ip = addr[0]
        magic_cookie, message_type, tcp_server_port = struct.unpack('LBH', data_from_udp_server)
        if magic_cookie == 0xfeedbeef and message_type == 0x2:
            print(f'Received offer from {host_ip}, attempting to connect...')
            tcp_server_port = int(tcp_server_port)

            listener = Listener(on_press=on_press)
            listener.start()

            TCP_CLIENT_THREAD = threading.Thread(target=Start_Client, args=(tcp_server_port, team_name, host_ip),
                                                 name='TCP client')
            TCP_CLIENT_THREAD.start()


def on_press(pressed_key):
    if SOCKET_LIST[0]:
        SOCKET_LIST[0].sendall(str(pressed_key).encode(UTF8_ENCODE))


def Start_Client(tcp_server_port, team_name, host_ip):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            SOCKET_LIST.append(client_socket)
            client_socket.connect((host_ip, tcp_server_port))
            client_socket.sendall(team_name.encode(UTF8_ENCODE))
            while True:
                data_from_server = client_socket.recv(BUFFER_SIZE)
                print(data_from_server.decode(UTF8_ENCODE))
    except:
        print("Server disconnected, listening for offer requests...")
        SOCKET_LIST.clear()
        Main()


if __name__ == '__main__':
    print("Client started, listening for offer request...")
    Main()


