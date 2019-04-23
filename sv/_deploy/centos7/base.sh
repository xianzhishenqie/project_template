# 扩展源
yum install -y epel-release
rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY-EPEL-7
rpm --import http://li.nux.ro/download/nux/RPM-GPG-KEY-nux.ro
rpm -Uvh http://li.nux.ro/download/nux/dextop/el7/x86_64/nux-dextop-release-0-1.el7.nux.noarch.rpm
yum update -y

# 基础安装
yum -y install gcc make
yum -y install wget vim
yum -y install mariadb mariadb-devel mariadb-server
yum -y install redis

# python3安装
yum -y groupinstall "Development tools"
yum -y install zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel
yum -y install libffi-devel
cd /tmp/
mkdir /usr/local/python3
wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tar.xz
tar -xvJf  Python-3.7.3.tar.xz
cd Python-3.7.3
./configure --prefix=/usr/local/python3 --enable-optimizations
make && make install

ln -s /usr/local/python3/bin/python3 /usr/bin/python3
ln -s /usr/local/python3/bin/pip3 /usr/bin/pip3

# pip源配置
mkdir ~/.pip/
cat <<EOF >> ~/.pip/pip.conf
[global]
index-url = http://mirrors.aliyun.com/pypi/simple/

[install]
trusted-host=mirrors.aliyun.com
EOF
# 虚拟环境
pip3 install virtualenv
pip3 install virtualenvwrapper
# 配置虚拟环境
cat <<"EOF" >> /etc/profile
export PATH=/usr/local/python3/bin/:$PATH
export WORKON_HOME=$HOME/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/python3/bin/virtualenvwrapper.sh
EOF
source /etc/profile


cd /tmp
wget http://nginx.org/download/nginx-1.15.2.tar.gz
tar zxvf nginx-1.15.2.tar.gz
cd nginx-1.15.2
./configure --prefix=/usr/local/nginx --with-stream
make
make install
# 添加代理配置目录
mkdir /usr/local/nginx/conf/tcp.d/


# python2 pip安装
cd /tmp
curl -O https://bootstrap.pypa.io/get-pip.py
python get-pip.py
pip install  --upgrade pip
# 配置supervisor
pip install supervisor
cd /tmp
echo_supervisord_conf > supervisord.conf
cat <<EOF >> supervisord.conf
[include]
files = /etc/supervisord.d/*.conf
EOF
mv supervisord.conf /etc/
mkdir /etc/supervisord.d/
# 启动supervisor
touch /usr/lib/systemd/system/supervisord.service
cat <<EOF > /usr/lib/systemd/system/supervisord.service
[Unit]
Description=Supervisor daemon

[Service]
Type=forking
ExecStart=/usr/bin/supervisord -c /etc/supervisord.conf
ExecStop=/usr/bin/supervisorctl \$OPTIONS shutdown
ExecReload=/usr/bin/supervisorctl \$OPTIONS reload
KillMode=process
Restart=on-failure
RestartSec=42s

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable supervisord
systemctl start supervisord
