import pandas as pd
import datetime as dt
import argparse

from oandapyV20 import API
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
import oandapyV20.endpoints.forexlabs as labs
import oandapyV20.endpoints.orders as ordersEndpoint
import oandapyV20.endpoints.trades as tradesEndpoint
import oandapyV20.endpoints.instruments as instruments


def main():
    import time
    time.sleep(20)
    # python3 morning_simple_3_old.py -instrument=EUR_USD -tradeUnits=100 -averageMultiplayer=1.5 -bottomBarrierPips=0.004 -endingHour=12 -openingInterval=1 -slPips=0.0015 -startingHour=8 -tpMultiplayer=14 -moveSlPips=0.0015

    parser = argparse.ArgumentParser()
    parser.add_argument('-averageMultiplayer')
    parser.add_argument('-bottomBarrierPips')
    parser.add_argument('-endingHour')
    parser.add_argument('-openingInterval')
    parser.add_argument('-slPips')
    parser.add_argument('-startingHour')
    parser.add_argument('-tpMultiplayer')
    parser.add_argument('-moveSlPips')
    parser.add_argument('-tradeUnits')
    parser.add_argument('-instrument')
    parser.add_argument('-aid')
    args = parser.parse_args()

    averageMultiplayer = float(args.averageMultiplayer)
    bottomBarrierPips = float(args.bottomBarrierPips)
    endingHour = int(args.endingHour)
    openingInterval = int(args.openingInterval)
    slPips = float(args.slPips)
    startingHour = int(args.startingHour)
    tpMultiplier = float(args.tpMultiplayer)
    middleHour = round(startingHour + (endingHour - startingHour)/2, 0)
    moveSlPips = float(args.moveSlPips)
    aid = args.aid

    tradeUnits = int(args.tradeUnits)
    instrument = args.instrument
    granularity_param = 'M5'

    client = API(access_token='f8599fa0624567b98d6293acc87489bb-e288ec05b46b6e3d0bc753e6a2fbab48')
    aid = '101-004-8182547-007'

    calendar = cal(client, instrument, 604800)
    # EDGE CASE: THERE ARE NO CALENDAR EVENTS, KEY ERROR WITH TIMESTAMP WILL BE RAISEN
    history = hist(client, instrument, 3, 0, granularity_param)
    merged = merge(history, calendar)

    # TO BE REMOVED
    r = instruments.InstrumentsCandles(instrument="EUR_USD", params={"count": 1, "granularity": "M1"})
    client.request(r)
    print(r.response['candles'])

    merged = merged[merged['high'] != 0]

    merged['ma5'] = merged['close'].rolling(5).mean()
    merged['ma10'] = merged['close'].rolling(10).mean()
    merged = merged.dropna()

    print('merged data')
    print(merged.tail(5))
    print('----')

    candleData = merged[
        (
                (merged.index.hour >= 5) &
                (merged.index.hour < startingHour + openingInterval) &
                (merged.index.minute.isin([20, 40]))
        ) |
        (
                (merged.index.hour == startingHour + openingInterval) &
                (merged.index.minute.isin([0]))
        ) |
        (
                (merged.index.hour == endingHour) &
                (merged.index.minute == 0)
        ) |
        (
            (merged.index.hour == startingHour) &
            (merged.index.minute == 0)
        )
        ]

    print('candleData')
    print(candleData)
    print('----')

    if len(candleData[candleData['impact'] != 0]) == 0:
        currentCandle = candleData.iloc[-1]
        print('currentCandle')
        print(currentCandle)
        print('---')

        # FIRST OPEN
        if (currentCandle.name.hour == startingHour and
                currentCandle.name.minute == 20):

            basePrice = candleData[
                    (candleData.index.hour == startingHour) &
                    (candleData.index.minute == 0)
            ].iloc[0].open
            print('first trade, base price open is')
            print(basePrice)
            print('the current candle open price is')
            print(currentCandle.open)
            if currentCandle.open < basePrice:
                response = openTrade(client, aid, instrument, tradeUnits, bottomBarrierPips, 0.0100)
                print(response)

        # OPEN OTHERS
        elif ((currentCandle.name.hour == startingHour) and
            (currentCandle.name.minute == 40)) or \
                ((currentCandle.name.hour > startingHour) and
                 (currentCandle.name.hour < startingHour + openingInterval)):
            print('next trades')

            if currentCandle['ma5'] < currentCandle['ma10']:

                tradesList = get_trades(client, aid)
                print('trades list')
                print(tradesList)
                if len(tradesList) != 0:
                    firstTimestamp = '2050-10-28T14:28:05.231759081Z'
                    pricesContainer = []
                    for trade in tradesList:
                        pricesContainer.append(trade['price'])
                        if trade['openTime'] < firstTimestamp:
                            firstTimestamp = trade['openTime']
                            firstSL = trade['stopLossOnFill']['price']
                            basePrice = trade['price']
                            
                    # EDGE CASE: trades before were closed because of bottomBarrier
                    # (or stoploss in other words), so it will open another trade
                    if currentCandle['open'] > firstSL:
                        if currentCandle['open'] < basePrice:
                            if currentCandle['open'] < min(pricesContainer):
                                unitsMultiplayed = len(pricesContainer) * averageMultiplayer
                                response = openTrade(client, aid, instrument, unitsMultiplayed, firstSL, 0.0100)
                                print(response)
                else:
                    # open trade when there are no open trades
                    basePrice = candleData[
                            (candleData.index.hour == startingHour) &
                            (candleData.index.minute == 0)
                    ].iloc[0].open
                    print('There are still no trades open, take a look at base price')
                    print(basePrice)
                    print('and at the current open price')
                    print(currentCandle['open'])

                    if currentCandle['open'] < basePrice:
                        response = openTrade(client, aid, instrument, tradeUnits, bottomBarrierPips, 0.0100)
                        print(response)

        # OPEN THE LAST ONE
        # MOVE SL AT THE END OF OPENING INTERVAL
        elif (currentCandle.name.hour == startingHour + openingInterval and
              currentCandle.name.minute == 0):
            print('last trade')

            if currentCandle['ma5'] > currentCandle['ma10']:

                tradesList = get_trades(client, aid)
                if len(tradesList) != 0:
                    firstTimestamp = '2050-10-28T14:28:05.231759081Z'
                    pricesContainer = []
                    unitsContainer = []
                    for trade in tradesList:
                        pricesContainer.append(trade['price'])
                        unitsContainer.append(trade['initialUnits'])
                        if trade['openTime'] < firstTimestamp:
                            firstTimestamp = trade['openTime']
                            firstSL = trade['stopLossOnFill']['price']
                            basePrice = trade['price']

                    # EDGE CASE: trades before were closed because of bottomBarrier
                    # (or stoploss in other words), so it will open another trade
                    if currentCandle['open'] > firstSL:
                        if currentCandle['open'] < basePrice:
                            if currentCandle['open'] < min(pricesContainer):
                                unitsMultiplayed = len(pricesContainer) * averageMultiplayer
                                openTrade(client, aid, instrument, unitsMultiplayed, firstSL, 0.0100)

            pricesContainer = []
            unitsContainer = []
            for trade in get_trades(client, aid):
                pricesContainer.append(trade['price'])
                unitsContainer.append(trade['initialUnits'])

            if len(pricesContainer) != 0:
                weightedPrices = []
                for i in range(len(pricesContainer)):
                    weightedPrices.append(pricesContainer[i] * unitsContainer[i])
                averagePrice = weightedPrices / sum(unitsContainer)
                newSL = averagePrice - slPips
                newTP = averagePrice + (slPips * tpMultiplier)

                for trade in get_trades(client, aid):
                    change_sl_tp(client, aid, trade['id'], newSL, newTP)

            # EDGE CASE: IT CAN TRY TO MOVE SL TOO CLOSE TO TRADES

        # MOVE SL
        elif currentCandle.name.hour == middleHour and \
                currentCandle.name.minute == 20:

            for trade in get_trades(client, aid):
                change_sl_tp(client, aid, trade['id'],
                             float(trade['stopLossOrder']['price']) + moveSlPips,
                             trade['stopLossOrder']['price'])


        # CLOSE TRADES (ENDING BARRIER)
        elif currentCandle.name.hour == endingHour:
            print('ending hour')

            for trade in get_trades(client, aid):
                r = tradesEndpoint.TradeClose(accountID=aid,
                                              data={"units": trade['initialUnits']},
                                              tradeID=trade['id'])
                client.request(r)

        else:
            print('no action')


