bind = "0.0.0.0:8080"
workers = 3
reload = True
worker_class = "gevent"
backlog = 2048
accesslog = "/home/ec2-user/punch.log"
loglevel = "debug"
