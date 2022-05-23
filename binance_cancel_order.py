
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

    secret_name = "binance/api/cesschneider"
    secret = get_secret(secret_name)
    print('Secret ARN:', secret['ARN'])
    keys = json.loads(secret['SecretString'])
    client = Client(
        keys['BINANCE_API_KEY'], 
        keys['BINANCE_API_SECRET']
    )

    try:
        response = client.futures_cancel_order(**params)
        #response = client.futures_cancel_order(**params)
        #orderIdList
        print('response:', response)

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
