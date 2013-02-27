import unittest
import tempfile
import contextlib
from osnotify import scripts
import subprocess
import stat
import os
import datetime
import time
import getpass


def tempscript(contents):
    return tempexecutable("#!/bin/bash\n" + contents)


@contextlib.contextmanager
def tempexecutable(contents):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(contents)
        f.close()
        subprocess.call(['chmod', '+x', f.name])
        yield f.name

    os.unlink(f.name)


@contextlib.contextmanager
def tmpf():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.close()
        yield f.name

    try:
        os.unlink(f.name)
    except:
        pass


def create_init_script_for(daemon, **kwargs):
    with tmpf() as pidfile:
        args = dict(pidfile=pidfile)
        args.update(**kwargs)
        return scripts.create_init_script_for(
            daemon, getpass.getuser(), **args)


class TestTempScript(unittest.TestCase):
    def test_it_is_executable(self):
        with tempscript("") as ts:
            self.assertEquals(0, subprocess.call([ts]))

    def test_printing_out_something(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            with tempscript('echo "I was executed" > ' + f.name) as srvc:
                result = subprocess.call([srvc])
                self.assertEquals(0, result)


class TestInitScriptCreation(unittest.TestCase):
    def test_error_if_no_parameter_specified(self):
        with tempfile.NamedTemporaryFile() as f:
            with tempscript('echo -n "I was executed" > ' + f.name) as daemon:
                initscript_contents = create_init_script_for(daemon)

                with tempexecutable(initscript_contents) as starter:
                    result = subprocess.call(['sudo', starter])
                    self.assertEquals(1, result)

            self.assertEquals("", open(f.name).read())

    def test_daemon_started(self):
        with tempfile.NamedTemporaryFile() as f:
            with tempscript('echo -n "I was executed" > ' + f.name) as daemon:
                initscript_contents = create_init_script_for(daemon)

                with tempexecutable(initscript_contents) as starter:
                    result = subprocess.call(['sudo', starter, 'start'])
                    self.assertEquals(0, result)
                    time.sleep(0.1)

            self.assertEquals("I was executed", open(f.name).read())

    def test_daemon_is_in_the_background(self):
        with tempscript('sleep 10') as daemon:
            initscript_contents = create_init_script_for(daemon)

            starttime = datetime.datetime.now()

            with tempexecutable(initscript_contents) as starter:
                result = subprocess.call(['sudo', starter, 'start'])
                self.assertEquals(0, result)

            delta = datetime.datetime.now() - starttime
            self.assertTrue(delta.seconds < 10)

    def test_stdout_is_not_visible(self):
        with tempscript('echo "I am the script"') as daemon:
            initscript_contents = create_init_script_for(daemon)

            with tempexecutable(initscript_contents) as starter:
                proc = subprocess.Popen(
                    ['sudo', starter, 'start'], stdout=subprocess.PIPE)
                proc.wait()
                self.assertEquals("", proc.stdout.read())

    def test_stderr_is_not_visible(self):
        with tempscript('echo "I am the script" >&2') as daemon:
            initscript_contents = create_init_script_for(daemon)

            with tempexecutable(initscript_contents) as starter:
                proc = subprocess.Popen(
                    ['sudo', starter, 'start'], stderr=subprocess.PIPE)
                proc.wait()
                self.assertEquals("", proc.stderr.read())

    def test_script_fails_with_non_root(self):
        with tempscript('echo "I am the script" >&2') as daemon:
            initscript_contents = create_init_script_for(daemon)

            with tempexecutable(initscript_contents) as starter:
                proc = subprocess.Popen(
                    [starter, 'start'], stderr=subprocess.PIPE)
                proc.wait()
                self.assertEquals(1, proc.returncode)
                self.assertTrue(
                    "This script must be ran as root" in proc.stderr.read())

    def test_script_runs_as_specified_user(self):
        with tmpf() as somefile:
            with tempscript('id -un > ' + somefile) as daemon:
                initscript_contents = create_init_script_for(daemon)

                with tempexecutable(initscript_contents) as starter:
                    proc = subprocess.Popen(['sudo', starter, 'start'])
                    proc.wait()
                    time.sleep(0.1)

            self.assertEquals(getpass.getuser(), open(somefile).read().strip())

    def test_daemon_is_stopped(self):
        with tmpf() as somefile:
            with tempscript("sleep 10") as daemon:
                initscript_contents = create_init_script_for(
                    daemon, pidfile=somefile)

                with tempexecutable(initscript_contents) as starter:
                    proc = subprocess.Popen(['sudo', starter, 'start'])
                    proc.wait()
                    time.sleep(0.1)

                    pid = open(somefile).read().strip()
                    self.assertTrue(bool(pid))

                    proc = subprocess.Popen(['sudo', starter, 'stop'])
                    proc.wait()
                    time.sleep(0.1)

                    self.assertFalse(os.path.exists(somefile))

    def test_daemon_standard_input(self):
        with tmpf() as somefile:
            with tempscript("cat; echo unblocked >" + somefile) as daemon:
                initscript_contents = create_init_script_for(daemon)

                with tempexecutable(initscript_contents) as starter:
                    proc = subprocess.Popen(['sudo', starter, 'start'])
                    proc.wait()
                    time.sleep(0.1)

                self.assertEquals("unblocked", open(somefile).read().strip())


class TestPathGetting(unittest.TestCase):
    def test_getting_path(self):
        scriptpath = scripts.get_full_path_for_script('osnotify-proxy')
        self.assertTrue(scriptpath)
        self.assertTrue(scriptpath.endswith('osnotify-proxy'))
