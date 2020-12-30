#!/usr/bin/env python3

import struct
import threading
import socket
import time
from enum import Enum
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
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    PINK = '\033[95m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


HOST = socket.gethostbyname(socket.gethostname())
BROADCAST_PORT = 13117
TCP_SERVER_PORT = 31097
BUFFER_SIZE = 4096
UTF8_ENCODE = 'utf-8'
WAITING_TIME = 10
GAME_TIME = 10
ONE_SECOND = 1

GROUP_A = []
GROUP_B = []
GROUP_A_SCORE = 0
GROUP_B_SCORE = 0
ACTIVE_CLIENTS_TREAD_LIST = []
ACTIVE_CONNECTION = 0

MAXIMUM_SERVER_SCORE = 0
LETTERS_TYPED_GROUP_A = {}
LETTERS_TYPED_GROUP_B = {}
MAXIMUM_AVERAGE_CLICK_TIME = 0
AVERAGE_CLICK_TIME_WINNING_GROUP = 0
AVERAGE_CLICK_TIME_LOSING_GROUP = 0
SERVER_ROUNDS = 0

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
    print(style.PINK + 'Server started, listening on IP address {}'.format(SERVER_ADDRESS[0]))
    TCP_SERVER_THREAD.start()

    while True:
        Game_started = False
        for i in range(WAITING_TIME):
            Waiting_For_Clients(UDP_SOCKET)
            # Sleep for 1 second
            time.sleep(ONE_SECOND)
        for i in range(GAME_TIME):
            if ACTIVE_CONNECTION >= 1:
                Game_Mode(Game_started)
                time.sleep(ONE_SECOND)
                Game_started = True
            else:
                print(style.RED + 'No players joined, back to sending out offer requests')
                break

        Terminate_Teams_Conecction()
        print(style.PINK + "Game over!")
        print(style.PINK + Update_Statistics(max(GROUP_A_SCORE,GROUP_B_SCORE),min(GROUP_A_SCORE,GROUP_B_SCORE)))
        print(style.PINK + "sending out offer requests...")
        Stop_All_Client_Threads()
        Reset()

# Waiting for clients - sending out offer messages and responding to request messages
# and new TCP connections. You leave this state after 10 seconds.
def Waiting_For_Clients(UDP_SOCKET):
    udp_message_format = struct.pack('LBH', 0xfeedbeef, 0x2, TCP_SERVER_PORT)
    UDP_SOCKET.sendto(udp_message_format,('<broadcast>',BROADCAST_PORT))

def Get_Team_Name(Group):
    names_of_teams = ""
    for team in Group:
        names_of_teams += team[Team.TEAM_NAME.value]
    return names_of_teams

# Game mode - collect characters from the network and calculate the score. You leave this
# state after 10 seconds.
def Game_Mode(is_game_started):
    global SERVER_ROUNDS
    if not is_game_started:
        SERVER_ROUNDS += 1
        data_to_send = style.CYAN + "Welcome to Keyboard Spamming Battle Royale.\n" \
                       "Group 1:\n" \
                       "==\n" \
                       f"{Get_Team_Name(GROUP_A)}" \
                       f"Group 2:\n" \
                       "==\n" \
                       f"{Get_Team_Name(GROUP_B)}" \
                       "Start pressing keys on your keyboard as fast as you can!!"

        for team in GROUP_A + GROUP_B:
            try:
                team[Team.TEAM_CONNECTION.value].sendall(data_to_send.encode(UTF8_ENCODE))
            except:
                print(style.RED + f"Couldn't send welcome message to {Team[Team.TEAM_NAME.value]}")
                pass

def Terminate_Teams_Conecction():

    winning_group,winning_group_id = Get_Winner()
    message_to_send = style.RED + "Game over!\n" \
                      f"Group 1 typed in {GROUP_A_SCORE} characters. Group 2 typed in {GROUP_B_SCORE} characters.\n" \
                      f"Group {winning_group_id} wins!\n\n" \
                      "Congratulation to the winners:\n" \
                      f"{Get_Team_Name(winning_group)}"

    for team in GROUP_A + GROUP_B:
        if team[Team.TEAM_CONNECTION.value]:
            team[Team.TEAM_CONNECTION.value].sendall(message_to_send.encode(UTF8_ENCODE))
            team[Team.TEAM_CONNECTION.value].close()

def most_common_key(dict):
    max_value = 0
    max_key = None
    for key,value in dict.items():
        if value > max_value:
            max_value = value
            max_key = key
    return max_key


