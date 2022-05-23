import os, json, math, uuid
from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException, BinanceOrderException
from binance.helpers import round_step_size
from binance_utils import float_precision

def get_min_quant(client, symbol):
    info = client.futures_exchange_info()
    for item in info['symbols']:
        if(item['symbol'] == symbol):
            for f in item['filters']:
                if f['filterType'] == 'LOT_SIZE':
                
                    return f['minQty']

def get_precise_quantity(event, client):
    symbol_info = client.get_symbol_info(event['symbol'])
    step_size = 0.0
    for f in symbol_info['filters']:
      if f['filterType'] == 'LOT_SIZE':
        step_size = float(f['stepSize'])
    
    precision = int(round(-math.log(step_size, 10), 0))
    quantity = float(round(event['quantity'], precision))

    return quantity

def create_futures_order(event, ticker, client):
    ticker['price'] = float(ticker['price'])
    symbol_info = client.get_symbol_info(event['symbol'])
    print('symbol_info:', symbol_info)

    stopPricePrecision = '.{}f'.format(2)
    print('stopPricePrecision:', stopPricePrecision)

    stopLossPercent = event['stopLossPercent'] if 'stopLossPercent' in event else '2.5'
    stopLossPercent = float(stopLossPercent) / 100

    if event['side'] == 'BUY':
        stopLossPrice = ticker['price'] - (ticker['price'] * stopLossPercent)
    if event['side'] == 'SELL':
        stopLossPrice = ticker['price'] + (ticker['price'] * stopLossPercent)

    stopLossPrice = format(stopLossPrice, stopPricePrecision)
    print('stopLossPrice:', stopLossPrice)

    activationPricePercent = event['activationPricePercent'] if 'activationPricePercent' in event else '1.0'
    activationPricePercent = float(activationPricePercent) / 100

    if 'callbackRate' not in event:
        event['callbackRate'] = 1.0
    event['callbackRate'] = float(event['callbackRate'])

    if 'positionSide' not in event:
        event['positionSide'] = 'BOTH'
    

    '''
    trade_size_in_dollars = 100
    order_amount = trade_size_in_dollars / ticker['price'] # size of order in BTC
    precision = 3 # info['symbols'][0]['quantityPrecision'] # the binance-required level of precision for BTC
    precise_order_amount = "{:0.0{}f}".format(order_amount, precision) # string of precise order amount that can be used when creating order
    print('precise_order_amount: ', precise_order_amount)
    '''
    
    '''
     symbol_info: {'symbol': 'AXSUSDT', 'status': 'TRADING', 'baseAsset': 'AXS', 
    'baseAssetPrecision': 8, 'quoteAsset': 'USDT', 'quotePrecision': 8, 'quoteAssetPrecision': 8, 'baseCommissionPrecision': 8, 'quoteCommissionPrecision': 8, 
    'icebergAllowed': True, 'ocoAllowed': True, 'quoteOrderQtyMarketAllowed': True, 'allowTrailingStop': False, 'isSpotTradingAllowed': True, 'isMarginTradingAllowed': True, 
    'orderTypes': ['LIMIT', 'LIMIT_MAKER', 'MARKET', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT'], 
    'permissions': ['SPOT', 'MARGIN']},
    'filters': [
        {'filterType': 'PRICE_FILTER', 'minPrice': '0.01000000', 'maxPrice': '1000.00000000', 'tickSize': '0.01000000'}, 
        {'filterType': 'PERCENT_PRICE', 'multiplierUp': '5', 'multiplierDown': '0.2', 'avgPriceMins': 5}, 
        {'filterType': 'LOT_SIZE', 'minQty': '0.01000000', 'maxQty': '900000.00000000', 'stepSize': '0.01000000'}, 
        {'filterType': 'MIN_NOTIONAL', 'minNotional': '10.00000000', 'applyToMarket': True, 'avgPriceMins': 5}, 
        {'filterType': 'ICEBERG_PARTS', 'limit': 10}, 
        {'filterType': 'MARKET_LOT_SIZE', 'minQty': '0.00000000', 'maxQty': '35798.87379861', 'stepSize': '0.00000000'}, 
        {'filterType': 'TRAILING_DELTA', 'minTrailingAboveDelta': 10, 'maxTrailingAboveDelta': 2000, 'minTrailingBelowDelta': 10, 'maxTrailingBelowDelta': 2000}, 
        {'filterType': 'MAX_NUM_ORDERS', 'maxNumOrders': 200}, 
        {'filterType': 'MAX_NUM_ALGO_ORDERS', 'maxNumAlgoOrders': 5}
    ]
    '''

    #print('symbol_info[filters]', symbol_info['filters'])
    #tick_size, step_size = get_tick_and_step_size(symbol)

    for f in symbol_info['filters']:
      if f['filterType'] == 'LOT_SIZE':
        step_size = float(f['stepSize'])
      if f['filterType'] == 'PRICE_FILTER':
        tick_size = float(f['tickSize'])
        
    print('step_size:', float(step_size))
    print('tick_size:', float(tick_size))
    
    quantity = event['quantity']
    calc_precision = int(round(-math.log(step_size, 10), 0))
    print('calc_precision:', calc_precision)
    quantity = get_precise_quantity(event, client)
    print('get_precise_quantity: ', quantity)
    min_quant = get_min_quant(client, event['symbol'])
    print('min_quant:', min_quant)
    quantity = float_precision(quantity, step_size)
    print('float_precision:', quantity)
    #tick = get_ticksize(cur)
    #price = round_step_size(float(price), float(tick))
    #print('round_step_size price:', price)

    order = None
    '''
    A unique id among open orders. Automatically generated if not sent. Can only be string following the rule: ^[\.A-Z\:/a-z0-9_-]{1,36}$
    '''
    orderId = str(uuid.uuid4())
    newClientOrderId = orderId.split('-')[0] + orderId.split('-')[1] + orderId.split('-')[2] + orderId.split('-')[3] +'_'+ event['interval']
    print('newClientOrderId:', newClientOrderId)

    results = {}
    results['price'] = ticker['price']
    results['positionSide'] = event['positionSide']
    results['clientOrderId'] = newClientOrderId

    try:
        if event['type'] == 'MARKET':
            marketOrder = client.futures_create_order(
                symbol=event['symbol'], 
                side=event['side'], 
                type=event['type'], 
                positionSide=event['positionSide'], 
                quantity=quantity,
                newClientOrderId=newClientOrderId
            )
            print('MARKET:', marketOrder)
            results['MARKET'] = marketOrder

            if event['side'] == 'BUY':
                stopLossPrice = ticker['price'] - (ticker['price'] * stopLossPercent)
                stopLossPrice = format(stopLossPrice, stopPricePrecision)
                print('long stopLossPrice: ', stopLossPrice)
            
                stopLongOrder = client.futures_create_order(
                    symbol=event['symbol'], 
                    side='SELL', 
                    type='STOP_MARKET', 
                    positionSide='BOTH',
                    timeInForce='GTC',
                    #quantity=float_precision(float(quantity)/2.0, step_size),
                    closePosition=True,
                    stopPrice=stopLossPrice,
                    newClientOrderId=newClientOrderId
                )
                print('STOP_LONG:', stopLongOrder)
                results['STOP_LONG'] = stopLongOrder
                '''
                trailingStopOrder = client.futures_create_order(
                    symbol=event['symbol'], 
                    side='SELL', 
                    type='TRAILING_STOP_MARKET', 
                    positionSide='BOTH',
                    timeInForce='GTC',
                    callbackRate=event['callbackRate'],
                    #activationPrice=activationPrice,
                    quantity=quantity
                    #newClientOrderId=newClientOrderId
                )
                print('TRAILING_STOP_MARKET:', trailingStopOrder)
                results['TRAILING_STOP_MARKET'] = trailingStopOrder
                '''
            if event['side'] == 'SELL':
                stopLossPrice = ticker['price'] + (ticker['price'] * stopLossPercent)
                stopLossPrice = format(stopLossPrice, stopPricePrecision)
                print('short stopLossPrice: ', stopLossPrice)
            
                stopShortOrder = client.futures_create_order(
                    symbol=event['symbol'], 
                    side='BUY', 
                    type='STOP_MARKET', 
                    positionSide='BOTH',
                    timeInForce='GTC',
                    #quantity=float_precision(float(quantity)/2.0, step_size),
                    closePosition=True,
                    stopPrice=stopLossPrice,
                    newClientOrderId=newClientOrderId
                )
                print('STOP_SHORT:', stopShortOrder)
                results['STOP_SHORT'] = stopShortOrder
                '''
                trailingStopOrder = client.futures_create_order(
                    symbol=event['symbol'], 
                    side='BUY', 
                    type='TRAILING_STOP_MARKET', 
                    positionSide='BOTH',
                    timeInForce='GTC',
                    callbackRate=event['callbackRate'],
                    #activationPrice=activationPrice,
                    quantity=quantity
                    #newClientOrderId=newClientOrderId
                )
                print('TRAILING_STOP_MARKET:', trailingStopOrder)
                results['TRAILING_STOP_MARKET'] = trailingStopOrder
                '''

        elif event['type'] == 'LIMIT':
            if event['positionSide'] == 'BOTH':
                longOrder = client.futures_create_order(
                    symbol=event['symbol'], 
                    side='BUY', 
                    type='MARKET', 
                    positionSide='LONG', 
                    quantity=quantity,
                    #timeInForce='GTC',
                    #price=ticker['price'],  # only for LIMIT
                    newClientOrderId=newClientOrderId
                )
                print('LONG:', longOrder)
                results['LONG'] = longOrder

                stopLossPrice = ticker['price'] - (ticker['price'] * stopLossPercent)
                stopLossPrice = format(stopLossPrice, stopPricePrecision)
                print('long stopLossPrice: ', stopLossPrice)
            
                stopLongOrder = client.futures_create_order(
                    symbol=event['symbol'], 
                    side='SELL', 
                    type='STOP_MARKET', 
                    positionSide='LONG',
                    timeInForce='GTC',
                    quantity=quantity,
                    stopPrice=stopLossPrice,
                    newClientOrderId=newClientOrderId
                )
                print('STOP_LONG:', stopLongOrder)
                results['STOP_LONG'] = stopLongOrder
    
                shortOrder = client.futures_create_order(
                    symbol=event['symbol'], 
                    side='SELL', 
                    type='MARKET', 
                    positionSide='SHORT',
                    quantity=quantity,
                    #timeInForce='GTC',
                    #price=ticker['price'], # only for LIMIT
                    newClientOrderId=newClientOrderId
                )
                print('SHORT:', shortOrder)
                results['SHORT'] = shortOrder

                stopLossPrice = ticker['price'] + (ticker['price'] * stopLossPercent)
                stopLossPrice = format(stopLossPrice, stopPricePrecision)
                print('short stopLossPrice: ', stopLossPrice)
            
                stopShortOrder = client.futures_create_order(
                    symbol=event['symbol'], 
                    side='BUY', 
                    type='STOP_MARKET', 
                    positionSide='SHORT',
                    timeInForce='GTC',
                    quantity=quantity,
                    stopPrice=stopLossPrice,
                    newClientOrderId=newClientOrderId
                )
                print('STOP_SHORT:', stopShortOrder)
                results['STOP_SHORT'] = stopShortOrder

            else:
                limitOrder = client.futures_create_order(
                    symbol=event['symbol'], 
                    side=event['type'],
                    type='LIMIT', 
                    positionSide=event['positionSide'], 
                    timeInForce='GTC',
                    quantity=quantity,
                    price=ticker['price'],
                    newClientOrderId=newClientOrderId
                )
                print('LIMIT:', limitOrder)
                results['LIMIT'] = limitOrder

        elif event['type'] == 'STOP_LIMIT'  or event['type'] == 'TAKE_PROFIT_LIMIT' or \
            event['type'] == 'STOP_MARKET' or event['type'] == 'TAKE_PROFIT_MARKET':
            '''
            symbol	STRING	YES	
            side	ENUM	YES	
            positionSide	ENUM	NO	Default BOTH for One-way Mode ; LONG or SHORT for Hedge Mode. It must be sent in Hedge Mode.
            type	ENUM	YES	
            timeInForce	ENUM	NO	
            quantity	DECIMAL	NO	Cannot be sent with closePosition=true(Close-All)
            reduceOnly	STRING	NO	"true" or "false". default "false". Cannot be sent in Hedge Mode; cannot be sent with closePosition=true
            price	DECIMAL	NO	
            newClientOrderId	STRING	NO	A unique id among open orders. Automatically generated if not sent. Can only be string following the rule: ^[\.A-Z\:/a-z0-9_-]{1,36}$
            stopPrice	DECIMAL	NO	Used with STOP/STOP_MARKET or TAKE_PROFIT/TAKE_PROFIT_MARKET orders.
            closePosition	STRING	NO	true, false；Close-All，used with STOP_MARKET or TAKE_PROFIT_MARKET.
            activationPrice	DECIMAL	NO	Used with TRAILING_STOP_MARKET orders, default as the latest price(supporting different workingType)
            callbackRate	DECIMAL	NO	Used with TRAILING_STOP_MARKET orders, min 0.1, max 5 where 1 for 1%
            workingType	ENUM	NO	stopPrice triggered by: "MARK_PRICE", "CONTRACT_PRICE". Default "CONTRACT_PRICE"
            priceProtect	STRING	NO	"TRUE" or "FALSE", default "FALSE". Used with STOP/STOP_MARKET or TAKE_PROFIT/TAKE_PROFIT_MARKET orders.
            newOrderRespType	ENUM	NO	"ACK", "RESULT", default "ACK"
            recvWindow	LONG	NO	
            timestamp	LONG	YES	
            '''
            event['timeInForce'] = 'GTC'
            event['newClientOrderId'] = newClientOrderId

            order = client.futures_create_order(**event)
            results[event['type']] = order

            print(results)
        
        elif event['type'] == 'TRAILING_STOP_MARKET':
            '''
            workingType	ENUM	NO	stopPrice triggered by: "MARK_PRICE", "CONTRACT_PRICE". Default "CONTRACT_PRICE" (LAST_PRICE)
            activationPrice	DECIMAL	NO	Used with TRAILING_STOP_MARKET orders, default as the latest price(supporting different workingType)
            callbackRate	DECIMAL	NO	Used with TRAILING_STOP_MARKET orders, min 0.1, max 5 where 1 for 1%
            '''

            if 'workingType' not in event:
                event['workingType'] = 'MARK_PRICE'
            
            if 'activationPrice' not in event:
                if event['side'] == 'BUY':
                    event['activationPrice'] = ticker['price'] - (ticker['price'] * activationPricePercent)
                if event['side'] == 'SELL':
                    event['activationPrice'] = ticker['price'] + (ticker['price'] * activationPricePercent)
        
            event['activationPrice'] = format(event['activationPrice'], stopPricePrecision)
            print('activationPrice:', event['activationPrice'])
        
            event['timeInForce'] = 'GTC'
            event['newClientOrderId'] = newClientOrderId

            order = client.futures_create_order(**event)
            results[event['type']] = order
            
        return results
    except BinanceAPIException as e:
        raise e
    except BinanceOrderException as e:
        raise e
