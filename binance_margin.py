from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException

        
def create_margin_order(event, ticker, client):
    print('Creating margin order')
    try:
        order = client.create_margin_order(
            symbol=event['symbol'],
            side=event['side'],
            type=event['type'],
            timeInForce=TIME_IN_FORCE_GTC,
            quantity=event['quantity'],
            price=ticker['price']
        )
        print(order)
        return order
    except BinanceAPIException as e:
        raise e
    except BinanceOrderException as e:
        raise e

