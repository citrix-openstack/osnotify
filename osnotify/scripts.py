import zmq
import sys
import argparse
import textwrap
from osnotify import gerrit
import urllib2
import json
import urllib
import datetime


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


def parse_args(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        '--host', dest='host', default='localhost',
        help='The host to connect to')
    parser.add_argument(
        '--topic', dest='topic', default='',
        help='The topic to subscribe to')
    return parser.parse_args()


def publish():
    args = parse_args("Publish lines of standard input")

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
    args = parse_args("Publish lines of standard input")

    context = zmq.Context()

    socket = context.socket(zmq.SUB)
    socket.connect("tcp://%s:6544" % args.host)
    socket.setsockopt(zmq.SUBSCRIBE, args.topic)

    while True:
        sys.stdout.write(socket.recv())
        sys.stdout.flush()

    socket.close()
    context.term()


def create_init_script_for(executable, user, pidfile, arguments=""):
    return textwrap.dedent("""#!/bin/sh
    [ "$(id -u)" != "0" ] && {
        echo "This script must be ran as root" >&2
        exit 1
    }
    case $1 in
    start)
        su %(user)s -s /bin/sh -c \\
        "nohup %(executable)s %(arguments)s> /dev/null 2>&1 < /dev/null & echo \$!" \\
        > %(pidfile)s
        exit 0
        ;;
    stop)
        su %(user)s -s /bin/sh -c "kill `cat %(pidfile)s`" && rm -f %(pidfile)s
        exit 0
        ;;
    esac
    exit 1
    """) % dict(executable=executable, user=user, pidfile=pidfile, arguments=arguments)


def get_full_path_for_script(scriptname):
    import sys
    import os.path

    return os.path.join(os.path.dirname(sys.executable), scriptname)


def install_service():
    import subprocess

    parser = argparse.ArgumentParser(description='install a service')
    parser.add_argument(
        'script', help='The script that you want to have as a service')
    parser.add_argument(
        'user', help='The service account which will run the service')

    args = parser.parse_args()

    initscript_path = '/etc/init.d/' + args.script
    scriptpath = get_full_path_for_script(args.script)

    with open(initscript_path, 'wb') as initscript:
        initscript.write(create_init_script_for(
            scriptpath, args.user, '/var/run/' + args.script))
        initscript.close()

    subprocess.call(['chmod', '+x', initscript_path])
    subprocess.call(['update-rc.d', args.script, 'defaults'])


def gerrit_to_githook():
    parser = argparse.ArgumentParser(
        description='Post github webhook notifications')
    parser.add_argument('url', help='The url to receive the post hooks')
    parser.add_argument(
        'projectlist',
        help='A file with the list of projects e.g.:openstack/nova')
    parser.add_argument(
        '--host', dest='host', default='localhost',
        help='The host to connect to')
    parser.add_argument(
        '--topic', dest='topic', default='',
        help='The topic to subscribe to')
    parser.add_argument(
        '--logfile', dest='logfile',
        help='Logfile to use')
    args = parser.parse_args()

    with open(args.projectlist, 'rb') as listfile:
        projects = listfile.read()

    if args.logfile:
        def log(msg):
            logline = str(datetime.datetime.now()) + " " + msg + '\n'

            if args.logfile == '-':
                sys.stdout.write(logline)
            else:
                with open(args.logfile, 'a') as logfile:
                    logfile.write(logline)
    else:
        def log(msg):
            pass

    context = zmq.Context()

    socket = context.socket(zmq.SUB)
    socket.connect("tcp://%s:6544" % args.host)
    socket.setsockopt(zmq.SUBSCRIBE, args.topic)

    while True:
        line = socket.recv()[len(args.topic):].strip()
        msg = gerrit.GerritMessage(line)
        if msg.is_merge and msg.branch == "master" and msg.project in projects:
            payload = json.dumps(gerrit.to_hook_payload(msg))
            urllib2.urlopen(args.url, urllib.urlencode(dict(payload=payload)))
            log("notified " + msg.project + ":" + line)
        else:
            log("skipped:" + line)

    socket.close()
    context.term()


def generate_initscript():
    import os

    parser = argparse.ArgumentParser(description='Generate an initscript')
    parser.add_argument(
        'script', help='Path to the executable you want to daemonize')
    parser.add_argument(
        '--arguments', help='Arguments for the executable', default="")
    parser.add_argument(
        'user', help='The service account which will run the service')

    args = parser.parse_args()

    print create_init_script_for(args.script, args.user, os.path.join(
        "/", "var", "run", os.path.basename(args.script) + ".pid"),
        args.arguments
        )
