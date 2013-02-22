import zmq
import sys
import argparse

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
    args = parser.parse()

    context = zmq.Context()

    socket = context.socket(zmq.PUB)
    socket.connect("tcp://%s:6543" % args.host)

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        socket.send(line, zmq.DONTWAIT)

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
