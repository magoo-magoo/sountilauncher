# Receive UDP packets transmitted by a broadcasting service
import getpass
import shlex
import time
# noinspection PyUnresolvedReferences
import sys
from pprint import pprint
from signal import SIGINT
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
help_cmd = 'help'
list_cmd = 'list'

exit_msg = '\n\nquitting...'

not_running = 'NOT_RUNNING'
running = 'RUNNING'


################################################################################
# Terminal stuff
################################################################################

class Terminal:
    def __init__(self, _id):
        self.id = _id
        self.process = None
        self.status = not_running

    def terminal(self):
        t = threading.Thread(target=self.terminal_broadcast)
        t.setDaemon(True)
        t.start()

        s = socket(AF_INET, SOCK_STREAM)
        s.bind(('', tcp_port))
        s.listen(1)
        try:
            conn = self.accept(s, None)
            while 1:
                if conn.send("X") <= 0:
                    print 'send failed'
                try:
                    data = conn.recv(buffer_size)
                except socket.error:
                    conn = self.accept(s, None)
                    continue
                if data:
                    data = str(data)
                    print data, 'received.'
                    if data == stop and self.process is not None:
                        self.stop()
                    elif data == test:
                        print test
                    else:
                        parts = data.split(':')
                        if len(parts) == 3 and parts[0] == start:
                            self.start(parts[1], parts[2])
                time.sleep(0.5)
        except KeyboardInterrupt:
            print exit_msg
            sys.exit(0)
        finally:
            self.stop()
            s.close()

    def accept(self, sock, old_conn):
        if old_conn is None:
            conn, (remote_host, remote_port) = sock.accept()
            print('connected by', remote_host, remote_port)
            return conn

    def stop(self):
        if self.process:
            self.process.send_signal(SIGINT)
            self.process.terminate()
            self.process = None

    def start(self, username, password):
        """

        :type password: str
        :type username: str
        """
        print 'start'
        print(username, password)
        cmd = "/usr/bin/python ./yes.py \"user: {0} pass: {1}\"".format(username, password)
        self.process = subprocess.Popen(shlex.split(cmd))
        print "PID:", self.process.pid

    def terminal_broadcast(self):
        s = socket(AF_INET, SOCK_DGRAM)
        s.bind(('', 0))
        s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        try:
            while 1:
                if self.process is not None and self.process.poll() is None:
                    self.status = running
                else:
                    self.status = not_running
                data = self.id + ':' + self.status
                s.sendto(data, ('<broadcast>', udp_port))
                # print 'broadcast: ' + data, ' sent.'
                time.sleep(1)
        except KeyboardInterrupt:
            print exit_msg
            sys.exit(0)


################################################################################
# Admin stuff
################################################################################


class Admin:
    def __init__(self):
        self.terminal_map = dict()

    def send(self, terminal_info, message):

        """

        :type terminal_info: TerminalInfo
        :type message: str
        :rtype: None
        """
        if terminal_info.sock is None:
            # Create a TCP/IP socket
            terminal_info.sock = socket(AF_INET, SOCK_STREAM)
            # Connect the socket to the port where the server is listening
            server_address = (terminal_info.ip, tcp_port)
            print >> sys.stderr, 'connecting to %s port %s' % server_address
            terminal_info.sock.connect(server_address)

        # Send data
        try:
            print >> sys.stderr, 'sending "%s"' % message
            terminal_info.sock.sendall(message)
        except socket.error:
            print >> sys.stderr, 'sending error'
            terminal_info.sock.close()
            terminal_info.sock = None

    def admin_start(self, terminal_info):
        """

        :type terminal_info: TerminalInfo
        """
        username = raw_input('terminal username: ')
        password = getpass.getpass()
        message = start + ':' + username + ':' + password

        self.send(terminal_info, message)

    def admin_stop(self, terminal_info):
        """

        :type terminal_info: TerminalInfo
        """
        self.send(terminal_info, stop)

    def admin_test(self, terminal_info):
        """

        :type terminal_info: TerminalInfo
        """
        pass

    def admin_get_mode(self):
        """

        :rtype: tuple
        """
        while True:
            mode = str(raw_input(start + '/' + stop + '/' + test + '/' + list_cmd + ': '))
            if mode == help_cmd:
                self.show_help()
                continue
            if mode == list_cmd:
                return mode, None
            if len(mode.split(':')) == 2:
                term_id = mode.split(':')[1]
                mode = mode.split(':')[0]
                if mode == start or mode == stop or mode == test:
                    return mode, term_id

    @staticmethod
    def show_help():
        print '\tcmd:ID\n ex : \n start:42'

    def admin_listen(self):
        s = socket(AF_INET, SOCK_DGRAM)
        s.bind(('', udp_port))

        while 1:
            data, wherefrom = s.recvfrom(buffer_size, 0)
            terminal_id = data.split(':')[0]
            terminal_status = data.split(':')[1]
            terminal_ip = wherefrom[0]
            term_info = TerminalInfo(terminal_id, terminal_ip, terminal_status)
            if self.terminal_map.has_key(terminal_id):
                self.terminal_map[terminal_id].id = terminal_id
                self.terminal_map[terminal_id].ip = terminal_ip
                self.terminal_map[terminal_id].status = terminal_status
            else:
                self.terminal_map[terminal_id] = term_info

    def admin(self):
        t = threading.Thread(target=self.admin_listen)
        t.setDaemon(True)
        t.start()
        try:
            while 1:
                mode, term_id = self.admin_get_mode()
                if mode != list_cmd:
                    try:
                        terminal_info = self.terminal_map[term_id]
                    except KeyError:
                        print term_id, ' not found'
                        continue
                if mode == list_cmd:
                    pprint(self.terminal_map)
                if mode == start:
                    self.admin_start(terminal_info)
                elif mode == stop:
                    self.admin_stop(terminal_info)
                elif mode == test:
                    self.admin_test(terminal_info)
        except KeyboardInterrupt:
            print exit_msg


class TerminalInfo:
    def __init__(self, _id, _ip, _status):
        """

        :type _status: str
        :type _ip: str
        :type _id: str
        """
        self.id = _id
        self.ip = _ip
        self.status = _status
        self.sock = None

    def __repr__(self):
        return "(" + str(self.ip) + ", " + str(self.status) + ")"


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
