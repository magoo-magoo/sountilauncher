# Receive UDP packets transmitted by a broadcasting service
import getpass
import time
# noinspection PyUnresolvedReferences
import sys
from socket import *
from threading import Thread

buffer_size = 1500
udp_port = 50000
tcp_port = 8989

admin_name = 'admin'
terminal_name = 'terminal'

start = 'start'
stop = 'stop'
test = 'test'

hello_msg = 'helloSounTiPunch'
exit_msg = '\n\nquitting...'

not_running = 'NOT RUNNING'
running = 'RUNNING'

terminal_status = not_running
terminal_id = None
terminal_connected = False


class Terminal:
    def __init__(self):
        pass


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
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('', udp_port))
    data, wherefrom = s.recvfrom(buffer_size, 0)
    terminal_ip_address = wherefrom[0]
    print data, ' received. Connecting to : ', terminal_ip_address
    mode = admin_get_mode()
    if mode == start:
        admin_start(terminal_ip_address)
    elif mode == stop:
        admin_stop()
    elif mode == test:
        admin_test()


def admin():
    try:
        while 1:
            admin_listen()
            time.sleep(5)
    except KeyboardInterrupt:
        print exit_msg


def terminal_broadcast():
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('', 0))
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    try:
        while 1:
            if not terminal_connected:
                data = repr(hello_msg)
                s.sendto(data, ('<broadcast>', udp_port))
            time.sleep(2)
    except KeyboardInterrupt:
        print exit_msg
        sys.exit(0)


def terminal():
    global terminal_connected
    thread = Thread(terminal_broadcast())
    thread.setDaemon(True)
    thread.start()

    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.bind(('127.0.0.1', tcp_port))
        s.listen(1)
        conn, (remote_host, remote_port) = s.accept()
        print('connected by', remote_host, remote_port)
        terminal_connected = True
        while 1:
            data = conn.recv(buffer_size)
            if not data:
                break
            conn.send(data)
    except KeyboardInterrupt:
        print exit_msg
        sys.exit(0)


def usage():
    sys.stdout = sys.stderr
    print 'Usage: ', sys.argv[0], ' ', admin_name
    print 'or ', sys.argv[0], ' ', terminal_name, ' id'


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        if sys.argv[1] == admin_name:
            admin()
        elif len(sys.argv) == 3 and sys.argv[1] == terminal_name:
            terminal_id = sys.argv[2]
            terminal()
        else:
            usage()
    else:
        usage()