def Update_Statistics(winning_team_score, losing_team_score):
    global MAXIMUM_SERVER_SCORE,AVERAGE_CLICK_TIME_WINNING_GROUP,AVERAGE_CLICK_TIME_LOSING_GROUP,MAXIMUM_AVERAGE_CLICK_TIME,LETTERS_TYPED_GROUP_B,LETTERS_TYPED_GROUP_A
    MAXIMUM_SERVER_SCORE = max(MAXIMUM_SERVER_SCORE,winning_team_score)
    AVERAGE_CLICK_TIME_WINNING_GROUP = winning_team_score / GAME_TIME
    AVERAGE_CLICK_TIME_LOSING_GROUP = losing_team_score / GAME_TIME
    MAXIMUM_AVERAGE_CLICK_TIME = max(AVERAGE_CLICK_TIME_WINNING_GROUP,AVERAGE_CLICK_TIME_LOSING_GROUP,MAXIMUM_AVERAGE_CLICK_TIME)

    common_A_key = most_common_key(LETTERS_TYPED_GROUP_A)
    common_A_value = LETTERS_TYPED_GROUP_A.get(common_A_key)
    common_B_key = most_common_key(LETTERS_TYPED_GROUP_B)
    common_B_value = LETTERS_TYPED_GROUP_B.get(common_B_key)

    group_A_chars = len(LETTERS_TYPED_GROUP_A)
    group_B_chars = len(LETTERS_TYPED_GROUP_B)

    statistic_to_print = style.CYAN + style.BOLD + f"Server highest score : {MAXIMUM_SERVER_SCORE}\n" \
                       f"Server fastest click time : {MAXIMUM_AVERAGE_CLICK_TIME} types per seconds\n" \
                       f"Winning average click time : {AVERAGE_CLICK_TIME_WINNING_GROUP} types per seconds\n" \
                       f"Losing average click time : {AVERAGE_CLICK_TIME_LOSING_GROUP} types per seconds\n" \
                       f"Most common typed letter of group A : {common_A_key}, typed in {common_A_value} times\n" \
                       f"Most common typed letter of group B : {common_B_key}, typed in {common_B_value} times\n" \
                       f"Group A typed in {group_A_chars} different chars\n" \
                       f"Group B typed in {group_B_chars} different chars\n"
    return statistic_to_print

def Get_Winner():
    if GROUP_A_SCORE > GROUP_B_SCORE:
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
            ACTIVE_CONNECTION += 1
            client_thread = threading.Thread(target=Handle_Client_TCP_Connection,
                                             args=(client_connection, client_address,),
                                             name=f'Client_{ACTIVE_CONNECTION}')
            ACTIVE_CLIENTS_TREAD_LIST.append(client_thread)
            client_thread.start()

def Add_Team(team_name, client_address,client_connection):
    if len(GROUP_A) > len(GROUP_B):
        GROUP_B.append((team_name, client_address,client_connection))
    else:
        GROUP_A.append((team_name, client_address,client_connection))

def Handle_Client_TCP_Connection(client_connection,client_address):
    first_message = True
    try:
        while True:
            client_data = client_connection.recv(BUFFER_SIZE).decode(UTF8_ENCODE)
            if not client_data:
                break
            if first_message:
                Add_Team(client_data, client_address,client_connection)
                first_message = False
            else:
                #print(f"received from client {client_data.decode(UTF8_ENCODE)}")
                Handle_Game(client_address,client_data)
    except:
        print(style.RED + f"Couldn't get team name from {client_address}")
        pass

class Team(Enum):
    TEAM_NAME = 0
    TEAM_ADDRESS = 1
    TEAM_CONNECTION = 2

# group A = True / group B = False
def Add_Letter(group,client_letter):
    global LETTERS_TYPED_GROUP_A,LETTERS_TYPED_GROUP_B
    # Team A
    if group:
        if LETTERS_TYPED_GROUP_A.get(client_letter):
            LETTERS_TYPED_GROUP_A[client_letter] += 1
        else:
            LETTERS_TYPED_GROUP_A[client_letter] = 1
    # Team B
    else:
        if LETTERS_TYPED_GROUP_B.get(client_letter):
            LETTERS_TYPED_GROUP_B[client_letter] += 1
        else:
            LETTERS_TYPED_GROUP_B[client_letter] = 1


def Handle_Game(client_address,client_data):
    global GROUP_A_SCORE,GROUP_B_SCORE
    for team in GROUP_A:
        if team[Team.TEAM_ADDRESS.value][1] == client_address[1]:
            Add_Letter(True,client_data)
            GROUP_A_SCORE += 1
    for team in GROUP_B:
        if team[Team.TEAM_ADDRESS.value][1] == client_address[1]:
            Add_Letter(False, client_data)
            GROUP_B_SCORE += 1

def Stop_All_Client_Threads():
    for active_client_thread in ACTIVE_CLIENTS_TREAD_LIST:
        try:
            active_client_thread.join()
        except:
            pass

def Reset():
    global GROUP_A, GROUP_B, ACTIVE_CONNECTION, ACTIVE_CLIENTS_TREAD_LIST, GROUP_A_SCORE, GROUP_B_SCORE\
        ,AVERAGE_CLICK_TIME_WINNING_GROUP,AVERAGE_CLICK_TIME_LOSING_GROUP,LETTERS_TYPED_GROUP_A,LETTERS_TYPED_GROUP_B
    GROUP_A = []
    GROUP_B = []
    ACTIVE_CLIENTS_TREAD_LIST = []
    ACTIVE_CONNECTION = 0
    GROUP_A_SCORE = 0
    GROUP_B_SCORE = 0
    LETTERS_TYPED_GROUP_A = {}
    LETTERS_TYPED_GROUP_B = {}

def Print_Statistics():
    pass

if __name__ == '__main__':
    Start_Server()
