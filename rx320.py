"""
rx320 controller
:copyright: (c) 2013 by Tom van Dijk
:license: BSD, see LICENSE for more details.
"""
import serial
import threading
import time

class RX320():
    MODE_AM = 0
    MODE_USB = 1
    MODE_LSB = 2
    MODE_CW = 3

    AGC_SLOW = 1
    AGC_MEDIUM = 2
    AGC_FAST = 3

    FILTERS = [
        6000, 5700, 5400, 5100, 4800, 4500, 4200,
        3900, 3600, 3300, 3000, 2850, 2700, 2550,
        2400, 2250, 2100, 1950, 1800, 1650, 1500,
        1350, 1200, 1050, 900, 750, 675, 600,
        525, 450, 375, 330, 300, 8000,]

    def __init__(self, port, sleep_time=0.2):
        self.ser = serial.Serial(port, 1200, timeout=1)
        self.strength = 0
        self.firmware = ''
        thr = threading.Thread(target=RX320.read_thread, args=[self])
        thr.daemon = True
        thr.start()
        thr = threading.Thread(target=RX320.strength_thread, 
                               args=[self, sleep_time])
        thr.daemon = True
        thr.start()

    def read_thread(self):
        buf = []
        while True:
            ch = self.ser.read(1)
            if len(ch) == 1:
                ch = ord(ch)
                if ch == 10:
                    pass # ignore
                elif ch == 13:
                    if len(buf) > 0: 
                        self.handle_response(buf)
                    buf = []
                else:
                    buf.append(ch)

    def strength_thread(self, sleep_time):
        while True:
            self.send_get_strength()
            time.sleep(sleep_time)

    def handle_response(self, buf):
        if buf[0] == ord('\x58'):
            if len(buf) >= 3:
                self.strength = buf[1] * 256 + buf[2]
            else:
                pass # invalid strength response! (ignore)
        elif buf[0] == ord('\x5a'):
            pass # unrecognized command! (ignore)
        elif len(buf) > 3 and str(bytearray(buf[:3])) == 'VER':
            self.firmware = str(bytearray(buf))
        elif len(buf) > 3 and str(bytearray(buf[:3])) == 'DSP':
            pass # power on! (ignore)
        else:
            pass # unknown response! (ignore)

    def set_freq(self, freq, cwbfo=0):
        assert hasattr(self, 'mode')
        assert hasattr(self, 'filter')

        if self.mode != RX320.MODE_CW: 
            cwbfo = 0

        mcor = [0, 1, -1, -1][self.mode]
        fcor = RX320.FILTERS[self.filter]/2+200

        adjusted_freq = freq - 1250 + mcor*(fcor+cwbfo)

        coarse = int(18000 + (adjusted_freq // 2500))
        fine = int(5.46 * (adjusted_freq % 2500))
        bfo = int(2.73 * (fcor+cwbfo+8000))
        self.set_tuning(coarse, fine, bfo)

        self.freq = freq
        self.cwbfo = cwbfo

    def set_tuning(self, coarse, fine, bfo):
        assert coarse >= 0 and coarse < 65536
        assert fine >= 0 and fine < 65536
        assert bfo >= 0 and bfo < 65536
        
        self.ser.write(b'\x4e%c%c%c%c%c%c\x0d' % 
                ((coarse>>8)&255, coarse&255, 
                (fine>>8)&255, fine&255, 
                (bfo>>8)&255, bfo&255))
        
        self.coarse = coarse
        self.fine = fine
        self.bfo = bfo

    def set_agc(self, agc):
        if agc >= 0 and agc <= 3:
            self.ser.write(b'\x47%d\x0d' % agc)
            self.agc = agc

    def set_mode(self, mode):
        if mode >= 0 and mode <= 4:
            self.ser.write(b'\x4d%d\x0d' % mode)
            self.mode = mode

    def set_filter(self, filter):
        if filter >= 0 and filter <= 33:
            self.ser.write(b'\x57%c\x0d' % filter)
            self.filter = filter

    def set_line_volume(self, vol):
        if vol < 0: vol = 0
        if vol > 63: vol = 63
        self.ser.write(b'\x41\x00%c\x0d' % vol)
        self.line_volume = vol

    def set_speaker_volume(self, vol):
        if vol < 0: vol = 0
        if vol > 63: vol = 63
        self.ser.write(b'\x56\x00%c\x0d' % vol)
        self.speaker_volume = vol
 
    def set_volume(self, vol):
        if vol < 0: vol = 0
        if vol > 63: vol = 63
        self.ser.write(b'\x43\x00%c\x0d' % vol)
        self.line_volume = vol
        self.speaker_volume = vol

    def send_get_firmware(self):
        self.firmware = ''
        self.ser.write(b'\x3f\x0d')
        
    def send_get_strength(self):
        self.ser.write(b'\x58\x0d')
