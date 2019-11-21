# -*- coding: utf-8 -*-

# XGBoost client
#
# Author: Owen Lu
# --------------------------------------------------
# This module simulates multiple clients that are sending requests to XGBoost server concurrently
from __future__ import print_function

import concurrent.futures
import json
import os

import zmq

# Set it to any number, it means the number of concurrent connected clients that are sending requests
NBR_CLIENTS = 32
IP = '127.0.0.1'  # ip address is the ip of the back-end XGBoost server
xgb_model_port = '5555'  # the port must be the same as the back-end XGBoost server
PARAMS = {}  # Parameters contains the front-end request content


def client_task(identity):
    context = zmq.Context.instance()
    socket = context.socket(zmq.REQ)
    socket.identity = u"Client-{}".format(identity).encode("ascii")

    # ip, eg. 127.0.0.1
    # port, eg. 5555
    socket.connect("tcp://{}:{}".format(IP, xgb_model_port))

    # Send request, get reply
    request = {PARAMS}
    socket.send_json(request)
    reply = socket.recv()
    s = json.loads(reply.decode('utf-8'))

    # Clean up by explicitly calling socket close and context terminate
    socket.close()
    context.term()
    return s


def main():
    print('Starting client ...')
    # Start background tasks
    with concurrent.futures.ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        executor.map(client_task, list(range(NBR_CLIENTS)))

    print('Client started')


if __name__ == '__main__':
    main()
