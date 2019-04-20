from oandapyV20.contrib.factories import InstrumentsCandlesFactory
import oandapyV20.endpoints.forexlabs as labs
from oandapyV20.endpoints import pricing
from oandapyV20 import API

import pandas as pd
import datetime as dt
import os
import requests


def myAPI():
    return API(access_token=open(os.path.expanduser('~/.key'), 'r').read().splitlines()[0])


def stream(instrument):
    api = myAPI()
    aid = open(os.path.expanduser('~/.key'), 'r').read().splitlines()[1]
    r = pricing.PricingStream(accountID=aid, params={'instruments': instrument})
    return api.request(r)


def get_book(instrument, tmp_typ, bucketNumber):
    if tmp_typ == 'positions':
        typ = 'positionBook'
    elif tmp_typ == 'orders':
        typ = 'orderBook'
    else:
        return 'Wrong type'

    response = requests.get(
        url='https://api-fxpractice.oanda.com/v3/instruments/{}/{}'.format(instrument, typ),
        headers={
            'Authorization': 'Bearer ' + open(os.path.expanduser('~/.key'), 'r').read().splitlines()[0],
        }
    ).json()

    if 'errorMessage' in response.keys():
        return response['errorMessage']
    else:
        bucketPrices = []
        bucketDict = {}
        for bucket in response[typ]['buckets']:
            bucketPrices.append(float(bucket['price']))
            bucketDict[float(bucket['price'])] = {
                "long": bucket['longCountPercent'],
                "short": bucket['shortCountPercent'],
            }

        returnBuckets = {}
        closestPrice = min(bucketPrices, key=lambda x: abs(x - float(response[typ]['price'])))
        for i in range(bucketNumber + 1, 1, -1):
            priceToLookUp = round(closestPrice + (float(response[typ]['bucketWidth']) * i), 4)
            returnBuckets[priceToLookUp] = {
                'longs': bucketDict[priceToLookUp]['long'],
                'shorts': bucketDict[priceToLookUp]['short'],
            }

        returnBuckets[closestPrice] = {
            'longs': bucketDict[closestPrice]['long'],
            'shorts': bucketDict[closestPrice]['short'],
        }

        for i in range(1, bucketNumber + 1):
            priceToLookUp = round(closestPrice - (float(response[typ]['bucketWidth']) * i), 4)
            returnBuckets[priceToLookUp] = {
                'longs': bucketDict[priceToLookUp]['long'],
                'shorts': bucketDict[priceToLookUp]['short'],
            }

        return response[typ]['time'], returnBuckets


