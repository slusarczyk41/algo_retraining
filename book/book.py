import sys
sys.path.append('../')

from tools import stream, get_book, myAPI, cal
from datetime import datetime as dt
from time import sleep
from pandas import to_datetime

import oandapyV20.endpoints.orders as orders_endpoint
import oandapyV20.endpoints.trades as trades


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-instrument')
    parser.add_argument('-bucketWidth')
    parser.add_argument('-minDifference')
    parser.add_argument('-minMovement')
    parser.add_argument('-slPips')
    parser.add_argument('-tpPips')
    parser.add_argument('-waitingPeriods')
    parser.add_argument('-openPeriods')
    parser.add_argument('-startingHour')
    parser.add_argument('-endingHour')
    parser.add_argument('-aid')
    args = parser.parse_args()


    instrument = 'EUR_USD'
    bucketWidth = 3
    minDifference = 0.1
    tradeUnits = 100
    minMovement = 0.0002
    slPips = 0.0010
    tpPips = 0.0020
    waitingPeriods = 5
    openPeriods = 10
    startingHour = 8
    endingHour = 22

    aid = "101-004-8182547-007"
    api = myAPI()

    try:
        del prevMinute
    except:
        pass

    trade = resetTrade().copy()
    for tick in stream(instrument):
        # testingContainer.append(tick)

        try:
            prevMinute
        except:
            prevMinute = int(tick['time'][14:16])
            continue

        if startingHour < int(tick['time'][11:13]) < endingHour:

            currentMinute = int(tick['time'][14:16])
            if tick['type'] == 'PRICE':
                currentAskPrice = tick['closeoutAsk']
                currentBidPrice = tick['closeoutBid']

            if currentMinute != prevMinute:
                if trade['status'] == 'idle':
                    print('------- idle -------')
                    print(tick['time'])

                    if currentMinute in (0, 20, 40):
                        while True:
                            bookTime, orders = get_book(instrument, 'orders', bucketWidth)
                            if int(bookTime[14:16]) == currentMinute:
                                break
                            sleep(1)

                        positions = get_book(instrument, 'positions', bucketWidth)[1]
                        decision = validateOpen(orders, positions, minDifference)
                        print('decision: ' + str(decision))
                        if decision:
                            trade['status'] = 'waiting'
                            trade['waitingPeriods'] = waitingPeriods

                            calendar = cal(api, instrument, '3600')
                            print('calendar ' + str(calendar))
                            if len(calendar) != 0:
                                lastEventTs = cal(api, instrument, '3600').iloc[-1].time
                                currentTs = to_datetime(tick['time'][:22])
                                print((currentTs - lastEventTs).seconds)
                                if (currentTs - lastEventTs).seconds < 1800:
                                    continue

                            if decision == 'buy':
                                print('opentrade')
                                openPrice = round(float(currentBidPrice) - minMovement, 5)
                                print(openTrade(api, aid,
                                                instrument,
                                                tradeUnits,
                                                round(openPrice - slPips, 5),
                                                round(openPrice + tpPips, 5),
                                                openPrice))

                            else:
                                print('opentrade')
                                openPrice = float(currentAskPrice) + minMovement
                                print(openTrade(api, aid,
                                                instrument,
                                                -tradeUnits,
                                                round(openPrice + slPips, 5),
                                                round(openPrice - tpips, 5),
                                                openPrice))


                elif trade['status'] == 'waiting':
                    print('------- waiting -------')
                    print('currentPrice: ' + str(currentAskPrice))
                    print('currentPrice: ' + str(currentBidPrice))
                    print('and the trade: ')
                    print(trade)

                    openTrades = get_trades(api, aid)
                    waitingOrders = get_orders(api, aid)
                    if len(openTrades) == 0 and len(waitingOrders) != 0:
                        print('still not open')
                        if trade['waitingPeriods'] == 0:
                            trade = resetTrade().copy()
                            for waitingTrade in waitingOrders:
                                r = orders_endpoint.OrderCancel(accountID=aid,
                                                                orderID=waitingTrade['id'])
                                print(api.request(r))
                        else:
                            trade['waitingPeriods'] -= 1
                    else:
                        trade['openPeriods'] = openPeriods
                        trade['status'] = 'open'


                elif trade['status'] == 'open':
                    print('----- open ------')
                    print(trade)
                    if trade['openPeriods'] == 0:
                        for openTrade in get_trades(api, aid):
                            r = trades.TradeClose(accountID=aid,
                                                  tradeID=openTrade['id'],
                                                  data={"units": openTrade['initialUnits']})
                            print(api.request(r))
                    else:
                        trade['openPeriods'] -= 1
                        trades = get_trades(api, aid)
                        print(trades)
                        for trade in trades:
                            if int(trade['initialUnits']) > 0:
                                print(change_sl_tp(aid, aid, trade['id'],
                                                   float(trade['stopLossOnFill']['price']) + 0.0001
                                                   ))
                            else:
                                print(change_sl_tp(aid, aid, trade['id'],
                                                   float(trade['stopLossOnFill']['price']) - 0.0001
                                                   ))


                else:
                    print('something went wrong')
                    print(trade)
                    print(get_trades(api, aid))
                    print(get_orders(api, aid))

            prevMinute = currentMinute


def resetTrade():
    return {
        'status': 'idle',
        'openPrice': None
    }


def openTrade(api, aid, instrument, tradeUnits, slPrice, tpPrice, openPrice):
    data = {
      "order": {
        "price": str(openPrice),
        "stopLossOnFill": {
          "timeInForce": "GTC",
          "price": str(slPrice)
        },
        "takeProfitOnFill": {
          "price": str(tpPrice)
        },
        "timeInForce": "GTC",
        "instrument": instrument,
        "units": str(tradeUnits),
        "type": "LIMIT",
        "positionFill": "DEFAULT"
      }
    }

    o = orders_endpoint.OrderCreate(aid, data=data)
    return api.request(o)


def change_sl_tp(client, aid, tradeID, sl):
    data = {
      "stopLoss": {
        "timeInForce": "GTC",
        "price": str(sl)
      }
    }

    r = trades.TradeCRCDO(accountID=aid,
                           tradeID=tradeID,
                           data=data)
    return client.request(r)


def get_trades(api, aid):
    trades_list = trades.OpenTrades(accountID=aid)
    return api.request(trades_list)['trades']


def get_orders(api, aid):
    trades_list = orders_endpoint.OrderList(accountID=aid)
    return api.request(trades_list)['orders']


def validateOpen(orders, positions, minDifference):
    longs = 0
    shorts = 0
    for key in orders.keys():
        longs += float(orders[key]['longs'])
        shorts += float(orders[key]['shorts'])
    ordersSentiment = longs / shorts

    longs = 0
    shorts = 0
    for key in positions.keys():
        longs += float(orders[key]['longs'])
        shorts += float(orders[key]['shorts'])
    positionsSentiment = longs / shorts

    if ordersSentiment > (1 + minDifference) and positionsSentiment > (1 + minDifference):
        return 'buy'
    elif ordersSentiment < (1 - minDifference) and positionsSentiment < (1 - minDifference):
        return 'sell'
    else:
        return None


if __name__ == '__main__':
    main()
