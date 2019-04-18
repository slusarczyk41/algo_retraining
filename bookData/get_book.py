import requests
from datetime import datetime, timedelta
import pandas as pd
import os
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-instrument', help='like EUR_USD')
    parser.add_argument('-type', help='positionBook/orderBook')
    parser.add_argument('-start_date', help='like 2019-03')
    parser.add_argument('-end_date', help='like 2019-04')
    args = parser.parse_args()

    key = open(os.path.expanduser('~/.key'), 'r').read().splitlines()[0]
    typ = args.type
    startDate = args.start_date + '-01T00:00:00Z'
    endDate = args.end_date + '-01T00:00:00Z'
    instrument = args.instrument

    priceRange = None
    df_list = []
    currMonth = pd.to_datetime(startDate).month

    for i, response in enumerate(dataGenerator(typ, startDate, endDate, key, instrument)):
        if typ in response.keys():

            if not priceRange:
                priceRange, zerosCounter, numberToRound = getInstrumentStats(response, typ)

            row = processRecord(response, typ, zerosCounter, numberToRound, priceRange)
            df_list.append(row)

            currTimestamp = pd.to_datetime(response[typ]['time'])
            if currMonth != currTimestamp.month:
                savingName = str(currTimestamp.year) + '-' + str(currTimestamp.month)
                print('saving data for: ' + savingName)
                save_data(df_list, savingName, typ, instrument)
                df_list = []

        else:
            if 'is not yet available. The most recent snapshot was' in response['errorMessage']:
                print('This month has not all data')
                savingName = str(currTimestamp.year) + '-' + str(currTimestamp.month)
                print('saving data for: ' + savingName)
                save_data(df_list, savingName, typ, instrument)
                break
            else:
                print(response)


def save_data(df_list, date, typ, instrument):
    df = pd.DataFrame(df_list, columns = [
            'time',
            'price',
            'roundedPrice',
            'level_0_l',
            'level_0_s',
            'level_1_up_l',
            'level_1_up_s',
            'level_1_down_l',
            'level_1_down_s',
            'level_2_up_l',
            'level_2_up_s',
            'level_2_down_l',
            'level_2_down_s',
            'level_3_up_l',
            'level_3_up_s',
            'level_3_down_l',
            'level_3_down_s',
            'level_4_up_l',
            'level_4_up_s',
            'level_4_down_l',
            'level_4_down_s',
            'level_5_up_l',
            'level_5_up_s',
            'level_5_down_l',
            'level_5_down_s',
        ])
    if not os.path.exists(instrument):
        os.mkdir(instrument)
    if not os.path.exists(instrument+'/'+typ.replace('Book', 's')):
        os.mkdir(instrument+'/'+typ.replace('Book', 's'))
    df.to_csv(instrument+'/'+typ.replace('Book', 's')+'/'+date+'.csv')


def dataGenerator(typ, start, end, key, instrument):
    reqNumber = (datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ") - \
                 datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ")).total_seconds() / 60 / 20

    date = datetime.strptime(start, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%dT%H:%M:%SZ")

    for i in range(int(reqNumber)):
        yield requests.get(
            url='https://api-fxpractice.oanda.com/v3/instruments/' +instrument+ '/' + typ,
            headers={
                'Authorization': 'Bearer ' + key,
            },
            data={
                'time': date
            }
        ).json()

        date = (datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ") + timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%SZ")


def processRecord(response, typ, zerosCounter, numberToRound, priceRange):
    price = float(response[typ]['price'])

    estimatePrices = []
    estimatePrices.append(float(str(round(price, zerosCounter))))
    estimatePrices.append(
        round(round(price, zerosCounter) - float(numberToRound / (10 ** (zerosCounter + 1))), zerosCounter + 1))
    estimatePrices.append(
        round(round(price, zerosCounter) + float(numberToRound / (10 ** (zerosCounter + 1))), zerosCounter + 1))

    diff = 100
    chosenMiddlePriceIndex = 0
    for i, p in enumerate(estimatePrices):
        if abs(price - p) < diff:
            diff = abs(price - p)
            chosenMiddlePriceIndex = i

    middlePrice = estimatePrices[chosenMiddlePriceIndex]

    tmpBuckets = {}
    for bucket in response[typ]['buckets']:
        tmpBuckets[float(bucket['price'])] = {
            'l': bucket['longCountPercent'],
            's': bucket['shortCountPercent'],
        }
    pricesKeys = list(tmpBuckets.keys())

    row = [
        response[typ]['time'],
        response[typ]['price'],
        middlePrice,
    ]

    if middlePrice in pricesKeys:
        row.append(tmpBuckets[middlePrice]['l'])
        row.append(tmpBuckets[middlePrice]['s'])
    else:
        row.append(0)
        row.append(0)

    UpPrice = middlePrice
    DownPrice = middlePrice
    floatedPriceBucket = float(priceRange)
    for i in range(5):
        UpPrice = UpPrice + floatedPriceBucket
        if UpPrice in pricesKeys:
            row.append(tmpBuckets[UpPrice]['l'])
            row.append(tmpBuckets[UpPrice]['s'])
        else:
            row.append(0)
            row.append(0)

        DownPrice = DownPrice + floatedPriceBucket
        if DownPrice in pricesKeys:
            row.append(tmpBuckets[DownPrice]['l'])
            row.append(tmpBuckets[DownPrice]['s'])
        else:
            row.append(0)
            row.append(0)

    return row


def getInstrumentStats(response, typ):
    priceRange = response[typ]['bucketWidth']
    numberToRound = len(str(response[typ]['bucketWidth']).split('.')[1])

    zerosCounter = 0
    for number in str(priceRange).split('.')[1]:
        if number == '0':
            zerosCounter = zerosCounter + 1
        else:
            break

    return priceRange, zerosCounter, numberToRound


if __name__ == '__main__':
    main()
