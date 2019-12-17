bind = "127.0.0.1:9000"                   # Don't use port 80 becaue nginx occupied it already.
errorlog = '/Users/crea/projects/AI-Music/Server/logs/gunicorn-error.log'  # Make sure you have the log folder create
accesslog = '/Users/crea/projects/AI-Music/Server/logs/gunicorn-access.log'
loglevel = 'debug'
workers = 3     # the number of recommended workers is '2 * number of CPUs + 1'