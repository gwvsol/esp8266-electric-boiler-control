from micropython import const
import time
import gc
from timezone import TZONE


#Registers overview
_SECONDS = const(0x00)
_MINUTES = const(0x01)
_HOURS = const(0x02) #Bit0-3 - Hour, Bit4 - 10Hour, Bit5 - 20Hour, Bit6 = 12/24
_WDAY = const(0x03)  #Bit0-3
_DATE = const(0x04)  #Bit0-5
_MONTH = const(0x05) #Bit0-4 - Month, Bit7 - Century
_YEAR = const(0x06)


class DS3231(object):

    def __init__(self, i2c, i2c_addr, zone=0, dht=True):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.zone = zone
        self.dht = dht
        self.block = False
        self.rtc = False
        if self.i2c_addr in self.i2c.scan():
            print('RTC: DS3231 find at address: 0x%x ' %(self.i2c_addr))
        else:
            print('RTC: DS3231 not found at address: 0x%x ' %(self.i2c_addr))
        gc.collect()


    #Преобразование двоично-десятичного формата
    def _bcd2dec(self, bcd):
        """Convert binary coded decimal (BCD) format to decimal"""
        return (((bcd & 0xf0) >> 4) * 10 + (bcd & 0x0f))


    #Преобразование в двоично-десятичный формат
    def _dec2bcd(self, dec):
        """Convert decimal to binary coded decimal (BCD) format"""
        tens, units = divmod(dec, 10)
        return (tens << 4) + units


    def _tobytes(self, num):
        return num.to_bytes(1, 'little')


    #Чтение времени или запись нового значения и преобразование в формат ESP8266
    #Возвращает кортеж в формате localtime() (в ESP8266 0 - понедельник, а 6 - воскресенье)
    def datetime(self, datetime=None):
        if datetime == None:
            """Reading RTC time and convert to ESP8266"""
            data = self.i2c.readfrom_mem(self.i2c_addr, _SECONDS, 7)
            ss = self._bcd2dec(data[0])
            mm = self._bcd2dec(data[1])
            if data[2] & 0x40:
                hh = self._bcd2dec(data[2] & 0x1f)
                if data[2] & 0x20:
                   hh += 12
            else:
                hh = self._bcd2dec(data[2])
            wday = data[3]
            mday = self._bcd2dec(data[4])
            MM = self._bcd2dec(data[5] & 0x1f)
            yy = self._bcd2dec(data[6])
            if data[5] & 0x80:
                yy += 2000
            else:
                yy += 1900
            return yy, MM, mday, hh, mm, ss, wday -1, 0
        elif datetime != None:
            """Direct write un-none value"""
            if datetime == 'reset': #Если datetime = 'reset', сброс времени на 2000-01-01 00:00:00
                (yy, MM, mday, hh, mm, ss, wday, yday) = (2000, 1, 1, 0, 0, 0, 0, 0)
            else:
                (yy, MM, mday, hh, mm, ss, wday, yday) = datetime
            if ss < 0 or ss > 59: #Записывем новое значение секунд
                raise ValueError('RTC: Seconds is out of range [0,59].')
            self.i2c.writeto_mem(self.i2c_addr, _SECONDS, self._tobytes(self._dec2bcd(ss)))
            if mm < 0 or mm > 59: #Записываем новое значение минут
                raise ValueError('RTC: Minutes is out of range [0,59].')
            self.i2c.writeto_mem(self.i2c_addr, _MINUTES, self._tobytes(self._dec2bcd(mm)))
            if hh < 0 or hh > 23: #Записываем новое значение часов
                raise ValueError('RTC: Hours is out of range [0,23].')
            self.i2c.writeto_mem(self.i2c_addr, _HOURS, self._tobytes(self._dec2bcd(hh)))  #Sets to 24hr mode
            if mday < 1 or mday > 31: #Записываем новое значение дней
                raise ValueError('RTC: Date is out of range [1,31].')
            self.i2c.writeto_mem(self.i2c_addr, _DATE, self._tobytes(self._dec2bcd(mday)))  #Day of month
            if wday < 0 or wday > 6: #Записываем новое значение дней недели
                raise ValueError('RTC: Day is out of range [0,6].')
            self.i2c.writeto_mem(self.i2c_addr, _WDAY, self._tobytes(self._dec2bcd(wday + 1)))
            if MM < 1 or MM > 12: #Записываем новое значение месяцев
                raise ValueError('RTC: Month is out of range [1,12].')
            self.i2c.writeto_mem(self.i2c_addr, _MONTH, self._tobytes(self._dec2bcd(MM)))
            if yy < 1900 or yy > 2099: #Записываем новое значение лет
                raise ValueError('RTC: Years is out of range [1900,2099].')
            if yy >= 2000:
                self.i2c.writeto_mem(self.i2c_addr, _MONTH, self._tobytes(self._dec2bcd(MM) | 0x80))
                self.i2c.writeto_mem(self.i2c_addr, _YEAR, self._tobytes(self._dec2bcd(yy-2000)))
            else:
                self.i2c.writeto_mem(self.i2c_addr, _MONTH, self._tobytes(self._dec2bcd(MM)))
                self.i2c.writeto_mem(self.i2c_addr, _YEAR, self._tobytes(self._dec2bcd(yy-1900)))
            (yy, MM, mday, hh, mm, ss, wday, yday) = self.datetime() #Cчитываем записанное новое значение времени с DS3231
            print('RTC: New Time: %02d-%02d-%02d %02d:%02d:%02d' %(yy, MM, mday, hh, mm, ss)) #Выводим новое время DS3231


    def settime(self, source='dht'):
        z = 0
        utc = self.datetime()
        tzone = TZONE(self.zone)
        if  source == 'esp': #Устанавливаем время с часов ESP8266
            utc = time.localtime()
        elif source == 'ntp': #Устанавливаем время c NTP сервера
            utc = time.localtime(tzone.getntp()) #Время с NTP без учета летнего или зимнего времени
            z = tzone.adj_tzone(utc) if self.dht else 0 #Корректируем время по временным зонам
        elif source == 'dht' and not self.block: #Только первод времени в DS3231, если нет блокировки
            rtc = self.datetime()
            # Если время 3часа утра и последнее воскресенье месяца
            if rtc[3] == 3 and tzone.sunday(rtc[0], rtc[1]) == rtc[2] and rtc[4] <= 2:
                # Если март
                if rtc[1] == 3:
                    z = 1 if self.dht else 0 #Переводим время вперед
                #Если октябрь
                elif rtc[1] == 10:
                    z = -1 if self.dht else 0 #Переводим время назад
                self.block = True #Устанавливаем блокировку на изменение времени
        rtc = self.datetime() #Cчитываем значение времени с DS3231
        #Блокировка перевода времени. Если октябрь, блокировка на 1час 3минуты
        if self.block and rtc[1] == 10:
            if rtc[3] == 2: #Если 2 часа, блокировка не снимается
                pass
            elif rtc[3] == 3 and rtc[4] <= 2: #Если 3 часа и меньше 2 минут, бликировка не снимается
                pass
            else: #Во всех остальных случаях блокировка снимается
                self.block = False
        #Если март, бликировка включена для следующего вызова метода
        elif self.block and rtc[1] == 3:
            if rtc[3] == 3: #Блокировка действует пока не измениться rtc[3] = 3
                pass
            else: #Во всех остальных случаях блокировка снимается
                self.block = False
        else: #Во всех остальных случаях блокировка снимается
            self.block = False
        (yy, MM, mday, hh, mm, ss, wday, yday) =  utc[0:3] + (utc[3]+z,) + utc[4:7] + (utc[7],)
        #Если существует разница во времени, применяем изменения
        if source == 'dht' and rtc[3] != hh:
            print('RTC: Old Time: {:0>2d}-{:0>2d}-{:0>2d} {:0>2d}:{:0>2d}:{:0>2d}'\
            .format(rtc[0], rtc[1], rtc[2], rtc[3], rtc[4], rtc[5]))
            self.datetime((yy, MM, mday, hh, mm, ss, wday, yday))
        elif source == 'esp' or source == 'ntp' or rtc[3] != hh or rtc[4] != mm or rtc[5] != ss:
            print('RTC: Old Time: {:0>2d}-{:0>2d}-{:0>2d} {:0>2d}:{:0>2d}:{:0>2d}'\
            .format(rtc[0], rtc[1], rtc[2], rtc[3], rtc[4], rtc[5]))
            self.datetime((yy, MM, mday, hh, mm, ss, wday, yday))
        #else: #Если разница во времени не обнаружена, выводим время с DS3231
        #    print('RTC: No time change: {:0>2d}-{:0>2d}-{:0>2d} {:0>2d}:{:0>2d}:{:0>2d}'\
        #    .format(yy, MM, mday, hh, mm, ss))


    @property
    def set_zone(self):
        """Установка временной зоны в процессе работы"""
        return self.zone
        
    @set_zone.setter
    def set_zone(self, timez):
        """Сеттер для установки звременной зоны в процессе работы"""
        self.zone = timez
