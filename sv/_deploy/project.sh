PRODUCT_NAME=sv
PRODUCT_PORT=8077
PRODUCT_DIR=/home/${PRODUCT_NAME}

mysql -e "
CREATE USER '"${PRODUCT_NAME}"'@'%' IDENTIFIED BY '"${PRODUCT_NAME}"';
CREATE USER '"${PRODUCT_NAME}"'@'localhost' IDENTIFIED BY '"${PRODUCT_NAME}"';
CREATE DATABASE "${PRODUCT_NAME}" DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
GRANT ALL PRIVILEGES ON "${PRODUCT_NAME}".* TO '"${PRODUCT_NAME}"'@'%';
GRANT ALL PRIVILEGES ON "${PRODUCT_NAME}".* TO '"${PRODUCT_NAME}"'@'localhost';
"
mkvirtualenv ${PRODUCT_NAME}
workon ${PRODUCT_NAME}
cd ${PRODUCT_DIR}
pip install -r requirements.txt


# 配置ningx
touch /usr/local/nginx/conf/${PRODUCT_NAME}.conf
cat <<EOF > /usr/local/nginx/conf/${PRODUCT_NAME}.conf
#user  nobody;
daemon off;
worker_processes  4;
events {
    worker_connections  1024;
}

stream {
    include tcp.d/*.conf;
}

http {
    include       mime.types;
    default_type  application/octet-stream;
    log_format  main  '\$remote_addr - \$remote_user [\$time_local] "\$request" '
                      '\$status \$body_bytes_sent "\$http_referer" '
                      '"\$http_user_agent" "\$http_x_forwarded_for"';
    sendfile        on;
    keepalive_timeout  65;
    server {
        listen       80;
        charset utf-8;
        access_log  logs/host.access.log  main;
        location /static {alias ${PRODUCT_DIR}/static/;}
        location /media {alias ${PRODUCT_DIR}/media/;}
        location / {
            client_max_body_size    100m;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header Host \$http_host;
            proxy_redirect off;
            proxy_pass http://127.0.0.1:${PRODUCT_PORT};
        }

        error_page   500 502 503 504  /50x.html;
        location = /50x.html {root   html; }
    }
}
EOF


# 配置nginx, memcached
touch /etc/supervisord.d/service.conf
cat <<EOF > /etc/supervisord.d/service.conf
[program:nginx]
command=/usr/local/nginx/sbin/nginx -c /usr/local/nginx/conf/${PRODUCT_NAME}.conf
autostart=true
autorestart=true
user=root

[program:redis]
command=redis-server
autostart=true
autorestart=true
user=root
EOF


# 配置sv supervisor
touch /etc/supervisord.d/${PRODUCT_NAME}.conf
cat <<EOF > /etc/supervisord.d/${PRODUCT_NAME}.conf
[program:${PRODUCT_NAME}]
command=/root/.virtualenvs/${PRODUCT_NAME}/bin/gunicorn ${PRODUCT_NAME}.wsgi -c gunicorn_config.py
directory=${PRODUCT_DIR}
autostart=true
autorestart=true
user=root

[program:daphne]
command=/root/.virtualenvs/${PRODUCT_NAME}/bin/daphne ${PRODUCT_NAME}.asgi:application -b 127.0.0.1 -p 8088
directory=${PRODUCT_DIR}
autostart=false
autorestart=false
user=root

[program:ws_worker]
command=/root/.virtualenvs/${PRODUCT_NAME}/bin/python manage.py runworker --only-channels=websocket.*
directory=${PRODUCT_DIR}
numprocs=4
process_name=%(program_name)s_%(process_num)02d
autostart=false
autorestart=false
user=root
EOF

supervisorctl update
