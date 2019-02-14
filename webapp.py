import picoweb, gc, ubinascii
from wificonnect import config
from ubinascii import hexlify
from uhashlib import sha256
gc.collect()                                                #Очищаем RAM

app = picoweb.WebApp(__name__)

http_head = """<!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width" initial-scale="1.0" maximum-scale="1.0" minimum-scale="1.0"/>
        <title>ESP8266 ADMIN</title>
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
        <h2><a class="menu" href="/">HOME</a></h2> """
        
http_footer = """
        </body>
        <footer class="footer">
        &copy; 2018, <a href="https://www.facebook.com/Syslighstar" target="_blank">SYSLIGHSTAR</a>
        </footer>
        </html> """


@app.route("/")
def index(req, resp):
    t = config['RTC_TIME']
    dts = 'ON' if config['DST'] == True else 'OFF'
    yield from picoweb.start_response(resp)
    yield from resp.awrite(http_head)
    yield from resp.awrite("""<div class="header">
                              <span>MAIN PARAMETERS</span></div>""")
    yield from resp.awrite('<div class="info">')
    if config['DEBUG']:
        yield from resp.awrite('<p>IP: %s </p>' %config['IP'])
    yield from resp.awrite('<p>{:0>2d}-{:0>2d}-{:0>2d} {:0>2d}:{:0>2d}</p>'.format(t[0], t[1], t[2], t[3], t[4]))
    yield from resp.awrite('<p>Time zone: {}</p>'.format(config['TIMEZONE']))
    yield from resp.awrite('<p>DST: {}</p>'.format(dts))
    yield from resp.awrite('<p>Set: {:.2f}\'C</p>'.format(config['T_WATER']))
    yield from resp.awrite('<p>Room: {:.2f}\'C</p>'.format(config['TEMP']))
    yield from resp.awrite('<p>Pressure: {}mmHg</p>'.format(config['PRESSURE']))
    yield from resp.awrite('<p>Humidity: {}%</p>'.format(config['HUMIDITY']))
    yield from resp.awrite('</div>')
    yield from resp.awrite(http_footer)
    
@app.route('/api/v1/temp') 
def temp(req, resp):
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
def temp(req, resp):
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
def temp(req, resp):
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

