import struct
import threading
import socket
import time
from enum import Enum

HOST = socket.gethostbyname(socket.gethostname())
BROADCAST_PORT = 13117
TCP_SERVER_PORT = 31097
BUFFER_SIZE = 4096
UTF8_ENCODE = 'utf-8'

GROUP_A = []
GROUP_B = []
GROUP_A_SCORE = 0
GROUP_B_SCORE = 0
ACTIVE_CLIENTS_TREAD_LIST = []
ACTIVE_CONNECTION = 0

def Start_Server():
    Reset()

    # Start Multiple TCP connections server
    TCP_SERVER_THREAD = threading.Thread(target=Start_TCP_Server, name='TCP server')
    #TCP_SERVER_THREAD.setDaemon(True)

    # Start UDP server
    UDP_SERVER_THREAD = threading.Thread(target=Start_UDP_Server,args=(TCP_SERVER_THREAD,), name='UDP server')
    #UDP_SERVER_THREAD.setDaemon(True)

    # Starting both servers
    UDP_SERVER_THREAD.start()

def Start_UDP_Server(TCP_SERVER_THREAD):
    # Create a TCP/IP socket
    UDP_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    UDP_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    UDP_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Bind the socket to the port
    SERVER_ADDRESS = (HOST, BROADCAST_PORT)
    print('Server started, listening on IP address {}'.format(SERVER_ADDRESS[0]))
    TCP_SERVER_THREAD.start()

    while True:
        Game_started = False
        for i in range(10):
            Waiting_For_Clients(UDP_SOCKET)
            # Sleep for 1 second
            time.sleep(1)
        for i in range(10):
            Game_Mode(Game_started)
            time.sleep(1)
            Game_started = True

        Terminate_Teams_Conecction()
        print("Game over, sending out offer requests...")
        Stop_All_Client_Threads()
        Reset()




# Waiting for clients - sending out offer messages and responding to request messages
# and new TCP connections. You leave this state after 10 seconds.
def Waiting_For_Clients(UDP_SOCKET):
    udp_message_format = struct.pack('LBH', 0xfeedbeef, 0x2, TCP_SERVER_PORT)
    UDP_SOCKET.sendto(udp_message_format,('<broadcast>',BROADCAST_PORT))


# Game mode - collect characters from the network and calculate the score. You leave this
# state after 10 seconds.
def Game_Mode(is_game_started):
    if not is_game_started:
        data_to_send = "Welcome to Keyboard Spamming Battle Royale.\n" \
                       "Group 1:\n" \
                       "==\n" \
                       f"{GROUP_A[0][Team.TEAM_NAME.value]}" \
                       f"{GROUP_A[1][Team.TEAM_NAME.value]}" \
                       f"Group 1:\n" \
                       "==\n" \
                       f"{GROUP_B[0][Team.TEAM_NAME.value]}" \
                       f"{GROUP_B[1][Team.TEAM_NAME.value]}" \
                       "Start pressing keys on your keyboard as fast as you can!!"
        for team in GROUP_A + GROUP_B:
            team[Team.TEAM_CONNECTION.value].sendall(data_to_send.encode(UTF8_ENCODE))

def Terminate_Teams_Conecction():
    winning_group,winning_group_id = Get_Winner()
    first_team = 0
    second_team = 1

    message_to_send = "Game over!\n" \
                      f"Group 1 typed in {GROUP_A_SCORE} characters. Group 2 typed in {GROUP_B_SCORE} characters.\n" \
                      f"Group {winning_group_id} wins!\n\n" \
                      "Congratulation to the winners:\n" \
                      f"{winning_group[first_team][Team.TEAM_NAME.value]}" \
                      f"{winning_group[second_team][Team.TEAM_NAME.value]}"

    for team in GROUP_A + GROUP_B:
        team[Team.TEAM_CONNECTION.value].sendall(message_to_send.encode(UTF8_ENCODE))
        team[Team.TEAM_CONNECTION.value].close()

def Get_Winner():
    if GROUP_A_SCORE > GROUP_A_SCORE:
        return GROUP_A,1
    return GROUP_B,2

def Start_TCP_Server():
    global ACTIVE_CONNECTION
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, TCP_SERVER_PORT))
        server.listen()
        while True:
            # Waiting for client to connect - Blocking
            client_connection, client_address = server.accept()
            ACTIVE_CONNECTION = ACTIVE_CONNECTION + 1
            if ACTIVE_CONNECTION <= 4:
                client_thread = threading.Thread(target=Handle_Client_TCP_Connection,
                                                 args=(client_connection, client_address,),
                                                 name=f'Client_{ACTIVE_CONNECTION}')
                ACTIVE_CLIENTS_TREAD_LIST.append(client_thread)
                client_thread.start()


def Add_Team(team_name, client_address,client_connection):
    if len(GROUP_A) > len(GROUP_B):
        GROUP_B.append((team_name, client_address,client_connection, 0))
    else:
        GROUP_A.append((team_name, client_address,client_connection, 0))


def Handle_Client_TCP_Connection(client_connection,client_address):
    first_message = True
    try:
        while True:
            client_data = client_connection.recv(BUFFER_SIZE)
            if not client_data:
                break
            if first_message:
                Add_Team(client_data.decode(UTF8_ENCODE), client_address,client_connection)
                first_message = False
            else:
                print(f"received from client {client_data.decode(UTF8_ENCODE)}")
                Handle_Game(client_address)
    except:
        pass


class Team(Enum):
    TEAM_NAME = 0
    TEAM_ADDRESS = 1
    TEAM_CONNECTION = 2
    TEAM_SCORE = 3


def Handle_Game(client_address):
    global GROUP_A_SCORE,GROUP_B_SCORE
    for team in GROUP_A:
        if team[Team.TEAM_ADDRESS.value][1] == client_address[1]:
            GROUP_A_SCORE += 1
    for team in GROUP_B:
        if team[Team.TEAM_ADDRESS.value][1] == client_address[1]:
            GROUP_B_SCORE += 1

def Stop_All_Client_Threads():
    for active_client_thread in ACTIVE_CLIENTS_TREAD_LIST:
        try:
            active_client_thread.join()
        except:
            pass

def Reset():
    global GROUP_A, GROUP_B, ACTIVE_CONNECTION, ACTIVE_CLIENTS_TREAD_LIST, GROUP_A_SCORE, GROUP_B_SCORE
    GROUP_A = []
    GROUP_B = []
    ACTIVE_CLIENTS_TREAD_LIST = []
    ACTIVE_CONNECTION = 0
    GROUP_A_SCORE = 0
    GROUP_B_SCORE = 0

if __name__ == '__main__':
    Start_Server()
