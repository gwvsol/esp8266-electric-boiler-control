import gc, network, os, json
import uasyncio as asyncio
from machine import I2C, Pin, freq
gc.collect()                                                            #Очищаем RAM
from i2c_ds3231 import DS3231
from ssd1306 import SSD1306_I2C
from term_adc import READ_TERM
from bme280 import BME280
gc.collect()                                                            #Очищаем RAM

#Базовый класс
class WiFiBase(object):
    def __init__(self):
        self.wifi_led = Pin(2, Pin.OUT, value = 1)              #Pin2, светодиод на плате контроллера
        self.i2c = I2C(scl=Pin(14), sda=Pin(12), freq=400000)   #Pin12 и 14 i2c шина
        self.default_on = Pin(14, Pin.IN)                       #Pin14, кнопка для сброса настроек в дефолт
        #Дефолтные настройки, если файла config.txt не обнаружено в системе
        self.default = {}
        self.default['DEBUG'] = True             #Разрешаем отладочный сообщения
        self.default['MODE_WiFi'] = 'AP'         #Включаем точку доступа
        self.default['ssid'] = 'HEAT_CONTROL'    #Устанавливаем имя точки доступа
        self.default['wf_pass'] = 'roottoor'     #Пароль для точки доступа
        self.default['timezone'] = 3             #Временная зона
        self.default['DST'] = True               #Разрешаем переход с летнего на зимнее время
        self.default['T_WATER'] = 20.0           #Температура в бойлере
        #Дефолтный хещ логина и пароля для web admin (root:root)
        self.default_web = str(b'0242c0436daa4c241ca8a793764b7dfb50c223121bb844cf49be670a3af4dd18')
        self.config = {} #Все настройки системы
        self.config['DEBUG'] = True
        self.config['MODE_WiFi'] = None
        self.config['ssid'] = None
        self.config['wf_pass'] = None
        self.config['TIMEZONE'] = None
        self.config['DST'] = None
        self.config['T_WATER'] = None
        self.config['ADR_RTC'] = 0x68                   #Адрес RTC DS3231
        self.config['ADR_OLED'] = 0x3c                  #Адрес OLED
        self.config['ADR_BME'] = 0x76                   #Адрес BME280 барометра
        self.config['WIFI_AP'] = ('192.168.4.1', '255.255.255.0', '192.168.4.1', '208.67.222.222')
        self.config['IP'] = None                        #Дефолтный IP адрес
        self.config['no_wifi'] = True                   #Интернет отключен(значение True)
        self.config['Uptime'] = 0                       #Время работы контроллера
        self.config['MemFree'] = None
        self.config['MemAvailab'] = None
        self.config['FREQ'] = None
        self.config['RTC_TIME'] = (0, 1, 1, 0, 0, 0, 0, 0)
        self.config['NTP_UPDATE'] = True
        self.config['TEMP'] = None
        self.config['PRESSURE'] = None
        self.config['HUMIDITY'] = None

        #Eсли нет файла config.txt или нажата кнопка сброса в дефолт, создаем файл config.txt
        if self.exists('config.txt') == False or not self.default_on(): 
            self.dprint('Create new config.txt file')
            with open('config.txt', 'w') as f:  
                json.dump(self.default, f)
        #Eсли нет файла root.txt или нажата кнопка сброса в дефолт, создаем его
        if self.exists('root.txt') == False or not self.default_on(): 
            self.dprint('Create new root.txt file')
            with open('root.txt', 'w') as f:
                f.write(self.default_web)
        #Читаем настройки из файла config.txt
        with open('config.txt', 'r') as f:
            conf = json.loads(f.read())
        #Обновляем настройки полученные из файла config.txt
        self.config['DEBUG'] = conf['DEBUG']
        self.config['MODE_WiFi'] = conf['MODE_WiFi']    #Режим работы WiFi AP или ST
        self.config['ssid'] = conf['ssid']              #SSID для подключения к WiFi
        self.config['wf_pass'] = conf['wf_pass']        #Пароль для подключения к WiFi
        self.config['TIMEZONE'] = conf['timezone']      #Временная зона
        self.config['DST'] = conf['DST']                #True включен переход на зимнее время False - выключен
        self.config['T_WATER'] = conf['T_WATER']        #Температура вводы в бойлере
        #Начальные настройки сети AP или ST
        if self.config['MODE_WiFi'] == 'AP':
            self._ap_if = network.WLAN(network.AP_IF)
            self.config['WIFI'] = self._ap_if
        elif self.config['MODE_WiFi'] == 'ST':
            self._sta_if = network.WLAN(network.STA_IF)
            self.config['WIFI'] = self._sta_if
        #Настройка для работы с RTC, OLED и барометром на BME280
        self.rtc = DS3231(self.i2c, self.config['ADR_RTC'], self.config['TIMEZONE'])
        self.oled = SSD1306_I2C(128, 64, self.i2c, self.config['ADR_OLED'])
        self.bme = BME280(i2c=self.i2c, address=self.config['ADR_BME'])
        self.temp = READ_TERM()

        loop = asyncio.get_event_loop()
        loop.create_task(self._heartbeat())                             #Индикация подключения WiFi
        loop.create_task(self._display())                               #Работа экрана
        loop.create_task(self._dataupdate())                            #Обновление информация и часы


    #Выводим отладочные сообщения
    def dprint(self, *args):
        if self.config['DEBUG']:
            print(*args)


    #Проверяем наличие файлов
    def exists(self, path):
        try:
            os.stat(path)
        except OSError:
            return False
        return True


    #Настройка для режима Точка доступа и подключения к сети WiFi
    def _con(self):
        if self.config['MODE_WiFi'] == 'AP':
            self.config['WIFI'].active(True)
            #Устанавливаем SSID и пароль для подключения к Точке доступа
            self.config['WIFI'].config(essid=self.config['ssid'], password=self.config['wf_pass'])
            #Устанавливаем статический IP адрес, шлюз, dns
            self.config['WIFI'].ifconfig(self.config['WIFI_AP'])
        elif self.config['MODE_WiFi'] == 'ST':
            self.config['WIFI'].active(True)
            network.phy_mode(1) # network.phy_mode = MODE_11B
            #Подключаемся к WiFi сети
            self.config['WIFI'].connect(self.config['ssid'], self.config['wf_pass'])

    
    #Выводим сообщения об ошибках соединения
    def _error_con(self):
        #Соединение не установлено...
        if self.config['WIFI'].status() == network.STAT_CONNECT_FAIL:
            self.dprint('WiFi: Failed due to other problems')
        #Соединение не установлено, причина не найдена точка доступа
        if self.config['WIFI'].status() == network.STAT_NO_AP_FOUND:
            self.dprint('WiFi: Failed because no access point replied')
        #Соединение не установлено, не верный пароль
        if self.config['WIFI'].status() == network.STAT_WRONG_PASSWORD:
            self.dprint('WiFi: Failed due to incorrect password')


    #Подключение к сети WiFi или поднятие точки доступа
    async def connect_wf(self):
        if self.config['MODE_WiFi'] == 'AP': #Если точка доступа
            self.dprint('WiFi AP Mode!')
            self._con() #Настройка для режима Точка доступа и подключения к сети WiFi
            if self.config['WIFI'].status() == -1:
                self.dprint('WiFi: AP Mode OK!')
                self.config['IP'] = self.config['WIFI'].ifconfig()[0]
                self.dprint('WiFi:', self.config['IP'])
                self.config['no_wifi'] = False
        elif self.config['MODE_WiFi'] == 'ST': #Если подключаемся к сети
            self.dprint('Connecting to WiFi...')
            self._con() #Настройка для режима Точка доступа и подключения к сети WiFi
            if self.config['WIFI'].status() == network.STAT_CONNECTING:
                self.dprint('WiFi: Waiting for connection to...')
            # Задержка на соединение, если не успешно, будет выдана одна из ошибок
            # Выполнение условия проверяем каждую секунду, задержка для получения IP адреса от DHCP
            while self.config['WIFI'].status() == network.STAT_CONNECTING:
                await asyncio.sleep(1)
            #Соединение успешно установлено
            if self.config['WIFI'].status() == network.STAT_GOT_IP:
                self.dprint('WiFi: Connection successfully!')
                self.config['IP'] = self.config['WIFI'].ifconfig()[0]
                self.dprint('WiFi:', self.config['IP'])
                self.config['no_wifi'] = False #Сообщаем, что соединение успешно установлено
            #Если соединение по каким-то причинам не установлено
            if not self.config['WIFI'].isconnected():
                self.config['no_wifi'] = True #Сообщаем, что соединение не установлено
                self.dprint('WiFi: Connection unsuccessfully!')
            self._error_con() #Выводим сообщения, о причинах отсутствия соединения


    #Переподключаемся к сети WiFi
    async def reconnect(self):
        self.dprint('Reconnecting to WiFi...')
        #Сбрасываем IP адрес к виду 0.0.0.0
        self.config['IP'] = self.config['WIFI'].ifconfig()[0]
        #Разрываем соединение, если они не разорвано
        self.config['WIFI'].disconnect()
        await asyncio.sleep(1)
        self._con() #Настройка для режима Точка доступа и подключения к сети WiFi
        # Задержка на соединение, если не успешно, будет выдана одна из ошибок
        # Выполнение условия проверяем каждые 20 милисекунд, задержка для получения IP адреса от DHCP
        while self.config['WIFI'].status() == network.STAT_CONNECTING:
            await asyncio.sleep_ms(20)
        #Если соединение установлено
        if self.config['WIFI'].status() == network.STAT_GOT_IP:
            #Сохраняем новый IP адрес
            self.config['IP'] = self.config['WIFI'].ifconfig()[0]
            self.config['no_wifi'] = False #Сообщаем, что соединение успешно установлено
            self.dprint('WiFi: Reconnecting successfully!')
            self.dprint('WiFi:', self.config['IP'])
        self._error_con() #Выводим сообщения, о причинах отсутствия соединения
        #Если по какой-то причине соединение не установлено
        if not self.config['WIFI'].isconnected():
            self.config['no_wifi'] = True #Сообщаем, что соединение не установлено
            self.dprint('WiFi: Reconnecting unsuccessfully!')
        await asyncio.sleep(1)


    #Проверка соединения с Интернетом
    async def _check_wf(self):
        while True:
            if not self.config['no_wifi']:                              #Если оединение установлено
                if self.config['WIFI'].status() == network.STAT_GOT_IP: #Проверяем наличие соединения
                    await asyncio.sleep(1)
                else:                                                   #Если соединение отсутсвует или оборвано
                    await asyncio.sleep(1)
                    self.config['no_wifi'] = True                       #Сообщаем, что соединение оборвано
            else:                                                       #Если соединение отсутсвует
                await asyncio.sleep(1)
                await self.reconnect()                                  #Переподключаемся
        await asyncio.sleep(1)
        gc.collect() 


    #Подключаемся к WiFi или поднимаем точку доступа
    async def connect(self):
        await self.connect_wf()                                         #Подключение или точка доступа, зависит от настройки
        if self.config['MODE_WiFi'] == 'ST':
            loop = asyncio.get_event_loop()
            loop.create_task(self._check_wf())
        elif self.config['MODE_WiFi'] == 'AP':
            gc.collect()
  
#=======================================================================

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
                if rtc[3] == 23 and rtc[4] == 41 and rtc[5] < 3 and self.config['NTP_UPDATE']:
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
            self.oled.text('IP: {}'.format(self.config['IP']), 0, 2)
            self.oled.text('{:0>2d}-{:0>2d}-{:0>2d}'.format(rtc[0], rtc[1], rtc[2]), 25, 17)
            self.oled.text('{:0>2d}:{:0>2d}:{:0>2d}'.format(rtc[3], rtc[4], rtc[5]), 25, 27)
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
                self.dprint('TEMP: {:.2f}\'C'.format(self.config['TEMP']))
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


gc.collect()                                                            #Очищаем RAM
def_main = WiFiBase()
loop = asyncio.get_event_loop()
loop.run_until_complete(def_main.main())
