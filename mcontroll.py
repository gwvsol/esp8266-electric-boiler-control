import gc
import uasyncio as asyncio
from machine import I2C, Pin, freq
from wificonnect import config
from wificonnect import WiFiControl
from i2c_pcf8563 import PCF8563
from ssd1306 import SSD1306_I2C
from term_adc import READ_TERM
from bme280 import BME280
import gc


class Main(WiFiControl):
    def __init__(self):
        super().__init__()
        self.wifi_led = Pin(2, Pin.OUT, value = 1)              #Pin2, светодиод на плате контроллера
        self.i2c = I2C(scl=Pin(14), sda=Pin(12), freq=400000)
        self.rtc = PCF8563(self.i2c, 0x51, zone=3)
        self.oled = SSD1306_I2C(128, 64, self.i2c, 0x3c)
        self.bme = BME280(i2c=self.i2c, address=0x76)
        self.temp = READ_TERM()
        

        loop = asyncio.get_event_loop()
        loop.create_task(self._heartbeat())                     #Индикация подключения WiFi
        loop.create_task(self._display())
        loop.create_task(self._dataupdate())
        

    async def _dataupdate(self):
        while True:
            self.config['RTC_TIME'] = self.rtc.datetime()
            rtc = self.config['RTC_TIME']
            #Проверка летнего или зименего времени каждую минуту в 30с
            if rtc[5] == 30: 
                self.rtc.settime('dht')
            #Если у нас режим подключения к точке доступа и если есть соединение, подводим часы по NTP
            if self.config['MODE_WiFi'] == 'ST' and not self.config['no_wifi']:
                #Подводка часов по NTP каждые сутки в 22:00:00
                if rtc[3] == 22 and rtc[4] == 0 and rtc[5] < 3 and self.config['NTP_UPDATE']:
                        self.config['NTP_UPDATE'] = False
                        self.rtc.settime('ntp')
                        await asyncio.sleep(1)
                        self.config['NTP_UPDATE'] = True
            self.config['TEMP'] = round(self.temp.value, 2)
            self.config['PRESSURE'] = round(float(self.bme.values[1]) * 760 / 1013.25, 2)
            self.config['HUMIDITY'] = self.bme.values[2]
            await asyncio.sleep(1)


    async def _display(self):
        while True:
            rtc = self.config['RTC_TIME']
            self.oled.fill(0)
            #self.oled.text('IP: {}'.format(self.config['IP']), 0, 2)
            self.oled.text('{:0>2d}-{:0>2d}-{:0>2d}'.format(rtc[0], rtc[1], rtc[2]), 25, 17)
            self.oled.text('{:0>2d}:{:0>2d}:{:0>2d}' .format(rtc[3], rtc[4], rtc[5]), 25, 27)
            self.oled.text('{}\'C'.format(self.config['TEMP']), 25, 37)
            self.oled.text('{}mmHg'.format(self.config['PRESSURE']), 25, 47)
            self.oled.text('{}%'.format(self.config['HUMIDITY']), 25, 57)
            self.oled.show()
            await asyncio.sleep(1)


    #Индикация подключения WiFi
    async def _heartbeat(self):
        while True:
            if self.config['no_wifi'] and self.config['MODE_WiFi'] == 'ST':
                self.wifi_led(not self.wifi_led())      #Быстрое мигание, если соединение отсутствует
                await asyncio.sleep_ms(200)
            elif not self.config['no_wifi'] and self.config['MODE_WiFi'] == 'ST':
                self.wifi_led(0)                        #Редкое мигание при подключении
                await asyncio.sleep_ms(50)
                self.wifi_led(1)
                await asyncio.sleep_ms(5000)
            else:
                self.wifi_led(0)                        #Два быстрых миганиения при AP Mode
                await asyncio.sleep_ms(50)
                self.wifi_led(1)
                await asyncio.sleep_ms(50)
                self.wifi_led(0)
                await asyncio.sleep_ms(50)
                self.wifi_led(1)
                await asyncio.sleep_ms(5000)


    async def _run_main_loop(self):                                     #Бесконечный цикл
        while True:
            if self.config['DEBUG']:
                self.config['MemFree'] = str(round(gc.mem_free()/1024, 2))
                self.config['MemAvailab'] = str(round(gc.mem_alloc()/1024, 2))
                self.config['FREQ'] = str(freq()/1000000)
                if self.config['MODE_WiFi'] == 'ST':
                    wifi = 'connect' if not self.config['no_wifi'] else 'disconnect'
                else:
                    wifi = 'AP mode'
                rtc = self.config['RTC_TIME']
            gc.collect()                                                #Очищаем RAM
            try:
                self.dprint('################# DEBUG MESSAGE ##########################')
                self.dprint('Uptime:', str(self.config['Uptime'])+' min')
                self.dprint('Date: {:0>2d}-{:0>2d}-{:0>2d}'.format(rtc[0], rtc[1], rtc[2]))
                self.dprint('Time: {:0>2d}:{:0>2d}:{:0>2d}'.format(rtc[3], rtc[4], rtc[5]))
                self.dprint('WiFi:', wifi)
                self.dprint('IP:', self.config['IP'])
                self.dprint('TEMP: {}\'C'.format(self.config['TEMP']))
                self.dprint('PRESSURE: {}mmHg'.format(self.config['PRESSURE']))
                self.dprint('HUMIDITY: {}%'.format(self.config['HUMIDITY']))
                self.dprint('MemFree:', '{}Kb'.format(self.config['MemFree']))
                self.dprint('MemAvailab:', '{}Kb'.format(self.config['MemAvailab']))
                self.dprint('FREQ:', '{}MHz'.format(self.config['FREQ']))
                self.dprint('################# DEBUG MESSAGE END ######################')
            except Exception as e:
                self.dprint('Exception occurred: ', e)
            self.config['Uptime'] += 1
            await asyncio.sleep(60)


    async def main(self):
        while True:
            try:
                await self.connect()
                await self._run_main_loop()
            except Exception as e:
                self.dprint('Global communication failure: ', e)
                await asyncio.sleep(20)


gc.collect()                                            #Очищаем RAM
def_main = Main()
loop = asyncio.get_event_loop()
loop.run_until_complete(def_main.main())