def history(orders, positions, days_back, instrument, granularity):

    if orders:
        try:
            ordersDirectory = './bookData/'+instrument+'/orders'
            ordersFiles = os.listdir(ordersDirectory)
        except FileNotFoundError:
            return "OrderBook data for {} was not found in directory {}"\
                    .format(instrument, ordersDirectory)
        tmp = []
        for file in ordersFiles:
            tmp.append(pd.read_csv('./bookData/{}/orders/{}'\
                                   .format(instrument, file)))
        tmpConcat = pd.concat(tmp)
        tmpConcat = tmpConcat \
            .set_index(pd.to_datetime(tmpConcat['time'], format="%Y-%m-%dT%H:%M:%SZ"))

        newColumns = []
        for column in tmpConcat.columns:
            newColumns.append(column + '_orders')
        tmpConcat.columns = newColumns

        orderBook = tmpConcat

    if positions:
        try:
            positionsDirectory = './bookData/'+instrument+'/positions'
            positionsFiles = os.listdir(positionsDirectory)
        except FileNotFoundError:
            return "PositionBook data for {} was not found in directory {}"\
                    .format(instrument, positionsDirectory)
        tmp = []
        for file in positionsFiles:
            tmp.append(pd.read_csv('./bookData/{}/positions/{}'\
                                   .format(instrument, file)))
        tmpConcat = pd.concat(tmp)
        tmpConcat = tmpConcat \
            .set_index(pd.to_datetime(tmpConcat['time'], format="%Y-%m-%dT%H:%M:%SZ"))

        newColumns = []
        for column in tmpConcat.columns:
            newColumns.append(column + '_positions')

        tmpConcat.columns = newColumns
        positionBook = tmpConcat

    api = myAPI()
    candles = hist(api, instrument, days_back, granularity)

    if days_back > 365:
        period = 31536000
    elif days_back > 182:
        period = 15552000
    elif days_back > 90:
        period = 7776000
    elif days_back > 30:
        period = 2592000
    else:
        period = 604800
    calendar = cal(api, instrument, period)

    if orders == True and positions == True:
        merged = merge(candles, calendar)
        allData = merged.join(orderBook).join(positionBook) \
            .drop(['Unnamed: 0_orders', 'Unnamed: 0_positions', 'price_orders',
                   'roundedPrice_orders', 'price_positions', 'roundedPrice_positions',
                   'time_orders', 'time_positions'], axis=1)
        return allData[allData['open'] != 0]

    if positions:
        merged = merge(candles, calendar)
        allData = merged.join(positionBook)\
            .drop(['Unnamed: 0_positions',
                   'price_positions', 'roundedPrice_positions',
                   'time_positions'], axis=1)
        return allData[allData['open'] != 0]

    if orders:
        merged = merge(candles, calendar)
        allData = merged.join(orderBook) \
            .drop(['Unnamed: 0_orders', 'price_orders',
                   'roundedPrice_orders',
                   'time_orders'], axis=1)
        return allData[allData['open'] != 0]

    if positions == False and orders == False:
        allData = merge(candles, calendar)
        return allData[allData['open'] != 0]


def hist(api, instrument, start_days, granularity):
    start_date = (dt.datetime.now()-dt.timedelta(days=start_days)).strftime('%Y-%m-%dT%H:%M:%SZ')

    params = {
        "from": start_date,
        "granularity":granularity,
    }

    df_list = []
    for r in InstrumentsCandlesFactory(instrument=instrument,params=params):
        api.request(r)
        df = pd.DataFrame(r.response['candles'])
        if not df.empty:
            time = df['time']
            volume = pd.DataFrame(df['volume'].apply(pd.Series))
            df = pd.DataFrame(df['mid'].apply(pd.Series))
            df = pd.concat([df,time,volume], axis=1)
            df['time'] = pd.to_datetime(df['time'], format='%Y-%m-%dT%H:%M:%S.000000000Z')
            df_list.append(df)
    final = pd.concat(df_list)

    names = {
        'o': 'open',
        'c': 'close',
        'h': 'high',
        'l': 'low',
        0: 'vol',
        'time': 'time',
    }
    new_names = []
    for column_name in final.columns:
        new_names.append(names[column_name])
    final.columns = new_names

    return final


def cal(client, instrument, period):
    params = {
        "instrument": instrument,
        "period": period
    }
    # PERIOD VALUES
    #3600 - 1 hour
    #43200 - 12 hours
    #86400 - 1 day
    #604800 - 1 week
    #2592000 - 1 month
    #7776000 - 3 months
    #15552000 - 6 months
    #31536000 - 1 year
    # http://developer.oanda.com/rest-live/forex-labs/

    r = labs.Calendar(params=params)
    client.request(r)

    try:
        df = pd.DataFrame.from_dict(r.response, orient='columns')
        df['timestamp'] = pd.to_datetime(df['timestamp']*1000000000)
        df = df[['impact', 'timestamp']]
        df.columns = ['impact', 'time']

        return df.groupby('time').sum().reset_index()
    except:
        return r.response


def merge(his, calendar):
    return pd.merge(his, calendar, left_on = 'time', right_on = 'time', how='outer')\
                                                                         .fillna(0)
