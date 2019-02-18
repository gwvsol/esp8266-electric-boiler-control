import picoweb, gc, ubinascii, os, json
from wificonnect import config
from machine import reset
gc.collect()                                                            # Очищаем RAM
from ubinascii import hexlify
from uhashlib import sha256
gc.collect()                                                            # Очищаем RAM


app = picoweb.WebApp(__name__)

http_head = """<!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width" initial-scale="1.0" maximum-scale="1.0" minimum-scale="1.0"/>
        <title>Boiler Control Admin</title>
        <style> 
        html { font-family: 'Lato', Calibri, Arial, sans-serif;
               height: 100%; }
        body { background: #ddd;
            color: #333; }
        .header { width: 100%;
            padding-top: .7em;
            padding-bottom: .7em;
            float: left;
            font-size: 1.3em;
            font-weight: 400;
            text-align: center; }
        .info { margin:0 auto;
                width:200px; }
        .menu { width: 100%;
            float: left;
            font-size: 1em;
            font-weight: 400;
            text-align: center; }
        .admin { margin: 0 auto;
                 width: 350px; }
        .footer { width: 100%;
            padding-top: 2em;
            padding-bottom: 2em;
            float: left;
            font-size: .5em;
            font-weight: 400;
            text-align: center; }
        a { text-decoration: none; }
        a:link { color: #333; }
        a:visited { color: #333; }
        a:hover { color: #333; }
        a:active { color: #333; }
        a.login { font-size: 1em; }
        </style>
        </head>
        <body>
        <h2><a class="menu" href="/">HOME</a></h2>"""

href_contr_set = '<a class="login" href="read">CONTROLLER SETTINGS</a>'
href_adm_panel = '<a class="login" href="admin">ADMIN PANEL</a>'

div_cl_header = '<div class="header">'
div_cl_info = '<div class="info">'
div_cl_admin = '<div class = "admin">'
div_end = '</div>'

span_main_param = '<span>MAIN PARAMETERS</span>'
span_boler_adm = '<span>Boiler Control Admin</span>'
span_err_pasw = '<span>Error Login<br>Close the browser, restart it,<br>and then try to log in again</span>'

wifi_form = """<form action='admin' method='POST'>
                    <fieldset>
                        <legend>Setting WiFi</legend>
                        <p><input type="radio" name="wifi" value="AP">AP<br>
                           <input type="radio" name="wifi" value="ST" checked>STATION</p>
                        <p><input type="text" name="ssid" placeholder="SSID" required autocomplete="off"></p>
                        <p><input type="password" name="pasw" pattern=".{8,12}" required title="8 to 12 characters" placeholder="WiFi Password" required autocomplete="off"></p>
                        <p><input type="submit" value="Set WiFi"></p>
                    </fieldset>
               </form>"""
               
passw_form = """<form action='admin' method='POST'>
                    <fieldset>
                        <legend>Chenge password</legend>
                        <p><input type="text" name="login" required placeholder="Login" autocomplete="off"></p>
                        <p><input type="password" name="passw" pattern=".{8,12}" required title="8 to 12 characters" required placeholder="Password" autocomplete="off"></p>
                        <p><input type="password" name="repassw" pattern=".{8,12}" required title="8 to 12 characters" required placeholder="Repeat Password" autocomplete="off"></p>
                        <p><input type="submit" value="Сhange password"></p>
                    </fieldset>
                </form>"""
                
date_set = """<form action='admin' method='POST'>
                <fieldset>
                    <legend>Setting date and time</legend>
                    <p>Daylight saving time<br>
                       <input type="radio" name="daylight" checked value="True">ON<br>
                       <input type="radio" name="daylight" value="False">OFF</p>
                    <p>Time on NTP server<br>
                        <input type="radio" name="ntp" checked value="True">ON<br>
                        <input type="radio" name="ntp" value="False">OFF</p>
                    <p><select size="1" name="tzone" required>
                       <option value="0">UTC 00:00</option>
                       <option value="1">UTC +01:00</option>
                       <option value="2">UTC +02:00</option>
                       <option value="3">UTC +03:00</option>
                       <option value="4">UTC +04:00</option>
                       <option value="5">UTC +05:00</option>
                       <option value="6">UTC +06:00</option>
                       </select></p>
                    <fieldset>
                        <legend>Setting time without an NTP server</legend>
                        <p><input type="date" name="date" required></p>
                        <p><input type="time" name="time" required></p>
                    </fieldset>
                    <p><input type="submit" value="Set Date&Time"></p>
                </fieldset>
            </form>"""
            
