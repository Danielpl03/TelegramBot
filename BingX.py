from datetime import datetime
import hmac
import time
import ccxt
import numpy as np
import pandas as pd 
import requests
import ta
import enum
import ta.momentum
from hashlib import sha256

APIURL = "https://open-api.bingx.com"
APIKEY = "rK86ktddkk4G42pNAwp92imFkzXcdbjhUXGXR881LH557JlseAEeeJs8YfmsWyR6dZQ7HNF3lvvFznf5i7g"
SECRETKEY = "PHbPnbqfJkpuDqfziP3uxV0s9wwZJFuHQRV9ynKTk3xUSJM0ErZlO81nLW5F8o6lfjvMqdz1pO5uKiOrqfKw"
PATH_PRECIOS = 'C:\D\Estudios\Trading\Datos historicos\preciosBingX.csv'

class ohlcv(enum.Enum):
    TIMESTAMP : int = 0
    OPEN : int= 1
    HIGH : int = 2
    LOW : int = 3
    CLOSE : int = 4
    VOLUME : int = 5

class direction(enum.Enum):
    BUY: 0
    SELL: 1

exchange = ccxt.bingx({
    'enableRateLimit': True,
    'apiKey': APIKEY,
    'secret': SECRETKEY,
    'options':{
        'defaultType': 'swap'
    }
 })











class Symbol:
    symbol: str
    price: float

    def __init__(self, symbol):
        self.price = getPrice
        self.symbol = symbol

    def getSymbol(self):
        return self.symbol

    def getPrecio(self):
        self.price = obtener_precio_crypto(symbol=self.symbol)
        return self.price

class Trade:
    symbol: Symbol
    openPrice: float
    currentPrice: float
    direction: int
    amount: float
    timestamp: datetime

    def __init__(self, symbol, openPrice, direction, amount):
        self.symbol = symbol
        self.openPrice = openPrice
        self.direction = direction
        self.amount = amount

    
class Response:
    code: str
    msg: str
    data: Symbol


msec = 1000
minute = 60 * msec
hour = 60 * minute
url = "https://open-api.bingx.com/openApi/swap/"

now = exchange.milliseconds()

def obtener_precio_crypto(symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        precio = ticker['close']
        return precio
    except ccxt.BaseError as error:
        print(f"Se produjo un error al obtener el precio de {symbol}: {error}")

def obtener_precios_limit(symbol, timeframe, length):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=length)
        return ohlcv
    except ccxt.BaseError as error:
        print(f"Se produjo un error al obtener los precios de cierre: {error}")

def obtener_precios_since(symbol, timeframe, since):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
        return ohlcv
    except ccxt.BaseError as error:
        print(f"Se produjo un error al obtener los precios de cierre: {error}")



def obtener_Precios(symbol, timeframe, length, source):
    precios = obtener_precios_limit(symbol, timeframe, length)
    if precios:
        preciosSrc = [precio[source] for precio in precios]
        return preciosSrc

def rsi(symbol, timeframe, length, source):
    preciosSrc = obtener_Precios(symbol, timeframe, length, source)
    df = pd.DataFrame(preciosSrc, columns=[source])
    rsi = ta.momentum.rsi(close=df[source], window=7, fillna=False)
    df.insert(1, 'RSI', [round(r,2) for r in rsi])
    return df

def calcular_rsi(preciosSrc, source):
    df = pd.DataFrame(preciosSrc, columns=[source])
    rsi = ta.momentum.rsi(close=df[source], window=7, fillna=False)
    df.insert(1, 'RSI', [round(r,2) for r in rsi])
    return df
    

def getPrice(symbol, timestamp):
    urls = url + "v1/ticker/price?timestamp=" + str(timestamp) + "&symbol=" + symbol

    response = requests.get(urls)
    data = response.json()
    ticker = data['data']
    return [ticker['symbol'],ticker['price']]


### Leer y guardar datos historicos
def obtenerPreciosNuevos(symbol, timeframe, since):
    header = [d for d in ohlcv.__members__] 
    df = pd.DataFrame(obtener_precios_since(symbol, timeframe, since), columns= header)
    if(df.empty):
        return None
    else:
        # Guardar los nuevos precios
        df.insert(1, 'Local_Time', [datetime.fromtimestamp(d/1000) for d in df[ohlcv.TIMESTAMP.name]])
        df.drop(df.index[0], inplace=True)
        df.drop(df.index[-1], inplace=True)
        return df


