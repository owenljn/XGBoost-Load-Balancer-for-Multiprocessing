# -*- coding: utf-8 -*-

# XGBoost Server
#
# Author: Owen Lu
# --------------------------------------------------
# This module loads the xgboost models for each worker process to handle incoming concurrent requests

import zmq
import json
import pickle
import multiprocessing
# from xgboost import XGBRegressor, XGBClassifier, DMatrix

NBR_WORKERS = 4
num_gpus = 2
xgb_model_port = '5555'
xgb_model_path = './'  # Set the path here

def worker_routine(ident, gpu_id, context=None):
    socket = zmq.Context().socket(zmq.REQ)
    socket.identity = u"Worker-{}".format(ident).encode("ascii")
    socket.connect("ipc://backend.ipc")

    # Load XGBoost model inside worker routine
    model = pickle.load(open(xgb_model_path, 'rb'))
    model.set_params(gpu_id=gpu_id, n_jobs=-1, treemethod='gpu_hist', predictor='gpu_predictor')

    # Tell broker we're ready for work
    socket.send(b"READY")
    count = 0
    while True:
        address, empty, request = socket.recv_multipart()
        json_msg = request.decode('utf-8')
        print("{}: {}".format(socket.identity.decode("ascii"),
                              json_msg))

        try:
            count += 1

            print("Received request: \n\n", count, json_msg, "\n\n-----------\n\n")

            trans_request = json.loads(json_msg)

            prediction = model.predict(trans_request['data'])
            result = {}
            result['preds'] = prediction

        except Exception as ex:
            result = {'preds': 'error'}

        finally:
            s = json.dumps(result).encode('utf-8')
            socket.send_multipart([address, b"", s])


if __name__ == '__main__':
    url_worker = "ipc://backend.ipc"
    url_client = 'tcp://*:{}'.format(xgb_model_port)  # Different ports should be used for different translation engines

    context = zmq.Context.instance()
    clients = context.socket(zmq.ROUTER)
    clients.bind(url_client)
    backend = context.socket(zmq.ROUTER)
    backend.bind(url_worker)


    # Start background tasks
    def start(task, *args):
        process = multiprocessing.Process(target=task, args=args)
        process.daemon = True
        process.start()

    # Distribute GPU resources to all workers, here 2 GPUs resources are distributed to 4 workers
    for i in range(NBR_WORKERS):
        if i <= NBR_WORKERS / num_gpus:
            gpu_id = 0
            start(worker_routine, i, gpu_id)
        else:
            gpu_id = 1
            start(worker_routine, i, gpu_id)

    # Initialize main loop state
    workers = []
    _workers = workers.append
    poller = zmq.Poller()
    # Only poll for requests from backend until workers are available
    poller.register(backend, zmq.POLLIN)

    while True:
        sockets = dict(poller.poll())

        if backend in sockets:
            # Handle worker activity on the backend
            request = backend.recv_multipart()
            worker, empty, client = request[:3]
            if not workers:
                # Poll for clients now that a worker is available
                poller.register(clients, zmq.POLLIN)
            _workers(worker)
            if client != b"READY" and len(request) > 3:
                # If client reply, send rest back to frontend
                empty, reply = request[3:]
                clients.send_multipart([client, b"", reply])

        if clients in sockets:
            # Get next client request, route to last-used worker
            client, empty, request = clients.recv_multipart()
            worker = workers.pop(0)
            backend.send_multipart([worker, b"", client, b"", request])
            if not workers:
                # Don't poll clients if no workers are available
                poller.unregister(clients)
    # Clean up
    backend.close()
    clients.close()
    context.term()
