import os, json, math
import boto3
from datetime import datetime
from secret_manager import get_secret
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException


def lambda_handler(event, context):
    print('event:', event)

    # event comes from EventBridge
    if 'detail' in event:
        params = event['detail']
    # event comes from API Gateway
    elif 'body' in event:
        params = json.loads(event['body'])
    else:
        params = event
    
    print('params:', params)

    secret_name = event['secret_name']
    secret = get_secret(secret_name)
    print('Secret ARN:', secret['ARN'])
    keys = json.loads(secret['SecretString'])
    client = Client(
        keys['BINANCE_API_KEY'], 
        keys['BINANCE_API_SECRET']
    )

    try:
        '''
            An additional parameter, recvWindow, may be sent to specify the number of milliseconds after timestamp the request is valid for. 
            If recvWindow is not sent, it defaults to 5000.
            Serious trading is about timing. Networks can be unstable and unreliable, which can lead to requests taking varying amounts of time to reach the servers. 
            With recvWindow, you can specify that the request must be processed within a certain number of milliseconds or be rejected by the server.
             It is recommended to use a small recvWindow of 5000 or less!
        '''
        if 'origClientOrderId' in params or 'orderId' in params:
            '''
            Name	Type	Mandatory	Description
            symbol	STRING	YES	
            orderId	LONG	NO	
            origClientOrderId	STRING	NO	
            recvWindow	LONG	NO	
            timestamp	LONG	YES	        
            '''
            print('futures_get_order')
            response = client.futures_get_order(**params)

        elif 'symbol' in params: # and 'startTime' in params:
            '''
            symbol	STRING	YES	
            orderId	LONG	NO	
            startTime	LONG	NO	
            endTime	LONG	NO	
            limit	INT	NO	Default 500; max 1000.
            recvWindow	LONG	NO	
            timestamp	LONG	YES	        
            '''
            print('futures_get_all_orders')
            response = client.futures_get_all_orders(**params)
            print('Found {} orders'.format(len(response)))

        else:
            '''
            symbol	STRING	NO	
            recvWindow	LONG	NO	
            timestamp	LONG	YES	
            '''
            print('futures_get_open_orders')
            response = client.futures_get_open_orders(**params)
            print('Found {} orders'.format(len(response)))


        return response

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