time_work_set = """<form action='admin' method='POST'>
                    <fieldset>
                        <legend>Setting the operating mode</legend>
                        <p><input type="radio" name="work_mode" value="contin">Continuous work<br>
                            <input type="radio" name="work_mode" value="schedule">On schedule<br>
                            <input type="radio" name="work_mode" checked value="onetime">One-time activation</p>
                        <p><input type="time" name="time_on" required><br>On time<br></p>
                        <p><input type="time" name="time_off" required><br>Off time<br></p>
                    <p><input type="submit" value="Set Time&Mode"></p>
                    </fieldset>
                </form>"""
                
debug_mode = """<form action='admin' method='POST'>
                    <fieldset>
                        <legend>Debug mode</legend>
                        <p><input type="radio" name="debug" value="True">ON<br>
                            <input type="radio" name="debug" checked value="False">OFF</p>
                        <p><input type="submit" value="Set Debug Mode"></p>
                    </fieldset>
                </form>"""
                
reset_control = """<form action='admin' method='POST'>
                    <fieldset>
                        <legend>Restarting the controller</legend>
                        <input type="hidden" name="reset" value="True">
                        <p><input type="submit" value="Restart"></p>
                    </fieldset>
                </form>"""

http_footer = """</body>
                <footer class="footer">
                    &copy; 2019, <a href="https://www.facebook.com/Syslighstar" target="_blank">SYSLIGHSTAR</a>
                </footer>
            </html>"""


# Выводим отладочные сообщения
def dprint(*args):
    if config['DEBUG']:
        print(*args)

# Шифруем пароль и логин
def setpasswd(login:str, passwd:str) -> str:
    return str(hexlify(sha256(str(passwd+login).encode()).digest()))

# Установка нового пароля администратора
def setroot(login:str, passw:str):
    dprint('Update root.txt file')
    passwd = setpasswd(login, passw)
    with open('root.txt', 'w') as f:    # Записываем новый пароль в файл
        f.write(passwd)
    with open('root.txt') as admin:
        root = admin.readline().rstrip() # Passwd для входа в ADMIN панель
    if root == passwd:
        gc.collect()                                                    # Очищаем RAM
        return True
    else:
        gc.collect()                                                    # Очищаем RAM
        return False

# Преобразуем строку в bool
def str_to_bool(s):
    if s == 'True':
         return True
    elif s == 'False':
         return False
    else:
         raise ValueError

# Рестарт контроллера
def reset_machine():
    reset()


# Читаем config.txt
def read_config():
    with open('config.txt', 'r') as f:
        return json.loads(f.read())

# Устанавливаем, обновляем дату и время
def datetime_update(ntp, data, ntime):
    dprint(config['RTC'].datetime())
    if str_to_bool(ntp):
        config['NTP_UPDATE'] = False
        config['RTC'].set_zone = config['TIMEZONE']
        config['RTC'].settime('ntp')
        config['NTP_UPDATE'] = True
        dprint('Setting time by NTP server...')
    elif not str_to_bool(ntp) and data and ntime:
        d = data.split('-')
        t = ntime.split(':')
        config['RTC'].datetime((int(d[0]), int(d[1]), int(d[2]), int(t[0]), int(t[1]), 0, 0, 0))
        dprint('Manual time setting...')

# Обновлем config.txt
def update_config(dbg=None, mode=None, ssid=None, pssw=None, tz=None, \
                    dts=None, tw=None, ton=None, toff=None, wall=None, 
                    wtab= None, otime=None):
    with open('config.txt', 'r') as f:
        conf = json.loads(f.read())
        gc.collect()                                                    # Очищаем RAM
    # Обновляем настройки полученные из файла config.txt
    conf['DEBUG'] = str_to_bool(dbg) if dbg else conf['DEBUG']
    config['DEBUG'] = str_to_bool(dbg) if dbg else conf['DEBUG']
    conf['MODE_WiFi'] = mode if mode else conf['MODE_WiFi']
    conf['ssid'] = ssid if ssid else conf['ssid']
    conf['wf_pass'] = pssw if pssw else conf['wf_pass']
    conf['timezone'] = int(tz) if tz else conf['timezone']
    config['TIMEZONE'] = int(tz) if tz else conf['timezone']
    conf['DST'] = str_to_bool(dts) if dts else conf['DST']
    config['DST'] = str_to_bool(dts) if dts else conf['DST']
    conf['T_WATER'] = tw if tw else conf['T_WATER']
    config['T_WATER'] = tw if tw else conf['T_WATER']
    conf['TIME_ON'] = ton if ton else conf['TIME_ON']
    config['TIME_ON'] = ton if ton else conf['TIME_ON']
    conf['TIME_OFF'] = toff if toff else conf['TIME_OFF']
    config['TIME_OFF'] = toff if toff else conf['TIME_OFF']
    conf['WORK_ALL'] = str_to_bool(wall) if wall else conf['WORK_ALL']
    config['WORK_ALL'] = str_to_bool(wall) if wall else conf['WORK_ALL']
    conf['WORK_TABLE'] = str_to_bool(wtab) if wtab else conf['WORK_TABLE']
    config['WORK_TABLE'] = str_to_bool(wtab) if wtab else conf['WORK_TABLE']
    conf['ONE-TIME'] = str_to_bool(otime) if otime else conf['ONE-TIME']
    config['ONE-TIME'] = str_to_bool(otime) if otime else conf['ONE-TIME']
    dprint('Update config.txt file\n', conf)
    gc.collect()                                                        # Очищаем RAM
    # Записываем новый файл config.txt
    with open('config.txt', 'w') as f:
       json.dump(conf, f)
    gc.collect()                                                        # Очищаем RAM


