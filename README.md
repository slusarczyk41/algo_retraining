# Algo (re)trading epic

In this repository I have all strategies I want to be public

### Quickstart

1) Create demo account at oanda website https://www.oanda.com/register/#/sign-up/demo
2) Handle the registration, and after logging in proceed to "Manage Funds" section
3) Add a few accounts with deposit (you need to do it manually, by default there is 0 balance)
4) Proceed to Manage API access and revoke/generate a token
5) Create in your home directory file .key, and paste the key in it
6) Congrats, now you can test your settings by 

### File structure

- oanda_old - my first playground with oanda's api
- tools-py - collection of useful functions for faster development
- workbook.ipynb - notebook where I test new functions for tools.py
- /bookData - folder where order/position book data is stored
- all the rest folders contain some strategy, there should be three 
 files: notebook with strategy testing, notebook with trading testing
 and .py file with trading itself

# Algorithms

### Decision tree (halted)

###### Description
The main point there was to train model again every new candle so it will 
be auto-updated.
###### Results 
The accuracy is bad, so right now this project is abandoned
###### Next steps
Find better definition when to close a trade.

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
Monitor three strategies which are live on demo

### ML indicator (idea)

###### Descriptions
The point is to create graphic indicator which shows on chart what should be the next market move.
This indicator is not meant to trade but just to be a filter (advice) for live trading
###### Results
None
###### Next steps
Create such a thing and apply it on pure python chart - decide whether it is useful or not.
