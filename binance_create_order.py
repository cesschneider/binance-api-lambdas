import os, json, math
import boto3
from datetime import datetime
from secret_manager import get_secret
from binance_spot import *
from binance_margin import *
from binance_futures import *
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException


def lambda_handler(event, context):
    print(event)
    
    if 'detail' in event:
        print('event from EventBridge')
        params = event['detail']
    elif 'body' in event:
        print('event from API Gateway')
        params = json.loads(event['body'])
    else:
        params = event

    params['interval'] = str(params['interval'])
    
    secret_name = event['secret_name']
    secret = get_secret(secret_name)
    print('Secret ARN:', secret['ARN'])
    keys = json.loads(secret['SecretString'])

    client = Client(
        keys['BINANCE_API_KEY'], 
        keys['BINANCE_API_SECRET']
    )

    if 'PERP' in params['symbol']:
        params['symbol'] = str(params['symbol']).replace('PERP','')
    
    ticker = client.get_symbol_ticker(symbol=params['symbol'])
    print('Ticker: ', ticker)

    info = client.get_symbol_info(params['symbol'])
    print('Supported order types: ', info['orderTypes'])

    order = None
    try:
        if params['market'] == 'SPOT':
            if 'stopPricePercent' in event:
                results = create_oco_order(params, ticker, client)
                detailType = 'create_oco_order'
            else:
                results = create_order(params, ticker, client)
                detailType = 'create_order'

        elif params['market'] == 'MARGIN':
            results = create_margin_order(params, ticker, client)
            detailType = 'create_margin_order'

        elif params['market'] == 'FUTURES':
            results = create_futures_order(params, ticker, client)
            detailType = 'create_futures_order'

        params['orders'] = results
        params['exchange'] = 'BINANCE'
        params['price'] = ticker['price']
        params['timestamp'] = str(datetime.now())
        params['positionSide'] = params['positionSide'] if 'positionSide' in params else None
        params['clientOrderId'] = results['clientOrderId']

        client = boto3.client('events')
        response = client.put_events(Entries=[{ 
            'EventBusName': 'etrader',
            'Source': 'binance.orders', 
            'DetailType': detailType, 
            'Detail': json.dumps(params)
        }])
        print('put_events: ', response)
        
        return results
        
    except BinanceAPIException as e:
        # error handling goes here
        print(e)
        return str(e)
        #raise e
    except BinanceOrderException as e:
        # error handling goes here
        print(e)
        return str(e)
        #raise e