def require_auth(func):
    def auth(req, resp):
        auth = req.headers.get(b"Authorization")
        if not auth:
            yield from resp.awrite(
                'HTTP/1.0 401 NA\r\n'
                'WWW-Authenticate: Basic realm="Electric-Boiler-Control"\r\n'
                '\r\n')
            return
        auth = auth.split(None, 1)[1]
        auth = ubinascii.a2b_base64(auth).decode()
        req.username, req.passwd = auth.split(":", 1)
        with open('root.txt') as admin:
            root = admin.readline().rstrip() # Logim для входа в ADMIN панель
        if setpasswd(req.username.lower(), req.passwd) == root:
            yield from func(req, resp)
        else: # Обрабатываем не верный ввод пароля
            yield from picoweb.start_response(resp)
            yield from resp.awrite(http_head)
            yield from resp.awrite('{}{}{}'.format(div_cl_header, span_err_pasw, div_end))
            yield from resp.awrite(http_footer)
    return auth


@app.route('/')
@require_auth
def index(req, resp):
    gc.collect()                                                        # Очищаем RAM
    t = config['RTC_TIME']
    dts = 'ON' if config['DST'] == True else 'OFF'
    yield from picoweb.start_response(resp)
    yield from resp.awrite(http_head)
    yield from resp.awrite('{}{}<br><br>{}<br>{}'\
            .format(div_cl_header, href_adm_panel, href_contr_set, div_end))
    yield from resp.awrite(div_cl_info)
    if config['DEBUG']:
        yield from resp.awrite('<p>IP: {}</p>'.format(config['IP']))
    yield from resp.awrite('<p>{:0>2d}-{:0>2d}-{:0>2d} {:0>2d}:{:0>2d}</p>'\
                .format(t[0], t[1], t[2], t[3], t[4]))
    yield from resp.awrite('<p>Time zone: {}</p>'.format(config['TIMEZONE']))
    yield from resp.awrite('<p>DST: {}</p>'.format(dts))
    yield from resp.awrite('<p>Set: {:.2f}\'C</p>'.format(config['T_WATER']))
    yield from resp.awrite('<p>Room: {:.2f}\'C</p>'.format(config['TEMP']))
    yield from resp.awrite(div_end)
    yield from resp.awrite(http_footer)


