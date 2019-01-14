import gc
import uasyncio as asyncio
from machine import Pin, freq
from wificonnect import WiFiControl
from i2c_pcf8563 import PCF8563


class Main(WiFiControl):
    def __init__(self):
        super().__init__()
        self.DEBUG = True                               #Режим отладки, делаем программу разговорчивой
        self.wifi_led = Pin(2, Pin.OUT, value = 1)      #Pin2, светодиод на плате контроллера


        loop = asyncio.get_event_loop()
        loop.create_task(self._heartbeat())             #Индикация подключения WiFi


    #Индикация подключения WiFi
    async def _heartbeat(self):
        while True:
            if self.config['internet_outage'] == True:
                self.wifi_led(not self.wifi_led())      #Быстрое мигание, если соединение отсутствует
                await asyncio.sleep_ms(200)
            elif self.config['internet_outage'] == False:
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
            self.config['MemFree'] = str(round(gc.mem_free()/1024, 2))
            self.config['MemAvailab'] = str(round(gc.mem_alloc()/1024, 2))
            self.config['FREQ'] = str(freq()/1000000)
            wifi = 'connected' if not self.config['internet_outage'] else 'disconnected'
            gc.collect()                                                #Очищаем RAM
            try:
                self.dprint('################# DEBUG MESSAGE ##########################')
                self.dprint('Uptime:', str(self.config['Uptime'])+' min')
                self.dprint('WiFi:', wifi)
                self.dprint('IP:', self.config['IP'])
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
