import multiprocessing

bind = '127.0.0.1:8077'
worker_class = 'gevent'
workers = multiprocessing.cpu_count() * 1
daemon = False

loglevel = 'info'
errorlog = './log/error.log'
accesslog = './log/access.log'
