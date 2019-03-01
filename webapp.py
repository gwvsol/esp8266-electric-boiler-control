import picoweb, gc, ubinascii, json
from wificonnect import config
from ubinascii import hexlify
from uhashlib import sha256
gc.collect()

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
href_adm_panel = '<a class="login" href="admin">ADMIN PANEL</a>'
div_cl_header = '<div class="header">'
div_cl_info = '<div class="info">'
div_cl_admin = '<div class = "admin">'
div_end = '</div>'
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
                       <option value="0">UTC +00:00</option>
                       <option value="1">UTC +01:00</option>
                       <option value="2">UTC +02:00</option>
                       <option value="3">UTC +03:00</option>
                       <option value="4">UTC +04:00</option>
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
                        <p>Temperature<br>
                        <input type="number" name="temp" size="4" min="30" max="65" step="5" value="40.0">'C</p>
                        <p><input type="radio" name="work_mode" value="contin">Continuous work<br>
                            <input type="radio" name="work_mode" value="schedule">On schedule<br>
                            <input type="radio" name="work_mode" checked value="onetime">One-time activation<br>
                            <input type="radio" name="work_mode" value="offall">Turn off heating boiler</p>
                        <p>Time<br>
                        <input type="time" name="time_on" required>On<br></p>
                        <p><input type="time" name="time_off" required>Off<br></p>
                    <p><input type="submit" value="Set Time&Mode"></p>
                    </fieldset>
                </form>"""
http_footer = """</body>
                <footer class="footer">
                    &copy; 2019, <a href="https://www.facebook.com/Syslighstar" target="_blank">SYSLIGHSTAR</a>
                </footer>
            </html>"""


def setpasswd(login:str, passwd:str) -> str:
    return str(hexlify(sha256(str(passwd+login).encode()).digest()))

def read_write_root(passwd=None):
    if passwd:
        with open('root.txt', 'w') as f:
            f.write(passwd)
    else:
        with open('root.txt') as f:
            return f.readline().rstrip()

def read_write_config(cfg=None):
    if cfg:
        with open('config.txt', 'w') as f:
            json.dump(cfg, f)
    else:
        with open('config.txt', 'r') as f:
            return json.loads(f.read())

def setroot(login:str, passw:str):
    passwd = setpasswd(login, passw)
    read_write_root(passwd=passw)
    if read_write_root() == passwd:
        return True
    else:
        return False

def str_to_bool(s):
    if s == 'True':
         return True
    elif s == 'False':
         return False
    else:
         raise ValueError

def bool_to_str(s):
    if s == True:
        return 'ON'
    elif s == False:
        return 'OFF'

def set_wall_wtab_otime(dvar, mode):
    if dvar == 'ON' or dvar == '1':
        if mode == 'wall':
            out = 'contin'
        elif mode == 'wtab':
            out = 'schedule'
        elif mode == 'otime':
            out = 'onetime'
    elif dvar == 'OFF' or dvar == '0':
        out = 'offall'
    gc.collect()
    return out

def datetime_update(ntp, data, ntime):
    if str_to_bool(ntp):
        config['NTP_UPDATE'] = False
        config['RTC'].set_zone = config['TIMEZONE']
        config['RTC'].settime('ntp')
        config['NTP_UPDATE'] = True
    elif not str_to_bool(ntp) and data and ntime:
        d = data.split('-')
        t = ntime.split(':')
        config['RTC'].datetime((int(d[0]), int(d[1]), int(d[2]), int(t[0]), int(t[1]), 0, 0, 0))
    gc.collect()

def update_config(mode=None, ssid=None, pssw=None, tz=None, \
                    dts=None, tw=None, ton=None, toff=None, wall=None, 
                    wtab= None, otime=None, rw=None):
    conf = read_write_config()
    if rw == 'w':
        conf['MODE_WiFi'] = mode if mode else conf['MODE_WiFi']
        conf['ssid'] = ssid if ssid else conf['ssid']
        conf['wf_pass'] = pssw if pssw else conf['wf_pass']
        conf['timezone'] = int(tz) if tz else conf['timezone']
        conf['DST'] = str_to_bool(dts) if dts else conf['DST']
        conf['T_WATER'] = tw if tw else conf['T_WATER']
        conf['TIME_ON'] = ton if ton else conf['TIME_ON']
        conf['TIME_OFF'] = toff if toff else conf['TIME_OFF']
        conf['WORK_ALL'] = str_to_bool(wall) if wall else conf['WORK_ALL']
        conf['WORK_TABLE'] = str_to_bool(wtab) if wtab else conf['WORK_TABLE']
        conf['ONE-TIME'] = str_to_bool(otime) if otime else conf['ONE-TIME']
        read_write_config(cfg=conf)
    config['DEBUG'] = conf['DEBUG']
    config['MODE_WiFi'] = conf['MODE_WiFi']
    config['ssid'] = conf['ssid']
    config['wf_pass'] = conf['wf_pass']
    config['TIMEZONE'] = conf['timezone']
    config['DST'] = conf['DST']
    config['T_WATER'] = conf['T_WATER']
    config['TIME_ON'] = conf['TIME_ON']
    config['TIME_OFF'] = conf['TIME_OFF']
    config['WORK_ALL'] = conf['WORK_ALL']
    config['WORK_TABLE'] = conf['WORK_TABLE']
    config['ONE-TIME'] = conf['ONE-TIME']
    config['DS_K'] = conf['DS_K']
    gc.collect()

def setting_update(timeon=None, timeoff=None, tempw=None, workmod=None):

    def on_off(tstr):
        t = tstr.split(':')
        if int(t[0]) >= 0 and int(t[0]) <= 23:
            if int(t[1]) >= 0 and int(t[1]) <= 59:
                out = (0, 0, 0, int(t[0]), int(t[1]), 0, 0, 0,)
            else: out = None
        else: out = None
        return out

    def twater(tempw):
        if float(tempw) >= 15.00 and float(tempw) <= 65.00:
            t = round(float(tempw), 1)
        else: t = None
        return t

    on = on_off(timeon) if timeon else None
    off = on_off(timeoff) if timeoff else None
    if workmod:
        wal = 'True' if workmod == 'contin' else 'False'
        wtb = 'True' if workmod == 'schedule' else 'False'
        wot = 'True' if workmod == 'onetime' else 'False'
        if workmod == 'offall':
            wal, wtb, wot = 'False', 'False', 'False'
    else:
        wal, wtb, wot = None, None, None
    t = twater(tempw) if tempw else None
    update_config(tw=t, ton=on, toff=off, wall=wal, wtab=wtb, otime=wot, rw='w')
    gc.collect()

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
        if setpasswd(req.username.lower(), req.passwd) == read_write_root():
            yield from func(req, resp)
        else:
            yield from picoweb.start_response(resp)
            yield from resp.awrite(http_head)
            yield from resp.awrite('{}{}{}'.format(div_cl_header, span_err_pasw, div_end))
            yield from resp.awrite(http_footer)
    return auth

@app.route('/')
def index(req, resp):
    t = config['RTC_TIME']
    ton = config['TIME_ON']
    toff = config['TIME_OFF']
    yield from picoweb.start_response(resp)
    yield from resp.awrite(http_head)
    yield from resp.awrite('{}{}<br>{}'\
            .format(div_cl_header, href_adm_panel, div_end))
    yield from resp.awrite(div_cl_info)
    yield from resp.awrite('<p>{:0>2d}-{:0>2d}-{:0>2d} {:0>2d}:{:0>2d}</p>'\
                .format(t[0], t[1], t[2], t[3], t[4]))
    yield from resp.awrite('<p>Time zone: {}</p>'.format(config['TIMEZONE']))
    yield from resp.awrite('<p>DST: {}</p>'.format(bool_to_str(config['DST'])))
    yield from resp.awrite('<p>Temp Set: {:.1f}\'C</p>'.format(config['T_WATER']))
    yield from resp.awrite('<p>Water temp: {:.1f}\'C</p>'.format(config['TEMP']))
    yield from resp.awrite('<p>Continuous work: {}</p>'.format(bool_to_str(config['WORK_ALL'])))
    yield from resp.awrite('<p>Scheduled operat: {}</p>'.format(bool_to_str(config['WORK_TABLE'])))
    yield from resp.awrite('<p>One-time activat: {}</p>'.format(bool_to_str(config['ONE-TIME'])))
    yield from resp.awrite('<p>On time: {:0>2d}:{:0>2d}</p>'.format(ton[3], ton[4]))
    yield from resp.awrite('<p>Off time: {:0>2d}:{:0>2d}</p>'.format(toff[3], toff[4]))
    yield from resp.awrite('<p>Actual power: {}%</p>'.format(str(int(config['PWM']/10))))
    yield from resp.awrite(div_end)
    yield from resp.awrite(http_footer)
    gc.collect()                                                        # Очищаем RAM

@app.route('/admin')
@require_auth
def admin(req, resp):
    yield from picoweb.start_response(resp)
    yield from resp.awrite(http_head)
    yield from resp.awrite('{}{}<br>{}'.format(div_cl_header, href_adm_panel, div_end))
    if req.method == "POST":
        yield from req.read_form_data()
        form = req.form
        if 'work_mode' and 'time_off' and 'time_on' and 'temp' in list(form.keys()):
            setting_update(form['time_on'], form['time_off'], form['temp'], form['work_mode'])
            yield from resp.awrite('{}{}{}'.format(div_cl_info, 'Setting the operating mode update', div_end))
        elif 'wifi'and 'ssid'and 'pasw' in list(form.keys()):
            update_config(mode=form['wifi'], ssid=form['ssid'], pssw=form['pasw'], rw='w')
            yield from resp.awrite('{}{}{}'.format(div_cl_info, 'Setting WiFi update', div_end))
        elif 'ntp' and'time' and 'daylight' and 'date' and 'tzone' in list(form.keys()):
            update_config(tz=form['tzone'], dts=form['daylight'], rw='w')
            datetime_update(form['ntp'], form['date'], form['time'])
            yield from resp.awrite('{}{}{}'.format(div_cl_info, 'Setting date and time update', div_end))
        elif 'login' and'repassw' and 'passw' in list(form.keys()):
            if form['passw'] == form['repassw'] and setroot(form['login'], form['passw']):
                yield from resp.awrite('{}{}{}'.format(div_cl_info, 'Admin password update', div_end))
            else:
                yield from resp.awrite('{}{}{}'.format(div_cl_info, 'Admin password not update', div_end))
        elif 'reset' in list(form.keys()):
            reset_machine()
    if req.method == "GET":
        yield from resp.awrite('{}{}<br>{}{}<br>{}<br>{}<br>{}<br>{}'\
                    .format(div_cl_header, div_end, \
                    div_cl_admin, time_work_set, wifi_form, date_set, \
                    passw_form, div_end))
    yield from resp.awrite(http_footer)
    gc.collect()                                                        # Очищаем RAM

@app.route('/api/v1/temp')
@require_auth
def temp(req, resp):
    if req.method == 'GET':
        yield from picoweb.start_response(resp)
        yield from resp.awrite('{:.2f}'.format(config['TEMP']))

@app.route('/api/v1/stemp')
@require_auth
def temp(req, resp):
    if req.method == 'GET':
        yield from picoweb.start_response(resp)
        yield from resp.awrite('{:.2f}'.format(config['T_WATER']))
    elif req.method == 'POST':
        req.parse_qs()
        try:
            t = req.form['stemp']
        except (ValueError, KeyError):
            t = None
        setting_update(tempw=t)

@app.route('/api/v1/wall')
@require_auth
def setwall(req, resp):
    if req.method == 'GET':
        out = bool_to_str(config['WORK_ALL'])
        yield from picoweb.start_response(resp)
        yield from resp.awrite(out)
    elif req.method == 'POST':
        req.parse_qs()
        try:
            wl = req.form['wall']
        except (ValueError, KeyError):
            wl = None
        setting_update(workmod=set_wall_wtab_otime(wl, 'wall'))

@app.route('/api/v1/wtab')
@require_auth
def setwtab(req, resp):
    if req.method == 'GET':
        out = bool_to_str(config['WORK_TABLE'])
        yield from picoweb.start_response(resp)
        yield from resp.awrite(out)
    elif req.method == 'POST':
        req.parse_qs()
        try:
            wt = req.form['wtab']
        except (ValueError, KeyError):
            wt = None
        setting_update(workmod=set_wall_wtab_otime(wt, 'wtab'))

@app.route('/api/v1/otime')
@require_auth
def setotime(req, resp):
    if req.method == 'GET':
        out = bool_to_str(config['ONE-TIME'])
        yield from picoweb.start_response(resp)
        yield from resp.awrite(out)
    elif req.method == 'POST':
        req.parse_qs()
        try:
            ot = req.form['otime']
        except (ValueError, KeyError):
            ot = None
        setting_update(workmod=set_wall_wtab_otime(ot, 'otime'))

@app.route('/api/v1/timeon')
@require_auth
def settimeon(req, resp):
    if req.method == 'GET':
        ton = config['TIME_ON']
        yield from picoweb.start_response(resp)
        yield from resp.awrite('{:0>2d}:{:0>2d}'.format(ton[3], ton[4]))
    elif req.method == 'POST':
        req.parse_qs()
        try:
            tOn = req.form['timeon']
        except (ValueError, KeyError):
            tOn = None
        setting_update(timeon=tOn)

@app.route('/api/v1/timeoff')
@require_auth
def settimeoff(req, resp):
    if req.method == 'GET':
        toff = config['TIME_OFF']
        yield from picoweb.start_response(resp)
        yield from resp.awrite('{:0>2d}:{:0>2d}'.format(toff[3], toff[4]))
    elif req.method == 'POST': 
        req.parse_qs()
        try:
            tOff = req.form['timeoff']
        except (ValueError, KeyError):
            tOff = None
        setting_update(timeoff=tOff)

@app.route('/api/v1/power')
@require_auth
def power(req, resp):
    if req.method == 'GET':
        yield from picoweb.start_response(resp)
        yield from resp.awrite('{}'.format(config['PWM']))
