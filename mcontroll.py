import gc, network, os, json
import uasyncio as asyncio
from machine import I2C, Pin, freq
from wificonnect import WiFiControl
gc.collect()                                                            # Очищаем RAM
from i2c_ds3231 import DS3231
from term_adc import READ_TERM
from webapp import app
gc.collect()                                                            # Очищаем RAM

# Базовый класс
class Main(WiFiControl):
    def __init__(self):
        super().__init__()
        self.wifi_led = Pin(2, Pin.OUT, value = 1)              # Pin2, светодиод на плате контроллера
        self.i2c = I2C(scl=Pin(14), sda=Pin(12), freq=400000)   # Pin12 и 14 i2c шина
        self.default_on = Pin(14, Pin.IN)                       # Pin14, кнопка для сброса настроек в дефолт
        # Дефолтные настройки, если файла config.txt не обнаружено в системе
        self.default = {}
        self.default['DEBUG'] = True             # Разрешаем отладочный сообщения
        self.default['MODE_WiFi'] = 'AP'         # Включаем точку доступа
        self.default['ssid'] = 'HEAT_CONTROL'    # Устанавливаем имя точки доступа
        self.default['wf_pass'] = 'roottoor'     # Пароль для точки доступа
        self.default['timezone'] = 3             # Временная зона
        self.default['DST'] = True               # Разрешаем переход с летнего на зимнее время
        self.default['T_WATER'] = 20.0           # Температура в бойлере
        self.default['TIME_ON'] = (0, 0, 0, 5, 0, 0, 0, 0)  # Время включения нагрева бойлера 05:00
        self.default['TIME_OFF'] = (0, 0, 0, 6, 0, 0, 0, 0) # Время выключения нагрева бойлера 06:00
        self.default['WORK_ALL'] = False         # Постоянный нагрев бойлера выключен
        self.default['WORK_TABLE'] = False       # Работа по расписнию
        self.default['ONE-TIME'] = False         # Одноразовое включение
        # Дефолтный хещ логина и пароля для web admin (root:root)
        self.default_web = str(b'0242c0436daa4c241ca8a793764b7dfb50c223121bb844cf49be670a3af4dd18')
        self.config['DEBUG'] = True                     # Разрешаем отладочный сообщения
        self.config['WEB_Port'] = 80                    # Порт на котором работает web приложение
        self.config['ADR_RTC'] = 0x68                   # Адрес RTC DS3231
        self.config['WIFI_AP'] = ('192.168.4.1', '255.255.255.0', '192.168.4.1', '208.67.222.222')
        self.config['IP'] = None                        # Дефолтный IP адрес
        self.config['no_wifi'] = True                   # Интернет отключен(значение True)
        self.config['Uptime'] = 0                       # Время работы контроллера
        self.config['RTC_TIME'] = (0, 1, 1, 0, 0, 0, 0, 0) # Дефолтное время
        self.config['NTP_UPDATE'] = True                # Разрешаем обновление по NTP
        self.config['MemFree'] = None
        self.config['MemAvailab'] = None
        self.config['FREQ'] = None
        
        self.config['TEMP'] = None

        # Eсли нет файла config.txt или нажата кнопка сброса в дефолт, создаем файл config.txt
        if self.exists('config.txt') == False or not self.default_on(): 
            self.dprint('Create new config.txt file')
            with open('config.txt', 'w') as f:  
                json.dump(self.default, f)
        # Eсли нет файла root.txt или нажата кнопка сброса в дефолт, создаем его
        if self.exists('root.txt') == False or not self.default_on(): 
            self.dprint('Create new root.txt file')
            with open('root.txt', 'w') as f:
                f.write(self.default_web)
        # Читаем настройки из файла config.txt
        with open('config.txt', 'r') as f:
            conf = json.loads(f.read())
        # Обновляем настройки полученные из файла config.txt
        self.config['DEBUG'] = conf['DEBUG']
        self.config['MODE_WiFi'] = conf['MODE_WiFi']    # Режим работы WiFi AP или ST
        self.config['ssid'] = conf['ssid']              # SSID для подключения к WiFi
        self.config['wf_pass'] = conf['wf_pass']        # Пароль для подключения к WiFi
        self.config['TIMEZONE'] = conf['timezone']      # Временная зона
        self.config['DST'] = conf['DST']                # True включен переход на зимнее время False - выключен
        self.config['T_WATER'] = conf['T_WATER']        # Заданная Температура вводы в бойлере
        self.config['TIME_ON'] = conf['TIME_ON']        # Время включения нагрева бойлера
        self.config['TIME_OFF'] = conf['TIME_OFF']      # Время выключения нагрева бойлера
        self.config['WORK_ALL'] = conf['WORK_ALL']      # Постоянный нагрев бойлера выключен
        self.config['WORK_TABLE'] = conf['WORK_TABLE']  # Работа по рассписанию
        self.config['ONE-TIME'] = conf['ONE-TIME']      # Одноразовое включение
        # Начальные настройки сети AP или ST
        if self.config['MODE_WiFi'] == 'AP':
            self._ap_if = network.WLAN(network.AP_IF)
            self.config['WIFI'] = self._ap_if
        elif self.config['MODE_WiFi'] == 'ST':
            self._sta_if = network.WLAN(network.STA_IF)
            self.config['WIFI'] = self._sta_if
        # Настройка для работы с RTC
        self.config['RTC'] = DS3231(self.i2c, self.config['ADR_RTC'], self.config['TIMEZONE'])
        self.rtc = self.config['RTC']
        self.temp = READ_TERM()
        
        loop = asyncio.get_event_loop()
        loop.create_task(self._heartbeat())                             # Индикация подключения WiFi
        loop.create_task(self._dataupdate())                            # Обновление информации и часы
        loop.create_task(self._start_web_app())                         # Включаем WEB приложение
        
    
    # Запуск WEB приложения
    async def _start_web_app(self):
        """Run/Work Web App"""
        while True:
            gc.collect()                                                    # Очищаем RAM
            await asyncio.sleep(5)
            if not self.config['no_wifi'] or self.config['MODE_WiFi'] == 'AP':
                self.ip = self.config['WIFI'].ifconfig()[0]
                self.dprint('WebAPP: Running...')
                app.run(debug=self.config['DEBUG'], host =self.ip, port=self.config['WEB_Port'])
            

    async def _dataupdate(self):
        while True:
            """RTC Update"""
            self.config['RTC_TIME'] = self.rtc.datetime()
            rtc = self.config['RTC_TIME']
            # Проверка летнего или зименего времени каждую минуту в 30с
            if rtc[5] == 30: 
                self.rtc.settime('dht')
            # Если у нас режим подключения к точке доступа и если есть соединение, подводим часы по NTP
            if self.config['MODE_WiFi'] == 'ST' and not self.config['no_wifi']:
                # Подводка часов по NTP каждые сутки в 22:00:00
                if rtc[3] == 22 and rtc[4] == 5 and rtc[5] < 3 and self.config['NTP_UPDATE']:
                        self.config['NTP_UPDATE'] = False
                        self.rtc.settime('ntp')
                        await asyncio.sleep(1)
                        self.config['NTP_UPDATE'] = True
            """Data Update"""
            self.config['TEMP'] = round(self.temp.value, 2)
            gc.collect()                                    # Очищаем RAM
            await asyncio.sleep(1)


    # Индикация подключения WiFi
    async def _heartbeat(self):
        while True:
            if self.config['no_wifi'] and self.config['MODE_WiFi'] == 'ST':
                self.wifi_led(not self.wifi_led())      # Быстрое мигание, если соединение отсутствует
                await asyncio.sleep_ms(200)
            elif not self.config['no_wifi'] and self.config['MODE_WiFi'] == 'ST':
                self.wifi_led(0)                        # Редкое мигание при подключении
                await asyncio.sleep_ms(50)
                self.wifi_led(1)
                await asyncio.sleep_ms(5000)
            else:
                self.wifi_led(0)                        # Два быстрых миганиения при AP Mode
                await asyncio.sleep_ms(50)
                self.wifi_led(1)
                await asyncio.sleep_ms(50)
                self.wifi_led(0)
                await asyncio.sleep_ms(50)
                self.wifi_led(1)
                await asyncio.sleep_ms(5000)


    async def _run_main_loop(self):                                     # Бесконечный цикл
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
            gc.collect()                                                # Очищаем RAM
            try:
                self.dprint('################# DEBUG MESSAGE ##########################')
                self.dprint('Uptime:', str(self.config['Uptime'])+' min')
                self.dprint('Date: {:0>2d}-{:0>2d}-{:0>2d}'.format(rtc[0], rtc[1], rtc[2]))
                self.dprint('Time: {:0>2d}:{:0>2d}:{:0>2d}'.format(rtc[3], rtc[4], rtc[5]))
                self.dprint('WiFi:', wifi)
                self.dprint('IP:', self.config['IP'])
                self.dprint('TEMP: {:.2f}\'C'.format(self.config['TEMP']))
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


gc.collect()                                                            # Очищаем RAM
def_main = Main()
loop = asyncio.get_event_loop()
loop.run_until_complete(def_main.main())
