
# Algorithm trading

In this repository I store all strategies I want to be public

### Quickstart

##### Oanda
1) Create demo account at oanda website https://www.oanda.com/register/#/sign-up/demo
2) Handle the registration, and after logging in proceed to "Manage Funds" section
3) Add a few accounts with deposit (you need to do it manually, by default there is 0 balance)
4) Proceed to Manage API access and revoke/generate a token

##### Repo
1) Clone the repository
2) Being above repository directory execute python(3) -m venv venv_algo
3) Activate virtualenv by . venv_algo/bin/activate (linux) or ./venv_algo/Scripts/activate (win)
4) CD to repo folder
5) Add the repo to installed packages by pip install -e .
6) Install requirements by python(3) -m pip install -r requirements.txt
7) Create in your home directory file .key, 
paste the api key generated on oanda website in the first line and
any account number in second line

##### Order/Position book data scrapping
1) cd to /bookData
2) execute python(3) get_book.py -instrument=XXX_XXX -type=xxxxxxBook -start_date=YYYY-MM -end_date=YYYY-MM


### File structure

- oanda_old - my first playground with oanda's api
- tools-py - collection of useful functions for faster development
- workbook.ipynb - notebook where I test new functions for tools.py
- /bookData - folder where order/position book data is stored
- all the rest folders contain some strategy, there should be three 
 files: notebook with strategy testing, notebook with trading testing
 and .py file with trading itself

## Existing algorithms


### Morning strategy (trading - testing phrase)

###### Description
The idea is that every morning smarter part of the market first thanks to
better analysis/data predicts how price will behave - whether it will o up or down.
Then, with clear goal it tries the market by placing orders in the wrong direction 
to fool other people - when they finally reach a level where lots of people have their 
stop looses it change the direction to the goal they anticipated before morning.
Secondly, I am not trying to find a level where prices changes direction but
to place many orders, based also on MA values.
###### Results
Scores in pips are not the best, there is a chance that I just found
a combination of features which fits a particular date period on specific instrument.
https://www.myfxbook.com/portfolios/simple-demo/308663
###### Next steps
Monitor three strategies which are live on demo accounts

### Book strategy (trading - testing phrase)

###### Description
Every 20 minutes there is a new order/position book data. From this values I can calculate
some kind of sentiment - whether market is more bullish or bearish. According to this value
limit trade will be opened, with price a bit moved in the opposite direction of market.
###### Results
Notebook testing showed that it could be a really good ide
###### Next steps
Deploy three strategies with are live on demo accounts


### Decision tree (halted)

###### Description
The main point there was to train model again every new day or candle
so it will be auto-updated.
###### Results 
The accuracy is bad, so right now this project is abandoned
###### Next steps
None

## Ideas

### ML indicator

###### Descriptions
The point is to create graphic indicator which shows on chart what should be the next market move.
This indicator is not meant to trade but just to be a filter (advice) for live trading
###### Results
None
###### Next steps
Create such a thing and apply it on pure python chart - decide whether it is useful or not.


### Fibonacci strategy

###### Descriptioon
Logic behind that is quite simple, use popular fibonacci extension levels to
open trades. The problem is how to define it and find proper max/min values for
a trend in the code
###### Results
None
###### Next steps
Try with approach that the time frame for max/min values looking is the same
as size of meta trader 4 window on different intervals.
