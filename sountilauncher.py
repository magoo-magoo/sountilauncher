# Receive UDP packets transmitted by a broadcasting service
import getpass
import time
# noinspection PyUnresolvedReferences
import sys
from socket import *
import threading

import subprocess

buffer_size = 1500
udp_port = 50000
tcp_port = 8989

admin_name = 'admin'
terminal_name = 'terminal'

start = 'start'
stop = 'stop'
test = 'test'

exit_msg = '\n\nquitting...'

not_running = 'NOT RUNNING'
running = 'RUNNING'

#
terminal_map = dict()


class TerminalInfo:
    def __init__(self, _id, _ip, _status):
        self.id = _id
        self.ip = _ip
        self.status = _status


class Terminal:
    def __init__(self, _id):
        self.id = _id
        self.connected = False

    def terminal(self):
        t = threading.Thread(target=self.terminal_broadcast)
        t.setDaemon(True)
        t.start()

        s = socket(AF_INET, SOCK_STREAM)
        s.bind(('', tcp_port))
        s.listen(1)
        try:
            conn, (remote_host, remote_port) = s.accept()
            print('connected by', remote_host, remote_port)
            self.connected = True
            while 1:
                data = conn.recv(buffer_size)
                if data:
                    data = str(data)
                    if data == stop:
                        print stop
                    elif data == test:
                        print test
                    else:
                        parts = data.split(':')
                        if len(parts) == 3 and parts[0] == start:
                            print 'start'
                            username = parts[1]
                            password = parts[2]
                            print(username, password)
                            proc = subprocess.Popen("/usr/bin/echo user: " + username + " pass: " + password)
                            print "PID:", proc.pid
                        time.sleep(3)
        except KeyboardInterrupt:
            print exit_msg
            sys.exit(0)
        finally:
            s.close()

    def terminal_broadcast(self):
        s = socket(AF_INET, SOCK_DGRAM)
        s.bind(('', 0))
        s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        try:
            while 1:
                if not self.connected:
                    data = self.id
                    s.sendto(data, ('<broadcast>', udp_port))
                time.sleep(2)
        except KeyboardInterrupt:
            print exit_msg
            sys.exit(0)


class Admin:
    def __init__(self):
        pass


def admin_start(address):
    username = raw_input('terminal username: ')
    password = getpass.getpass()

    # Create a TCP/IP socket
    sock = socket(AF_INET, SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    server_address = (address, tcp_port)
    print >> sys.stderr, 'connecting to %s port %s' % server_address
    sock.connect(server_address)
    try:

        # Send data
        message = username + ':' + password
        print >> sys.stderr, 'sending "%s"' % message
        sock.sendall(message)

        # # Look for the response
        # amount_received = 0
        # amount_expected = len(message)
        #
        # while amount_received < amount_expected:
        #     data = sock.recv(16)
        #     amount_received += len(data)
        #     print >>sys.stderr, 'received "%s"' % data

    finally:
        print >> sys.stderr, 'closing socket'
        sock.close()


def admin_stop():
    pass


def admin_test():
    pass


def admin_get_mode():
    while True:
        mode = raw_input(start + '/' + stop + '/' + test + ': ')
        if mode == start or mode == stop or mode == test:
            return mode


def admin_listen():
    while 1:
        s = socket(AF_INET, SOCK_DGRAM)
        s.bind(('', udp_port))
        data, wherefrom = s.recvfrom(buffer_size, 0)
        s.close()
        terminal_ip_address = wherefrom[0]
        print 'terminal ID : ', data
        print 'Connecting to : ', terminal_ip_address
        time.sleep(0.5)


def admin():
    t = threading.Thread(target=admin_listen)
    t.setDaemon(True)
    t.start()
    try:
        while 1:
            mode, term_id = admin_get_mode()
            if mode == start:
                admin_start(term_id)
            elif mode == stop:
                admin_stop()
            elif mode == test:
                admin_test()
    except KeyboardInterrupt:
        print exit_msg


def usage():
    sys.stdout = sys.stderr
    print 'Usage: ', sys.argv[0], ' ', admin_name
    print 'or ', sys.argv[0], ' ', terminal_name, ' id'


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        if sys.argv[1] == admin_name:
            admin()
        elif len(sys.argv) == 3 and sys.argv[1] == terminal_name:
            term = Terminal(sys.argv[2])
            term.terminal()
        else:
            usage()
    else:
        usage()
