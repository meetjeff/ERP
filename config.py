bind = "0.0.0.0:8080"
#workers = 3
reload = True
worker_class = "gevent"
backlog = 2048
accesslog = "/home/punch/punch.log"
loglevel = "debug"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
