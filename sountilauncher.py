# Receive UDP packets transmitted by a broadcasting service
import getpass
import shlex
import time
# noinspection PyUnresolvedReferences
import sys
from socket import *
import threading
import subprocess

buffer_size = 1500
udp_port = 56921
tcp_port = 8989

admin_name = 'admin'
terminal_name = 'terminal'

start = 'start'
stop = 'stop'
test = 'test'

exit_msg = '\n\nquitting...'

not_running = 'NOT RUNNING'
running = 'RUNNING'


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
                            proc = subprocess.Popen(shlex.split("/bin/echo \"user: " + username + " pass: " + password + "\""))
                            print "PID:", proc.pid
                time.sleep(0.5)
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
                data = self.id
                s.sendto(data, ('<broadcast>', udp_port))
                print 'broadcast: ' + data, ' sent.'
                time.sleep(10)
        except KeyboardInterrupt:
            print exit_msg
            sys.exit(0)


class Admin:
    def __init__(self):
        self.terminal_map = dict()

    def admin_start(self, term_id):
        username = raw_input('terminal username: ')
        password = getpass.getpass()

        try:
            term = self.terminal_map[term_id]
        except KeyError:
            print term_id, ' not found'
            return
        # Create a TCP/IP socket
        sock = socket(AF_INET, SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = (term.ip, tcp_port)
        print >> sys.stderr, 'connecting to %s port %s' % server_address
        sock.connect(server_address)
        try:

            # Send data
            message = start + ':' + username + ':' + password
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

    def admin_stop(self):
        pass

    def admin_test(self):
        pass

    def admin_get_mode(self):
        while True:
            mode = str(raw_input(start + '/' + stop + '/' + test + ': '))
            if len(mode.split(':')) == 2:
                term_id = mode.split(':')[1]
                mode = mode.split(':')[0]
                if mode == start or mode == stop or mode == test:
                    return mode, term_id

    def admin_listen(self):
        s = socket(AF_INET, SOCK_DGRAM)
        s.bind(('', udp_port))

        while 1:
            data, wherefrom = s.recvfrom(buffer_size, 0)
            terminal_ip_address = wherefrom[0]
            print 'terminal ID : ', data, ' - ip  : ', terminal_ip_address
            term_info = TerminalInfo(data, terminal_ip_address, not_running)
            self.terminal_map[data] = term_info
            time.sleep(0.5)

    def admin(self):
        t = threading.Thread(target=self.admin_listen)
        t.setDaemon(True)
        t.start()
        try:
            while 1:
                mode, term_id = self.admin_get_mode()
                if mode == start:
                    self.admin_start(term_id)
                elif mode == stop:
                    self.admin_stop()
                elif mode == test:
                    self.admin_test()
                time.sleep(1)
        except KeyboardInterrupt:
            print exit_msg


def usage():
    sys.stdout = sys.stderr
    print 'Usage: ', sys.argv[0], ' ', admin_name
    print 'or ', sys.argv[0], ' ', terminal_name, ' id'


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        if sys.argv[1] == admin_name:
            adm = Admin()
            adm.admin()
        elif len(sys.argv) == 3 and sys.argv[1] == terminal_name:
            term = Terminal(sys.argv[2])
            term.terminal()
        else:
            usage()
    else:
        usage()
