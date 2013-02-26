import zmq
import sys
import argparse
import textwrap


def proxy():
    context = zmq.Context()

    frontend = context.socket(zmq.XSUB)
    frontend.bind("tcp://*:6543")

    backend = context.socket(zmq.XPUB)
    backend.bind("tcp://*:6544")

    zmq.device(zmq.QUEUE, frontend, backend)

    frontend.close()
    backend.close()
    context.term()


class Parser(object):
    def __init__(self, description):
        self.parser = argparse.ArgumentParser(description=description)

    def add_host(self):
        self.parser.add_argument(
            '--host', dest='host', default='localhost',
            help='The host to connect to')

    def add_topic(self):
        self.parser.add_argument(
            '--topic', dest='topic', default='',
            help='The topic to subscribe to')

    def parse(self):
        return self.parser.parse_args()


def publish():
    parser = Parser("Publish lines of standard input")
    parser.add_host()
    parser.add_topic()
    args = parser.parse()

    context = zmq.Context()

    socket = context.socket(zmq.PUB)
    socket.connect("tcp://%s:6543" % args.host)

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        socket.send(args.topic + line, zmq.DONTWAIT)

    socket.close()
    context.term()


def subscribe():
    parser = Parser("Publish lines of standard input")
    parser.add_host()
    parser.add_topic()
    args = parser.parse()

    context = zmq.Context()

    socket = context.socket(zmq.SUB)
    socket.connect("tcp://%s:6544" % args.host)
    socket.setsockopt(zmq.SUBSCRIBE, args.topic)

    while True:
        sys.stdout.write(socket.recv())
        sys.stdout.flush()


def create_init_script_for(executable, user, pidfile):
    return textwrap.dedent("""#!/bin/sh
    [ "$(id -u)" != "0" ] && {
        echo "This script must be ran as root" >&2
        exit 1
    }
    case $1 in
    start)
        su %(user)s -s /bin/sh -c "nohup %(executable)s > /dev/null 2>&1 < /dev/null & echo \$!" > %(pidfile)s
        exit 0
        ;;
    stop)
        su %(user)s -s /bin/sh -c "kill `cat %(pidfile)s`" && rm -f %(pidfile)s
        exit 0
        ;;
    esac
    exit 1
    """) % dict(executable=executable, user=user, pidfile=pidfile)


def get_full_path_for_script(scriptname):
    import sys
    import os.path

    return os.path.join(os.path.dirname(sys.executable), scriptname)


def install_service():
    import subprocess

    parser = argparse.ArgumentParser(description='install a service')
    parser.add_argument('script', help='The script that you want to have as a service')
    parser.add_argument('user', help='The service account which will run the service')

    args = parser.parse_args()

    initscript_path = '/etc/init.d/' + args.script
    scriptpath = get_full_path_for_script(args.script)

    with open(initscript_path, 'wb') as initscript:
        initscript.write(create_init_script_for(
            scriptpath, args.user, '/var/run/' + args.script))
        initscript.close()

    subprocess.call(['chmod', '+x', initscript_path])
    subprocess.call(['update-rc.d', args.script, 'defaults'])
