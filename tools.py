from oandapyV20.contrib.factories import InstrumentsCandlesFactory
import oandapyV20.endpoints.forexlabs as labs

import pandas as pd
import datetime as dt
import numpy as np


def test():
    return 'dupa'

def hist(api, instrument, start_days, end_days, granularity):

    start_date = (dt.datetime.now()-dt.timedelta(days=start_days)).strftime('%Y-%m-%dT%H:%M:%SZ')
    end_date = (dt.datetime.now()-dt.timedelta(days=end_days, hours=2,minutes=4)).strftime('%Y-%m-%dT%H:%M:%SZ')

    params ={
                "from": start_date,
                "to": end_date,
                "granularity":granularity,
            }

    df_list = []
    for r in InstrumentsCandlesFactory(instrument=instrument,params=params):
        api.request(r)
        df = pd.DataFrame(r.response['candles'])
        if(df.empty==False):
            time = df['time']
            volume = pd.DataFrame(df['volume'].apply(pd.Series))
            df = pd.DataFrame(df['mid'].apply(pd.Series))
            df = pd.concat([df,time,volume], axis=1)
            df['time'] = pd.to_datetime(df['time'], format='%Y-%m-%dT%H:%M:%S.000000000Z')
            #df.set_index('time',inplace=True)
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
    
    df = pd.DataFrame.from_dict(r.response, orient='columns')
    
    df['timestamp'] = pd.to_datetime(df['timestamp']*1000000000)
    df = df[['impact', 'timestamp']]
    df.columns = ['impact', 'time']

    return df.groupby('time').sum().reset_index()

def merge(history, calendar):
    return pd.merge(history, calendar, left_on = 'time', right_on = 'time', how='outer')\
                                                                            .set_index('time')\
                                                                            .astype(float)\
                                                                            .fillna(0)