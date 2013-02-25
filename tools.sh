#!/bin/bash

function install_zmq_compile_dependencies
{
(
export DEBIAN_FRONTEND=noninteractive
sudo apt-get install -qy libtool autoconf automake uuid-dev g++ make
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
./configure
make
sudo make install
)
rm -rf "$ZMQ"
}

function install_python_zmq_deps
{
(
export DEBIAN_FRONTEND=noninteractive
sudo apt-get install -qy python-pip python-dev
)
}

function osnotify_setup
{
    sudo pip install -U pyzmq
    sudo python setup.py install
}

function osnotify_setup_venv
{
    [ -e .env ] || virtualenv .env
    . .env/bin/activate
    pip install -U pyzmq
    python setup.py develop
}

function osnotify-install
{
    install_zmq_compile_dependencies
    compile_install_zmq
    install_python_zmq_deps
    osnotify_setup
}

function osnotify-develop
{
    install_zmq_compile_dependencies
    compile_install_zmq
    install_python_zmq_deps
    osnotify_setup_venv
}

function osnotify-ci
{
    osnotify-install
    # Tests should come here
}


if [ "$1" == "develop" ]
then
    osnotify-develop
fi

if [ "$1" == "ci" ]
then
    osnotify-ci
fi

if [ "$1" == "install" ]
then
    osnotify-install
fi

