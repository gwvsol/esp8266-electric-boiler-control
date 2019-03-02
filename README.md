## ESP8266-Electric-boiler-controller

[![micropython](https://user-images.githubusercontent.com/13176091/53680744-4dfcc080-3ce8-11e9-94e1-c7985181d6a5.png)](https://micropython.org/)

Контроллер для управления нагревом воды в бойлере. Собран на ESP8266. В качестве датчика температуры используется DS18B20, а часов точного времени DS3231. Для управления нагревательным элементом, симистор BTA41-600 с рабочим током 40А. Питание контроллера выполнено на HLK-PM03 3W.
##### Функции контроллера
* Поддержание заданной температуры воды
* Включение нагрева по рассписанию
* Одноразовое включение нагрева
* Поддержка работы по временным зонам
* Автоматический переход с летнего на зимнее время
* Автоматическая подводка часов по NTP серверу, один раз в сутки, при наличии WiFi соединения.
* Web интерфейс для настройки контроллера
* API интерфейс для интеграции с системой умный дом (Например, [OpenHab](https://www.openhab.org/))
##### Используемые библиотеки
* [OneWire](https://github.com/micropython/micropython/blob/master/drivers/onewire/onewire.py)
* [DS18B20](https://github.com/micropython/micropython/blob/master/drivers/onewire/ds18x20.py)
* [DS3231](https://github.com/gwvsol/ESP8266-i2c-DS3231)
* [timezone](https://github.com/gwvsol/ESP8266-TimeZone)
* [collections](https://github.com/micropython/micropython-lib/tree/master/collections/collections) и зависимости
* [uasyncio](https://github.com/micropython/micropython-lib/tree/master/uasyncio/uasyncio) и зависисмоти
* [picoweb](https://github.com/pfalcon/picoweb)
##### Web интерфес
Логин и пароль по умолчанию: root root, при настройке контроллера его необходимо изменить. В случае утери пароля, предусмотрен сброс настроек контроллера.

![2019-03-02-10-14-37](https://user-images.githubusercontent.com/13176091/53681250-8ce24480-3cef-11e9-8c19-a6087d8a1010.png) ![2019-03-02-10-14-50](https://user-images.githubusercontent.com/13176091/53681259-a5eaf580-3cef-11e9-9e6d-dfa91ab67fbf.png) ![2019-03-02-10-15-26](https://user-images.githubusercontent.com/13176091/53681273-c915a500-3cef-11e9-907d-9d1ab44bf3b6.png) ![2019-03-02-10-15-51](https://user-images.githubusercontent.com/13176091/53681332-b485dc80-3cf0-11e9-8520-b8c29e8a927e.png) ![2019-03-02-10-16-11](https://user-images.githubusercontent.com/13176091/53681348-ff9fef80-3cf0-11e9-970f-df6319f08843.png) ![2019-03-02-10-16-17](https://user-images.githubusercontent.com/13176091/53681366-4c83c600-3cf1-11e9-80f3-bbab6f49703a.png)
##### API интефейс
Поддерживает GET и POST запросы.

*Запрос значения температуры воды* ```/api/v1/temp```

```curl -s -u root:root -G http://192.168.0.16/api/v1/temp```

*Запрос значения поддерживаемой температуры или установка нового значения* ```/api/v1/stemp```

```curl -s -u root:root -G http://192.168.0.16/api/v1/stemp```

```curl -s -u root:root -X POST http://192.168.0.16/api/v1/stemp?stemp=56.60``` или

```curl -s -u root:root -X POST http://192.168.0.16/api/v1/stemp/30.60```

