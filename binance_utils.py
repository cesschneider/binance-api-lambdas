import math
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException

def get_tick_and_step_size(symbol, client):
    tick_size = None
    step_size = None
    symbol_info = client.get_symbol_info(symbol)
    for filt in symbol_info['filters']:
        if filt['filterType'] == 'PRICE_FILTER':
            tick_size = float(filt['tickSize'])
        elif filt['filterType'] == 'LOT_SIZE':
            step_size = float(filt['stepSize'])
    return tick_size, step_size
    
def float_precision(f, n):
    n = int(math.log10(1 / float(n)))
    f = math.floor(float(f) * 10 ** n) / 10 ** n
    f = "{:0.0{}f}".format(float(f), n)
    return str(int(f)) if int(n) == 0 else f
    
def order_market_buy(client, symbol, quantity):
    tick_size, step_size = get_tick_and_step_size(symbol)
    order = client.order_market_buy(symbol=symbol, quantity=float_precision(quantity, step_size))
    return order
    
def get_precise_quantity(client):
    info = client.futures_exchange_info()
    symbols_n_precision = []
    #print('futures_exchange_info: ', info)
    for item in info['symbols']: 
        symbols_n_precision[item['symbol']] = item['quantityPrecision'] # not really necessary but here we are...
