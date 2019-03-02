## ESP8266-Electric-boiler-controller

[![micropython](https://user-images.githubusercontent.com/13176091/53680744-4dfcc080-3ce8-11e9-94e1-c7985181d6a5.png)](https://micropython.org/)

Контроллер для управления нагревом воды в бойлере. Собран на ESP8266. В качестве датчика температуры используется DS18B20, а часов точного времени DS3231. Для управления нагревательным элементом, симистор BTA41-600 с рабочим током 40А. Питание контроллера выполнено на HLK-PM03 3W.

#### Функции контроллера
* Поддержание заданной температуры воды
* Включение нагрева по рассписанию
* Одноразовое включение нагрева
* Поддержка работы по временным зонам
* Автоматический переход с летнего на зимнее время
* Автоматическая подводка часов по NTP серверу, один раз в сутки, при наличии WiFi соединения.
* Web интерфейс для настройки контроллера
* API интерфейс для интеграции с системой умный дом (Например, [OpenHab](https://www.openhab.org/))

#### Используемые библиотеки
* [term_adc](https://github.com/gwvsol/ESP8266-ADC-Thermistor)
* [DS3231](https://github.com/gwvsol/ESP8266-i2c-DS3231)
* [timezone](https://github.com/gwvsol/ESP8266-TimeZone)
* [collections](https://github.com/micropython/micropython-lib/tree/master/collections/collections) и зависимости
* [uasyncio](https://github.com/micropython/micropython-lib/tree/master/uasyncio/uasyncio) и зависисмоти
* [picoweb](https://github.com/pfalcon/picoweb)

#### Web интерфес
Логин и пароль по умолчанию: root root, при настройке контроллера его необходимо изменить. В случае утери пароля, предусмотрен сброс настроек контроллера.

![2019-03-02-10-14-37](https://user-images.githubusercontent.com/13176091/53681250-8ce24480-3cef-11e9-8c19-a6087d8a1010.png) 
![2019-03-02-10-14-50](https://user-images.githubusercontent.com/13176091/53681259-a5eaf580-3cef-11e9-9e6d-dfa91ab67fbf.png) 
![2019-03-02-10-15-26](https://user-images.githubusercontent.com/13176091/53681273-c915a500-3cef-11e9-907d-9d1ab44bf3b6.png) 
![2019-03-02-10-15-51](https://user-images.githubusercontent.com/13176091/53681332-b485dc80-3cf0-11e9-8520-b8c29e8a927e.png) 
![2019-03-02-10-16-11](https://user-images.githubusercontent.com/13176091/53681348-ff9fef80-3cf0-11e9-970f-df6319f08843.png) 
![2019-03-02-10-16-17](https://user-images.githubusercontent.com/13176091/53681366-4c83c600-3cf1-11e9-80f3-bbab6f49703a.png)

#### API интефейс
Поддерживает GET и POST запросы.

*Запрос значения температуры воды* ```/api/v1/temp```

```curl -s -u root:root -G http://YOUR_IP/api/v1/temp```

*Запрос значения поддерживаемой температуры или установка нового значения* ```/api/v1/stemp```

```curl -s -u root:root -G http://YOUR_IP/api/v1/stemp```

```curl -s -u root:root -X POST http://YOUR_IP/api/v1/stemp?stemp=56.60``` или

```curl -s -u root:root -X POST http://YOUR_IP/api/v1/stemp/30.60```

*Запрос значения или установка постоянной работы/выключения системы обогрева воды* ```/api/v1/wall```

```curl -s -u root:root -G http://YOUR_IP/api/v1/wall```

```curl -s -u root:root -X POST http://YOUR_IP/api/v1/wall?wall=1/{0} или ?wall=ON/{OFF}``` или

```curl -s -u root:root -X POST http://YOUR_IP/api/v1/wall/1{0} или wall/ON{OFF}```

*Запрос значения или установка работы/выключения системы обогрева воды по рассписанию* ```/api/v1/wtab```

```curl -s -u root:root -G http://YOUR_IP/api/v1/wtab```

```curl -s -u root:root -X POST http://YOUR_IP/api/v1/wtab?wtab=1/{0} или ?wtab=ON/{OFF}``` или

```curl -s -u root:root -X POST http://YOUR_IP/api/v1/wtab/1{0} или wtab/ON{OFF}```

*Запрос значения или единоразовое включение/выключения системы обогрева воды* ```/api/v1/otime```

```curl -s -u root:root -G http://YOUR_IP/api/v1/otime```

```curl -s -u root:root -X POST http://YOUR_IP/api/v1/otime?otime=1/{0} или ?otime=ON/{OFF}``` или

```curl -s -u root:root -X POST http://YOUR_IP/api/v1/otime/1{0} или otime/ON{OFF}```

*Запрос значения или установка времени включения системы обогрева воды* ```/api/v1/timeon```

```curl -s -u root:root -G http://YOUR_IP/api/v1/timeon```

```curl -s -u root:root -X POST http://YOUR_IP/api/v1/timeon?timeon=21:10``` или

```curl -s -u root:root -X POST http://YOUR_IP/api/v1/timeon/21:45```

*Запрос значения или установка времени выключения системы обогрева воды* ```/api/v1/timeoff```

```curl -s -u root:root -G http://YOUR_IP/api/v1/timeoff```

```curl -s -u root:root -X POST http://YOUR_IP/api/v1/timeon?timeoff=21:10``` или

```curl -s -u root:root -X POST http://YOUR_IP/api/v1/timeoff/21:45```

*Запрос значения мощности обогрева воды* ```/api/v1/power```

```curl -s -u root:root -G http://YOUR_IP/api/v1/power```

#### Файл настроек контроллера
В контроллере используется два файла настроек, в ```config.txt``` находятся все основные настройки контроллера. Файл имеет вид:
```json
{
    "WORK_TABLE": false, 
    "wf_pass": "Fedex##54", 
    "K": 0, 
    "DST": true, 
    "ssid": "w2234", 
    "D": 1.03424e-07, 
    "TIME_OFF": [0, 0, 0, 6, 0, 0, 0, 0], 
    "BALANCE_R": 9550.0, 
    "timezone": 3, 
    "THERMISTOR_R": 10000.0, 
    "A": 0.00335402, 
    "B": 0.000246038, 
    "C": 3.40538e-06, 
    "DEBUG": true, 
    "WORK_ALL": false, 
    "MODE_WiFi": "ST", 
    "ONE-TIME": false, 
    "TIME_ON": [0, 0, 0, 5, 0, 0, 0, 0], 
    "T_WATER": 30.0
}
```

Подавляющее большинство настроек этого файла изменяются через Web или API интерфейс. Исключение составляют только ```"DEBUG": true, "A": 0.00335402, "B": 0.000246038, "C": 3.40538e-06, "D": 1.03424e-07, "K": 0, "BALANCE_R": 9550.0, "THERMISTOR_R": 10000.0```. Параметер ```DEBUG``` необходим тольк для отладки контроллера. Парамеры ```A, B, C, D, K, BALANCE_R, THERMISTOR_R``` необходимы для настройки работы контроллера с терморезистором.

Для установки в контроллер нового файла ```config.txt``` используется USB-UART преобразователь с уровнями сигнала 3,3v, а так же утилита ```ampy```.
```bash
ampy put config.txt
```
Файл ```root.txt``` используется для хранения ```hash``` логина и пароля. По умолчанию этот файл хранит ```hash``` ```root:root```. Если же в процессе работы логин и пароль был изменен, файл будет содержать новый ```hash```.

Во время первого включения, создаются эти два файла, которые в дальнейшем используются для работы контроллера.

#### Компиляция
Для компиляции используется [SDK for ESP8266/ESP8285 chips](https://github.com/pfalcon/esp-open-sdk). 

После компиляции, необходимо очистить чип ESP8266 и залить новую прошивку, для чего используется ```esptool```
```bash
pip3 install setuptools
pip3 install esptool
```
```bash
esptool.py --port /dev/ttyUSB0 erase_flash
esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect -fm dio 0 firmware-combined.bin
```
***
#### Модель печатной платы контроллера
![2018-12-25_00-14-01](https://user-images.githubusercontent.com/13176091/53683429-59141880-3d09-11e9-99ac-9264537ced6f.png)
![2018-12-25_00-13-10](https://user-images.githubusercontent.com/13176091/53683434-73e68d00-3d09-11e9-9c34-9804adbb2fb1.png)
***








