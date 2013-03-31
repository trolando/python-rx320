"""
rx320 tcp/ip server
:copyright: (c) 2013 by Tom van Dijk
:license: BSD, see LICENSE for more details.
"""
from rx320 import RX320
import socket
import threading

class RX320Connection(threading.Thread):
    def __init__(self, connection, controller, *args, **kwargs):
        super(RX320Connection,self).__init__(*args, **kwargs)
        self.connection = connection
        self.controller = controller
        self.daemon = True
        self.start()

    def linesplit(self):
        socket = self.connection
        buffer = socket.recv(4096)
        done = False
        while not done:
            if "\n" in buffer:
                (line, buffer) = buffer.split("\n", 1)
                yield line.strip()
            else:
                more = socket.recv(4096)
                if not more:
                    done = True
                else:
                    buffer = buffer+more
        if buffer:
            yield buffer.strip()

    def run(self):
        try:
            for line in self.linesplit():
                result = self.handle(line.split())
                self.connection.sendall("%s\n" % result)
        finally:
            self.connection.close()

    def handle(self, command):
        if len(command) == 0:
            return "ERROR" 
        if command[0] == 'ALL' and len(command) == 4:
            # ALL <freq> <mode> <filter>
            self.controller.set_mode(int(command[2]))
            self.controller.set_filter(int(command[3]))
            self.controller.set_freq(int(command[1]))
            return "Done"
        elif command[0] == 'FREQ' and len(command) == 2:
            self.controller.set_freq(int(command[1]))
            return "Done"
        elif command[0] == 'VOL' and len(command) == 2:
            self.controller.set_speaker_volume(int(command[1]))
            return "Done"
        elif command[0] == 'LINEVOL' and len(command) == 2:
            self.controller.set_line_volume(int(command[1]))
            return "Done"
        elif command[0] == 'MODE' and len(command) == 2:
            self.controller.set_mode(int(command[1]))
            return "Done"
        elif command[0] == 'FILTER' and len(command) == 2:
            self.controller.set_filter(int(command[1]))
            return "Done"
        elif command[0] == 'AGC' and len(command) == 2:
            self.controller.set_agc(int(command[1]))
            return "Done"
        elif command[0] == 'GETMODE':
            if hasattr(self.controller, 'mode'):
                return str(self.controller.mode)
            else:
                return 'NA'
        elif command[0] == 'GETFILTER':
            if hasattr(self.controller, 'filter'):
                return str(self.controller.filter)
            else:
                return 'NA'
        elif command[0] == 'GETAGC':
            if hasattr(self.controller, 'agc'):
                return str(self.controller.agc)
            else:
                return 'NA'
        elif command[0] == 'GETSMETER':
            return str(self.controller.strength) 
        elif command[0] == 'GETVOL':
            if hasattr(self.controller, 'speaker_volume'):
                return str(self.controller.speaker_volume)
            else:
                return 'NA'
        elif command[0] == 'GETLINEVOL':
            if hasattr(self.controller, 'line_volume'):
                return str(self.controller.line_volume)
            else:
                return 'NA'
        elif command[0] == 'GETFREQ':
            if hasattr(self.controller, 'freq'):
                return str(self.controller.freq)
            else:
                return 'NA'
        return "ERROR"

if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser(
        usage = "%prog [options] device",
        description = "RX320 controller"
    )
    parser.add_option("-p", "--port",
        dest = "local_port",
        action = "store",
        type = "int",
        help = "TCP/IP port",
        default = 4665
    )
    parser.add_option("-s", "--sleep",
        dest = "sleep_time",
        action = "store",
        type = "float",
        help = "Seconds to wait between strength polls",
        default = 0.2
    )
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error('need device as argument, e.g. /dev/tty...')

    controller = RX320(args[0], options.sleep_time)
    # initialize controller
    controller.set_volume(99)
    controller.set_mode(RX320.MODE_LSB)
    controller.set_agc(RX320.AGC_MEDIUM)
    controller.set_filter(RX320.FILTERS.index(2100))
    controller.set_freq(3630000)
    controller.set_line_volume(16)
    controller.set_speaker_volume(96)

    print "Initialized RX320 '%s'" % args[0]

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('', options.local_port))
    srv.listen(1)

    print "Waiting for connections on port %d..." % (options.local_port)

    while True:
        try:
            connection, addr = srv.accept()
            connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            c = RX320Connection(connection, controller)
        except KeyboardInterrupt:
            break
        except socket.error, msg:
            pass
