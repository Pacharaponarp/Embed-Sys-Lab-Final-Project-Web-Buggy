import socket
import os
import time
import dotenv
from flask import Flask, render_template
from queue import Queue
from threading import Thread

dotenv.load_dotenv()

httpServer = Flask(os.getenv('PROJECT_NAME'))
dataQueue = Queue()
clientDataQueue = Queue()
lastPush = 0
clientState = {"isOnline": False}


def socketServer(dataQueue: Queue, clientDataQueue: Queue):
    with open("ThreadLog.txt", "a") as fp:
        fp.write("[Socket] Thread Open\n")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((os.getenv('HOST'), int(os.getenv('SOCKET_PORT'))))
    sock.listen(0)
    while True:
        client, addr = sock.accept()
        with open("ThreadLog.txt", "a") as fp:
            fp.write("[Socket] Client Connect\n")
        print("[Socket] Client Connect")
        try:
            while True:
                if not dataQueue.empty():
                    client.send(dataQueue.get())
                time.sleep(0.001)
                clientData = client.recv(1)
                if clientData != None:
                    with open("ThreadLog.txt", "a") as fp:
                        fp.write(f"{clientData}\n")
                    print(clientData)
                    clientDataQueue.put(clientData)
        except:
            client.close()
            with open("ThreadLog.txt", "a") as fp:
                fp.write("[Socket] Client Disconnect\n")
            print("[Socket] Client Disconnect")
            clientDataQueue.put(b'd')


@httpServer.route("/", methods=['GET'])
def index():
    return render_template('index.html')


@httpServer.route("/move/<direction>", methods=['POST'])
def move(direction):
    direction = str(direction)
    global dataQueue
    global lastPush
    if (direction in ['w', 's', 'a', 'd'] and time.time()-lastPush > 0.001):
        lastPush = time.time()
        dataQueue.put(bytes(direction, 'ascii'))
    elif (direction == "stop" and time.time()-lastPush > 0.001):
        lastPush = time.time()
        dataQueue.put(bytes('x', 'ascii'))
    return ""


@httpServer.route("/state", methods=['GET'])
def state():
    global clientDataQueue

    while not clientDataQueue.empty():
        data = clientDataQueue.get().decode('ascii')
        with open("WebLog.txt", "a") as fp:
            fp.write(f"Receive Data From Client Data Queue: {data}\n")
        if data == 'c':
            clientState['isOnline'] = True
        elif data == 'd':
            clientState['isOnline'] = False
    return clientState


Thread(target=socketServer, args=(dataQueue, clientDataQueue,)).start()
httpServer.run(
    host=os.getenv('HOST'), port=int(os.getenv('HTTP_PORT')))
