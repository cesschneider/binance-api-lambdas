import os, json, math
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException


def create_oco_order(event, ticker, client):
    print('Creating OCO order')

    ticker['price'] = float(ticker['price'])
    event['stopPricePercent'] = float(event['stopPricePercent']) / 100

    # Price Restrictions:
    # SELL: Limit Price > Last Price > Stop Price
    # BUY: Limit Price < Last Price < Stop Price

    if event['side'] == 'BUY':
        stopPrice = ticker['price'] + (ticker['price'] * event['stopPricePercent'])
    elif event['side'] == 'SELL':
        stopPrice = ticker['price'] + (ticker['price'] * event['stopPricePercent'])

    # 38544.55000000
    stopPrice = format(int(stopPrice), '.8f')
    print('stopPrice: ', stopPrice)

    try:
        order = client.create_oco_order(
            symbol=event['symbol'],
            side=event['side'],
            quantity=event['quantity'],
            price=ticker['price'],
            stopPrice=stopPrice,
            stopLimitPrice=stopPrice,
            stopLimitTimeInForce='GTC'
        )
        print(order)
        return order
    except BinanceAPIException as e:
        raise e
    except BinanceOrderException as e:
        raise e
        
def create_order(event, ticker, client):
    print('Creating spot order')
    try:
        order = client.create_order(
            symbol=event['symbol'],
            side=event['side'],
            type=event['type'],
            timeInForce='GTC',
            quantity=event['quantity'],
            price=ticker['price']
        )
        print(order)
        return order
    except BinanceAPIException as e:
        raise e
    except BinanceOrderException as e:
        raise e