def guardarPrecios(symbol, timeframe, df):
    if df is None:
        since = exchange.parse8601('2024-05-01 00:00:00')
    else:
        since = obtenerUltimaFechaDePrecios(df)
        df = df.drop('RSI', axis=1)
    dfN = obtenerPreciosNuevos(symbol, timeframe, since=since)
    if dfN is None:
        return None
    else:
        if df is not None:
            dfN: pd.DataFrame = pd.concat([df, dfN])
        dfN.insert(7, 'RSI', calcular_rsi(dfN, ohlcv.CLOSE.name)['RSI'])
        dfN.to_csv(PATH_PRECIOS, index=False)
    
def obtenerUltimaFechaDePrecios(df):
    return df[ohlcv.TIMESTAMP.name].iloc[-1]

def readPrecios() -> pd.DataFrame | None: 
    try:
        df = pd.read_csv(PATH_PRECIOS)
        return df
    except FileNotFoundError | PermissionError:
        return None


### Documentacion ###
def get_sign(api_secret, payload):
    signature = hmac.new(api_secret.encode("utf-8"), payload.encode("utf-8"), digestmod=sha256).hexdigest()
    print("sign=" + signature)
    return signature


def getServerTime():
    return requests.request(method="GET", url="https://open-api.bingx.com/openApi/swap/v2/server/time").json().get('data').get('serverTime')

def send_request(method, path, urlpa, payload):
    url = "%s%s?%s&signature=%s" % (APIURL, path, urlpa, get_sign(SECRETKEY, urlpa))
    print(url)
    headers = {
        'X-BX-APIKEY': APIKEY,
    }
    response = requests.request(method, url, headers=headers, data=payload)
    return response

def obtenerBalance():
    urlpa = "timestamp="+str(getServerTime())
    path = '/openApi/swap/v2/user/balance'
    method = 'GET'
    response = send_request(method, path, urlpa, {})
    return response

def revisarCompra():
    if df['RSI'].iloc[-1] > df['RSI'].iloc[-2]:
        """>>> Revisando si se comprará o  no"""

def revisarVenta():
    if df['RSI'].iloc[-1] < df['RSI'].iloc[-2]:
        """>>> Revisando si se vendera o  no"""


def revisarRsi(df):
    print(df['RSI'].iloc[-1])
    if df['RSI'].iloc[-1] >= 70:
        return  'overbought'
    elif df['RSI'].iloc[-1] <= 30:
        return 'oversold'
    


if __name__ == '__main__':

    print(obtener_precio_crypto("BTCU-USDT"))
    # df = readPrecios()
    # guardarPrecios('BTC-USDT', '15m', df)
    # df = readPrecios()
    # print(revisarRsi(df))
    # while True:
    #     df = readPrecios()
    #     print(revisarRsi(df))
    #     lastPriceDate = obtenerUltimaFechaDePrecios(df)
    #     horaActual = getServerTime()
    #     nextClose = (lastPriceDate + 1800000) - horaActual
    #     print('El robot se detendrá por ', (nextClose/1000) , " seg. Se reanudara ", datetime.fromtimestamp( (horaActual+nextClose)/1000) )
    #     time.sleep(nextClose / 1000) #Esperamos hasta el proximo cierre de vela

    # print(nextClose, "   ", datetime.fromtimestamp( (getServerTime() + nextClose) /1000) )


# print(obtenerBalance().json().get('data').get('balance').get('balance'))

# print(ohlcv.CLOSE.name)

# print(obtenerPreciosNuevos('BTC-USDT', '15m', 1714538700000))

# guardarPrecios('BTC-USDT', '15m')


# print(obtener_precios_since('BTC-USDT','15m', 1714610700000))

# guardarPrecios('BTC-USDT', '15m')

# rsi = calcular_rsi('BTC-USDT', '15m', 8, ohlcv.CLOSE)
# print(rsi)

# for r in rsi['RSI']:
#     if(float(r) > 70):
#         lastTrade = "venta"
#         break
#     elif(float(r) < 30):
#         lastTrade = "compra"
#         break

# while(True):
#     print(lastTrade)
#     break 



# print(getPrice("BTC-USDT", now))
# print(f"El precio de Bitcoin Futures es: {obtener_precio_crypto('BTC-USDT')}")
