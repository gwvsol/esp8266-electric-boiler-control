import picoweb, gc, ubinascii, os, json
from wificonnect import config
gc.collect()                                                # Очищаем RAM
from ubinascii import hexlify
from uhashlib import sha256
gc.collect()                                                # Очищаем RAM


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

err_pasw = """<div class="header"><span>Error Login<br>
            Close the browser, restart it,<br>
            and then try to log in again</span></div>"""

div_first = '<div class="header"><span>'
div_end = '</span></div>'

err_req = 'The request is not supported'
err_method = 'Method is not supported'
set_update = 'settings have been updated'

http_footer = """</body>
            <footer class="footer">
            &copy; 2018, <a href="https://www.facebook.com/Syslighstar" target="_blank">SYSLIGHSTAR</a>
            </footer>
            </html>"""


# Выводим отладочные сообщения
def dprint(*args):
    if config['DEBUG']:
        print(*args)


# Шифруем пароль и логин
def setpasswd(login:str, passwd:str) -> str:
    return str(hexlify(sha256(str(passwd+login).encode()).digest()))


# Читаем config.txt
def read_config():
    with open('config.txt', 'r') as f:
        return json.loads(f.read())


# Обновлем config.txt
def update_config(dbg=None, mode=None, ssid=None, pssw=None, tz=None, dts=None, tw=None):
    with open('config.txt', 'r') as f:
        conf = json.loads(f.read())
        gc.collect()                                                # Очищаем RAM
    # Обновляем настройки полученные из файла config.txt
    conf['DEBUG'] = dbg if dbg else conf['DEBUG']
    conf['MODE_WiFi'] = mode if mode else conf['MODE_WiFi']
    conf['ssid'] = ssid if ssid else conf['ssid']   
    conf['wf_pass'] = pssw if pssw else conf['wf_pass']
    conf['timezone'] = tz if tz else conf['timezone']
    conf['DST'] = dts if dts else conf['DST']
    conf['T_WATER'] = tw if tw else conf['T_WATER']
    dprint('Update config.txt file\n', conf)
    gc.collect()                                                    # Очищаем RAM
    # Записываем новый файл config.txt
    with open('config.txt', 'w') as f:
       json.dump(conf, f)
    gc.collect()                                                    # Очищаем RAM


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
        if setpasswd(req.username.lower(), req.passwd.lower()) == root:
            yield from func(req, resp)
        else: # Обрабатываем не верный ввод пароля
            yield from picoweb.start_response(resp)
            yield from resp.awrite(http_head)
            yield from resp.awrite(err_pasw)
            yield from resp.awrite(http_footer)
    return auth


@app.route('/')
@require_auth
def index(req, resp):
    gc.collect()                                                # Очищаем RAM
    t = config['RTC_TIME']
    dts = 'ON' if config['DST'] == True else 'OFF'
    yield from picoweb.start_response(resp)
    yield from resp.awrite(http_head)
    yield from resp.awrite("""<div class="header">
                              <a class="login" href="admin">ADMIN PANEL</a><br><br>
                              <a class="login" href="read">CONTROLLER SETTINGS</a><br><br>
                              <span>MAIN PARAMETERS</span></div>""")
    yield from resp.awrite('<div class="info">')
    if config['DEBUG']:
        yield from resp.awrite('<p>IP: {}</p>'.format(config['IP']))
    yield from resp.awrite('<p>{:0>2d}-{:0>2d}-{:0>2d} {:0>2d}:{:0>2d}</p>'.format(t[0], t[1], t[2], t[3], t[4]))
    yield from resp.awrite('<p>Time zone: {}</p>'.format(config['TIMEZONE']))
    yield from resp.awrite('<p>DST: {}</p>'.format(dts))
    yield from resp.awrite('<p>Set: {:.2f}\'C</p>'.format(config['T_WATER']))
    yield from resp.awrite('<p>Room: {:.2f}\'C</p>'.format(config['TEMP']))
    yield from resp.awrite('<p>Pressure: {}mmHg</p>'.format(config['PRESSURE']))
    yield from resp.awrite('<p>Humidity: {}%</p>'.format(config['HUMIDITY']))
    yield from resp.awrite('</div>')
    yield from resp.awrite(http_footer)


@app.route('/wifi')
@require_auth
def wifiset(req, resp):
    gc.collect()                                                # Очищаем RAM
    yield from picoweb.start_response(resp)
    yield from resp.awrite(http_head)
    gc.collect()                                                # Очищаем RAM
    if req.method == "POST":
        yield from req.read_form_data()
        update_config(mode=req.form['wifi'], ssid=req.form['ssid'], pssw=req.form['pasw'])
        gc.collect()                                                    # Очищаем RAM
        yield from resp.awrite('{}{}{}{}'.format(div_first, 'Wi-Fi ', set_update, div_end))
    else:
        yield from resp.awrite('{}{}{}'.format(div_first, err_method, div_end))
    yield from resp.awrite(http_footer)
    gc.collect()                                                        # Очищаем RAM


