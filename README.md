# Algo trading epic

In this repository I store all strategies I have made as a backup

## Decision tree

###### Description
The main point there was to train model again every new candle so it will 
be auto-updated.
###### Results 
The accuracy is not good so right now this project is abandoned
###### Next steps
Find better definition when to close a trade.

## Morning

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
###### Next steps
Monitor three strategies which are live on demo

## Book

###### Description
Thanks to oanda's data about position and order book I want to try to create kind of
sentiment score for every 20 minutes on the market. By having such a score I can anticipate,
whether the market is more bullish or bearish - then, during next few minutes I can wait
for price to go the opposite direction then sentiment and then open a trade according to
the sentiment
###### Results
From parameters fitting this strategy seems to be very good
###### Next steps
Create a strategy which will be operating on streaming data