@app.route('/admin')
@require_auth
def admin(req, resp):
    yield from picoweb.start_response(resp)
    yield from resp.awrite(http_head)
    yield from resp.awrite('{}{}<br><br>{}<br>{}'.format(div_cl_header, href_adm_panel, href_contr_set, div_end))
    if req.method == "POST":
        yield from req.read_form_data()
        form = req.form
        # Setting the operating mode
        if 'work_mode' and 'time_off' and 'time_on' in list(form.keys()):
            pass
            #update_config(ton=None, toff=None, wall=None, wtab= None, otime=None)
            #form['work_mode']
            #form['time_off']
            #form['time_on']
        # Setting WiFi
        elif 'wifi'and 'ssid'and 'pasw' in list(form.keys()):
            update_config(mode=form['wifi'], ssid=form['ssid'], pssw=form['pasw'])
            yield from resp.awrite('{}{}{}'.format(div_cl_info, 'Setting WiFi update', div_end))
        # Setting date and time
        elif 'ntp' and'time' and 'daylight' and 'date' and 'tzone' in list(form.keys()):
            update_config(tz=form['tzone'], dts=form['daylight'])
            datetime_update(form['ntp'], form['date'], form['time'])
            yield from resp.awrite('{}{}{}'.format(div_cl_info, 'Setting date and time update', div_end))
        # Chenge password
        elif 'login' and'repassw' and 'passw' in list(form.keys()):
            if form['passw'] == form['repassw']:
                if setroot(form['login'], form['passw']):
                    yield from resp.awrite('{}{}{}'.format(div_cl_info, 'Admin password update', div_end))
                else:
                    yield from resp.awrite('{}{}{}'.format(div_cl_info, 'Admin password not updata', div_end))
        # Debug mode
        elif 'debug' in list(form.keys()):
            update_config(dbg=form['debug'])
            yield from resp.awrite('{}{}{}'.format(div_cl_info, 'Debug mode update', div_end))
            yield from resp.awrite('{}{}{}'.format(div_cl_info, 'To apply the settings', div_end))
            yield from resp.awrite('{}{}{}'.format(div_cl_info, 'Reboot the controller', div_end))
        # Restarting the controller
        elif 'reset' in list(form.keys()):
            reset_machine()
    if req.method == "GET":
        yield from resp.awrite('{}{}{}<br>{}{}<br>{}<br>{}<br>{}<br>{}<br>{}{}'\
                    .format(div_cl_header, span_boler_adm, div_end, \
                    div_cl_admin, time_work_set, wifi_form, date_set, \
                    passw_form, debug_mode, reset_control, div_end))
    yield from resp.awrite(http_footer)
    gc.collect()                                                        # Очищаем RAM


@app.route('/read')
@require_auth
def read_set(req, resp):
    yield from picoweb.start_response(resp)
    yield from resp.awrite(http_head)
    yield from resp.awrite('{}{}<br><br>{}'\
            .format(div_cl_header, href_adm_panel, div_end))
    yield from resp.awrite('<div class="info">')
    conf = list(read_config().items())
    gc.collect()                                                        # Очищаем RAM
    for i in conf:
        on_off = 'ON' if i[1] == True else 'OFF'
        if i[0] == 'MODE_WiFi':
            yield from resp.awrite('<p>Wi-Fi Mode: {}</p>'.format(i[1]))
        if i[0] == 'ssid':
            yield from resp.awrite('<p>SSID: {}</p>'.format(i[1]))
        if i[0] == 'wf_pass':
            yield from resp.awrite('<p>Wi-Fi Passwd: {}</p>'.format(i[1]))
        if i[0] == 'T_WATER':
            yield from resp.awrite('<p>Water temp set: {}\'C</p>'.format(i[1]))
        if i[0] == 'DEBUG':
            yield from resp.awrite('<p>Debug mode: {}</p>'.format(on_off))
        if i[0] == 'timezone':
            yield from resp.awrite('<p>Time zone: {}</p>'.format(i[1]))
        if i[0] == 'DST':
            yield from resp.awrite('<p>Daylight saving time: {}</p>'.format(on_off))
        if i[0] == 'TIME_ON':
            yield from resp.awrite('<p>On time: {:0>2d}:{:0>2d}</p>'.format(i[1][3], i[1][4]))
        if i[0] == 'TIME_OFF':
            yield from resp.awrite('<p>Off time: {:0>2d}:{:0>2d}</p>'.format(i[1][3], i[1][4]))
        if i[0] == 'WORK_ALL':
            yield from resp.awrite('<p>Continuous work: {}</p>'.format(on_off))
        if i[0] == 'WORK_TABLE':
            yield from resp.awrite('<p>Scheduled operation: {}</p>'.format(on_off))
        if i[0] == 'ONE-TIME':
            yield from resp.awrite('<p>One-time activation: {}</p>'.format(on_off))
    yield from resp.awrite('</div>')
    yield from resp.awrite(http_footer)
    gc.collect()                                                        # Очищаем RAM


@app.route('/api/v1/temp')
@require_auth
def temp(req, resp):
    gc.collect()                                                        # Очищаем RAM
    if req.method == 'GET': # TEST curl -s -G -v http://192.168.0.16/api/v1/temp
        yield from picoweb.start_response(resp)
        yield from resp.awrite('{:.2f}'.format(config['TEMP']))
    elif req.method == 'POST': # TEST curl -s -X POST -v http://192.168.0.16/api/v1/temp?temp=56.60
        req.parse_qs()         # TEST curl -s -X POST -v http://192.168.0.16/api/v1/temp/300.60
        try:
            req_form = round(float(req.form['temp']), 2)
        except KeyError:
            req_form = 'Error'
        except ValueError:
            req_form = req.form['temp']
        yield from picoweb.start_response(resp)
        yield from resp.awrite('{}'.format(req_form))