def openTrade(api, aid, instrument, tradeUnits, sl, tp):
    data = {
        "order": {
            "instrument": instrument,
            "units": tradeUnits,
            "side": "sell",
            "type": "MARKET",
            "stopLossOnFill": {
                "timeInForce": "GTC",
                "price": str(sl),
            },
            "takeProfitOnFill": {
                "timeInForce": "GTC",
                "price": str(tp),
            },
        },
        "lowerBound": 0.0005,
        "upperBound": 0.0005,
    }

    o = ordersEndpoint.OrderCreate(aid, data=data)
    return api.request(o)


def get_trades(api, aid):
    trades_list = tradesEndpoint.OpenTrades(accountID=aid)
    return api.request(trades_list)['trades']


def change_sl_tp(client, aid, tradeID, sl, tp):
    data = {
        "takeProfit": {
            "timeInForce": "GTC",
            "price": str(tp)
        },
        "stopLoss": {
            "timeInForce": "GTC",
            "price": str(sl)
        }
    }

    r = tradesEndpoint.TradeCRCDO(accountID=aid,
                          tradeID=tradeID,
                          data=data)

    return client.request(r)


def hist(api, instrument, start_days, end_days, granularity):
    start_date = (dt.datetime.now() - dt.timedelta(days=start_days)).strftime('%Y-%m-%dT%H:%M:%SZ')
    # end_date = (dt.datetime.now() - dt.timedelta(days=end_days, hours=2, minutes=4)).strftime('%Y-%m-%dT%H:%M:%SZ')

    params = {
        "from": start_date,
        "granularity": granularity,
    }

    df_list = []
    for r in InstrumentsCandlesFactory(instrument=instrument, params=params):
        api.request(r)
        df = pd.DataFrame(r.response['candles'])
        if (df.empty == False):
            time = df['time']
            volume = pd.DataFrame(df['volume'].apply(pd.Series))
            df = pd.DataFrame(df['mid'].apply(pd.Series))
            df = pd.concat([df, time, volume], axis=1)
            df['time'] = pd.to_datetime(df['time'], format='%Y-%m-%dT%H:%M:%S.000000000Z')
            # df.set_index('time',inplace=True)
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


def cal(client, instrument, perdiod):
    params = {
        "instrument": instrument,
        "period": perdiod
    }

    # PERIOD VALUES
    # 3600 - 1 hour
    # 43200 - 12 hours
    # 86400 - 1 day
    # 604800 - 1 week
    # 2592000 - 1 month
    # 7776000 - 3 months
    # 15552000 - 6 months
    # 31536000 - 1 year
    # http://developer.oanda.com/rest-live/forex-labs/

    r = labs.Calendar(params=params)
    client.request(r)

    df = pd.DataFrame.from_dict(r.response, orient='columns')

    df['timestamp'] = pd.to_datetime(df['timestamp'] * 1000000000)
    df = df[['impact', 'timestamp']]
    df.columns = ['impact', 'time']

    return df.groupby('time').sum().reset_index()


def merge(history, calendar):
    return pd.merge(history, calendar, left_on = 'time', right_on = 'time', how='outer')\
                                                                            .set_index('time')\
                                                                            .astype(float)\
                                                                            .fillna(0)


if __name__ == '__main__':
    main()
