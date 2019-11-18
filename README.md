# XGBoost-Load-Balancer-for-Multiprocessing
This is a workaround to bypass the multiprocessing issue of XGBoost, since XGBoost is not thread-safe, running the model in the multiprocessing environment throws 'dmlc::Error'

The xgboost_client.py here works as a front-end simulator that simulates multiple concurrent requests, these requests are attemping to call predict method of xgboost models, but instead of calling the predict method directly, they send requests to back-end using ZMQ load balancer.

The xgboost_server.py is the back-end that uses multiple worker instances to handle front-end requests, each worker routine has its own XGBoost model initialized, the requests coming from the front-end get distributed evenly to the back-end workers. Note the number of the maximum back-end workers is limited by your GPU memory, if you are using CPU, then theoretically you can initiate more workers without memory issue

Note this is just a demo code that displays how this load balancing mechanism can help avoid the dmlc error when using XGBoost with multiprocessing. Please modify the code accordingly to your own implementation.

