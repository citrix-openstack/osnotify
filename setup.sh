#!/bin/bash

function install_dependencies
{
(
export DEBIAN_FRONTEND=noninteractive
sudo apt-get install -qy libtool autoconf automake uuid-dev g++ make \
python-pip python-dev python-virtualenv
)
}

function compile_install_zmq
{
ZMQ=$(mktemp -d)
(
cd "$ZMQ"
wget http://download.zeromq.org/zeromq-3.2.2.tar.gz
tar -xzf zeromq-3.2.2.tar.gz
cd zeromq-3.2.2/
./configure --prefix="$1/zmq"
make
make install
)
rm -rf "$ZMQ"
}

function setup_pyzmq
{
ZMQ=$(mktemp -d)
(
cd "$ZMQ"
wget https://pypi.python.org/packages/source/p/pyzmq/pyzmq-13.0.0.tar.gz
tar -xzf pyzmq-13.0.0.tar.gz
cd pyzmq-13.0.0
python setup.py configure --zmq="$1"
python setup.py install
)
rm -rf "$ZMQ"
}

function osnotify_setup_venv
{
    [ -e "$1/env" ] || virtualenv "$1/env"
    . "$1/env/bin/activate"
    setup_pyzmq "$1/zmq"
}

function osnotify_install
{
    [ -e "$1" ] && {
        echo "The given directory [$1] already exists"
        exit 1
    }
    compile_install_zmq "$1"
    osnotify_setup_venv "$1"
    pip install https://github.com/citrix-openstack/osnotify/archive/master.zip
    sudo "$1/env/bin/osnotify-install-service" "osnotify-proxy" "$(id -un)"
}

function osnotify_develop
{
    compile_install_zmq "$1"
    osnotify_setup_venv "$1"
    python setup.py develop
}

function osnotify_ci
{
    install_dependencies
    osnotify_install "$HOME/osnotify"
}


if [ "$1" == "develop" ]
then
    osnotify_develop "$(readlink -f $2)"
fi

if [ "$1" == "ci" ]
then
    osnotify_ci "$HOME/osnotify"
fi

if [ "$1" == "install" ]
then
    osnotify_install "$(readlink -f $2)"
fi
