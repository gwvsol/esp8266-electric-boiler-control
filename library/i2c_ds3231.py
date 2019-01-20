import machine
try:
    import utime as time
except:
    import time
import uasyncio as asyncio
import gc
from timezone import TZONE

class DS3231(object):

    def __init__(self, i2c, i2c_addr, zone=0, win=True, source_time='local'):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.timebuf = bytearray(7)
        self.zone = zone
        self.win = win
        self.stime = source_time
        self.tzone = TZONE(self.zone)
        self.rtc = False
        if self.i2c_addr in self.i2c.scan():
            print('RTS DS3231 find at address: 0x%x ' %(self.i2c_addr))
        else:
            print('RTS DS3231 not found at address: 0x%x ' %(self.i2c_addr))
        gc.collect()

        loop = asyncio.get_event_loop()
        loop.create_task(self._update_time())


    def _bcd2dec(self, bcd):
        return (((bcd & 0xf0) >> 4) * 10 + (bcd & 0x0f))


    def _dec2bcd(self, dec):
        tens, units = divmod(dec, 10)
        return (tens << 4) + units


    def _tobytes(self, num):
        return num.to_bytes(1, 'little')
    

    def rtctime(self):
        self.i2c.readfrom_mem_into(self.i2c_addr, 0, self.timebuf)
        return self._convert()


    def _convert(self):
        data = self.timebuf
        ss = self._bcd2dec(data[0])
        mm = self._bcd2dec(data[1])
        if data[2] & 0x40:
            hh = self._bcd2dec(data[2] & 0x1f)
            if data[2] & 0x20:
               hh += 12
        else:
            hh = self._bcd2dec(data[2])
        wday = data[3]
        DD = self._bcd2dec(data[4])
        MM = self._bcd2dec(data[5] & 0x1f)
        YY = self._bcd2dec(data[6])
        if data[5] & 0x80:
            YY += 2000
        else:
            YY += 1900
        
        result = YY, MM, DD, hh, mm, ss, wday -1, 0 
        return result


    def save_time(self, default=False):
        if  self.stime == 'local' and not default:
            (YY, MM, mday, hh, mm, ss, wday, yday) = time.localtime()
        elif not default:
            if self.stime == 'ntp' and not self.rtc:
                utc = time.localtime(self.tzone.getntp())
                z = self.tzone.adj_tzone(utc) if self.win else 0
            elif self.rtc:
                utc = self.rtctime()
                z = 1 if utc[1] == 3 else -1
            (YY, MM, mday, hh, mm, ss, wday, yday) =  utc[0:3] + (utc[3]+z,) + utc[4:7] + (utc[7],)
        else:
            (YY, MM, mday, hh, mm, ss, wday, yday) = (2000, 1, 1, 0, 0, 0, 0, 0)
        
        self.i2c.writeto_mem(self.i2c_addr, 0, self._tobytes(self._dec2bcd(ss)))
        self.i2c.writeto_mem(self.i2c_addr, 1, self._tobytes(self._dec2bcd(mm)))
        self.i2c.writeto_mem(self.i2c_addr, 2, self._tobytes(self._dec2bcd(hh)))  
        self.i2c.writeto_mem(self.i2c_addr, 3, self._tobytes(self._dec2bcd(wday + 1)))  
        self.i2c.writeto_mem(self.i2c_addr, 4, self._tobytes(self._dec2bcd(mday)))  
        if YY >= 2000:
            self.i2c.writeto_mem(self.i2c_addr, 5, self._tobytes(self._dec2bcd(MM) | 0b10000000))
            self.i2c.writeto_mem(self.i2c_addr, 6, self._tobytes(self._dec2bcd(YY-2000)))
        else:
            self.i2c.writeto_mem(self.i2c_addr, 5, self._tobytes(self._dec2bcd(MM)))
            self.i2c.writeto_mem(self.i2c_addr, 6, self._tobytes(self._dec2bcd(YY-1900)))
        print('New RTC Time: ', self.rtctime())
        
        
    async def _update_time(self):
        while True:
            rtc = self.rtctime()
            if rtc[0] <= 2000:
                if self.tzone.getntp() > 0:
                    self.save_time()
                    await asyncio.sleep(10)
            if rtc[1] == 3 or rtc[1] == 10:
                rtc = self.rtctime()
                if rtc[3] == 3 and self.tzone.sunday(rtc[0], rtc[1]) == rtc[2]:
                    self.rtc = True
                    self.save_time()
                    self.rtc = False
                    if rtc[1] == 3:
                        await asyncio.sleep(60)
                    else:
                        await asyncio.sleep(3660)
            await asyncio.sleep(1)


    # Wait until DS3231 seconds value changes before reading and returning data
    def await_transition(self):
        self.i2c.readfrom_mem_into(self.i2c_addr, 0, self.timebuf)
        ss = self.timebuf[0]
        while ss == self.timebuf[0]:
            self.i2c.readfrom_mem_into(self.i2c_addr, 0, self.timebuf)
        return self.timebuf
        

    # Test hardware RTC against DS3231. Default runtime 10 min. Return amount
    # by which DS3231 clock leads RTC in PPM or seconds per year.
    # Precision is achieved by starting and ending the measurement on DS3231
    # one-seond boundaries and using ticks_ms() to time the RTC.
    # For a 10 minute measurement +-1ms corresponds to 1.7ppm or 53s/yr. Longer
    # runtimes improve this, but the DS3231 is "only" good for +-2ppm over 0-40C.
    def rtc_test(self, runtime=600, ppm=False):
        factor = 1000000 if ppm else 31557600  # seconds per year
        self.await_transition()  # Start on transition
        rtc_start = time.ticks_ms()  # and get RTC time NOW
        ds3231_start = time.mktime(self._convert())
        time.sleep(runtime)  # Wait a while (precision doesn't matter)
        self.await_transition()
        d_rtc = time.ticks_diff(time.ticks_ms(), rtc_start)
        d_ds3231 = 1000 * (time.mktime(self._convert()) - ds3231_start)
        return (d_ds3231 - d_rtc) * factor / d_ds3231