@app.route('/admin')
@require_auth
def admin(req, resp):
    yield from picoweb.start_response(resp)
    yield from resp.awrite(http_head)
    yield from resp.awrite("""<div class="header">
                          <a class="login" href="read">CONTROLLER SETTINGS</a><br></div>""")
    yield from resp.awrite("""
    <div class="header"><span>Boiler Control Admin</span></div>
    <br>
    <div class = "admin">
        <form action='wifi' method='POST'>
        <fieldset>
            <legend>Setting WiFi</legend>
            <p><input type="radio" name="wifi" value="AP">AP<br>
               <input type="radio" name="wifi" value="ST" checked>STATION</p>
            <p><input type="text" name="ssid" placeholder="SSID" required autocomplete="off"></p>
            <p><input type="password" name="pasw" pattern=".{8,12}" required title="8 to 12 characters" placeholder="WiFi Password" required autocomplete="off"></p>
            <p><input type="submit" value="Set WiFi"></p>
        </fieldset>
        </form>
    <br>
        <form action='passw-set' method='POST'>
            <fieldset>
                <legend>Chenge password</legend>
                <p><input type="text" name="login" required placeholder="Login" autocomplete="off"></p>
                <p><input type="password" name="passw" pattern=".{8,12}" required title="8 to 12 characters" required placeholder="Password" autocomplete="off"></p>
                <p><input type="password" name="repassw" pattern=".{8,12}" required title="8 to 12 characters" required placeholder="Repeat Password" autocomplete="off"></p>
                <p><input type="submit" value="Сhange password"></p>
            </fieldset>
        </form>
    </div>""")


@app.route('/read')
@require_auth
def read_set(req, resp):
    yield from picoweb.start_response(resp)
    yield from resp.awrite(http_head)
    yield from resp.awrite("""<div class="header">
                              <a class="login" href="admin">ADMIN PANEL</a><br><br>
                              <span>CONTROLLER SETTINGS</span></div>""")
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
            yield from resp.awrite('<p>Water temp set: {}</p>'.format(i[1]))
        if i[0] == 'DEBUG':
            yield from resp.awrite('<p>Debug mode: {}</p>'.format(on_off))
        if i[0] == 'timezone':
            yield from resp.awrite('<p>Time zone: {}</p>'.format(i[1]))
        if i[0] == 'DST':
            yield from resp.awrite('<p>Daylight saving time: {}</p>'.format(on_off))
    yield from resp.awrite('</div>')
    yield from resp.awrite(http_footer)
    gc.collect()                                                        # Очищаем RAM


@app.route('/api/v1/temp')
@require_auth
def temp(req, resp):
    gc.collect()                                                # Очищаем RAM
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


@app.route('/api/v1/pres')
@require_auth 
def pres(req, resp):
    gc.collect()                                                # Очищаем RAM
    if req.method == 'GET': # TEST curl -s -G -v http://192.168.0.16/api/v1/pres
        yield from picoweb.start_response(resp)
        yield from resp.awrite('{}'.format(config['PRESSURE']))
    elif req.method == 'POST': # TEST curl -s -X POST -v http://192.168.0.16/api/v1/pres?pres=567.60
        req.parse_qs()         # TEST curl -s -X POST -v http://192.168.0.16/api/v1/pres/300.60
        try:
            req_form = round(float(req.form['pres']), 2)
        except KeyError:
            req_form = 'Error'
        except ValueError:
            req_form = req.form['pres']
        yield from picoweb.start_response(resp)
        yield from resp.awrite('{}'.format(req_form))


@app.route('/api/v1/hum')
@require_auth
def hum(req, resp):
    gc.collect()                                                # Очищаем RAM
    if req.method == 'GET': # TEST curl -s -G -v http://192.168.0.16/api/v1/hum
        yield from picoweb.start_response(resp)
        yield from resp.awrite('{}'.format(config['HUMIDITY']))
    elif req.method == 'POST': # TEST curl -s -X POST -v http://192.168.0.16/api/v1/hum?pres=300.60
        req.parse_qs()         # TEST curl -s -X POST -v http://192.168.0.16/api/v1/hum/300.60
        try:
            req_form = round(float(req.form['hum']), 2)
        except KeyError:
            req_form = 'Error'
        except ValueError:
            req_form = req.form['hum']
        yield from picoweb.start_response(resp)
        yield from resp.awrite('{}'.format(req_form))

