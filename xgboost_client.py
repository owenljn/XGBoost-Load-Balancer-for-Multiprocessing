# -*- coding: utf-8 -*-

# XGBoost client
#
# Author: Owen Lu
# --------------------------------------------------
# This module simulates multiple clients that are sending requests to XGBoost server concurrently
from __future__ import print_function
import os
import zmq
import json
import concurrent.futures

# Set it to any number, it means the number of concurrent connected clients that are sending requests
NBR_CLIENTS = 32
IP = '127.0.0.1'
PORT = 5555
PARAMS = {}


def client_task(identity):
    socket = zmq.Context().socket(zmq.REQ)
    socket.identity = u"Client-{}".format(identity).encode("ascii")

    # ip, eg. 127.0.0.1
    # port, eg. 5555
    socket.connect("tcp://{}:{}".format(IP, PORT))

    # Send request, get reply
    request = {PARAMS}
    socket.send_json(request)
    reply = socket.recv()
    s = json.loads(reply.decode('utf-8'))
    return s

def main():
    print('Starting client ...')
    # Start background tasks
    with concurrent.futures.ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        executor.map(client_task, list(range(NBR_CLIENTS)))

    print('Client started')


if __name__ == '__main__':
    main()
