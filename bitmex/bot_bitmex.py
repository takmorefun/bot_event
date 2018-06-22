#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 31 16:32:09 2018

@author: matsumototakuya
"""
#テクニカル系botの基底クラス．ローソク足でのバックテスト．注文処理を実装．
import ccxt
import pandas as pd
import time
import requests
import datetime

class Order:
   def __init__(self, key, secret, isTestNet):
       self.product_code = 'BTC/USD'
       self.key = key
       self.secret = secret
       self.api = ccxt.bitmex({
       'apiKey': key,
       'secret': secret,})
       
       if isTestNet:
           self.api.urls["api"] =  self.api.urls["test"]
       self.latest_exec_info = []

   #指値注文用関数
   def limit(self, side, price, size, minute_to_expire=None):
       print("Order: Limit. Side : {}".format(side))
       response = {"status":"internalError in order.py"}
       try:
           response = self.api.create_order(self.product_code, type='limit', side=side, amount=size, price=price)
       except:
           pass
       while "error" in response:
           try:
               response = self.api.create_order(self.product_code, type='limit', side=side, amount=size, price=price)
           except:
               pass
           time.sleep(3)
       return response
       
   #成行注文用関数
   def market(self, side, size, minute_to_expire= None):
       print("Order: Market. Side : {}".format(side))
       response = {"status": "internalError in order.py"}
       try:
           response = self.api.create_order('BTC/USD', type='market', side=side, amount=size)
       except:
           pass
       while "error" in response:
           try:
               response = self.api.create_order('BTC/USD', type='market', side=side, amount=size)
#               print(response)
           except:
               pass
           time.sleep(3)
       return response            
       
   """
   現状のポジションを送付する
   """
   def get_pos_info(self):
       position_list = self.api.private_get_position()[0]
       if position_list['currentQty'] == 0: # sizeが0より大きければ現在LONG状態、0より小さければ現在SHORT状態と判断
           side = 'NO POSITION'
       elif position_list['currentQty'] > 0:
           side = 'LONG'
       else:
           side = 'SHORT'
       
       message = "Side:" + side + ", Size:" + str(round(position_list['currentQty'])) + ", avgEntryPrice:" + str(position_list['avgEntryPrice'])
       
       return message  
       
   """
   現状のポジション、利益の取得
   """
   def get_current_position(self):
       position_ = self.api.private_get_position()[0]
       if position_['currentQty'] == 0:
           side = 'NO POSITION'
           size = 0
           price = 0
           collateral = 0
           profit = 0
       else:
           size = position_['currentQty']
           price = position_['avgEntryPrice']
           collateral = abs(size / price / position_["leverage"])
           
           r = requests.get("https://api.cryptowat.ch/markets/bitmex/btcusd-perpetual-futures/price")
           ticker = r.json()["result"]["price"]

           profit = (ticker - price) / price * size / price
           if position_['currentQty'] > 0:
               side = 'LONG'
           else:
               side = 'SHORT'

       return {"side":side, "size":size, "price":price, "collateral":collateral, "profit":profit}

   

class Bot:
   def __init__(self, key, secret, line_token, isTestNet):
       self._lot = 10
       #何分足のデータを使うか．初期値は5分足．
       self._candleTerm = "5T"
       self._candlePeriod = "5" 
       self._candleLength = 50
       
       self.latest_order_time = datetime.datetime.now()
       
       #現在のポジション．1ならロング．-1ならショート．0ならポジションなし．
       self._pos = 0
       self.order = Order(key, secret, isTestNet)

       #ラインに稼働状況を通知
       self.line_notify_token = line_token
       self.line_notify_api = 'https://notify-api.line.me/api/notify'

       #注文執行コスト
       self._cost = 0
       
   @property
   def candleTerm(self):
       return self._candleTerm
   @candleTerm.setter
   def candleTerm(self, val):
       """
       valは"5T"，"1H"などのString
       """
       self._candleTerm = val
   @property
   def candlePeriod(self):
       return self._candlePeriod
   @candlePeriod.setter
   def candlePeriod(self, val):
       self._candlePeriod = val
       
   @property
   def candleLength(self):
       return self._candleLength
   @candleLength.setter
   def candleLength(self, val):
       self._candleLength = val
       
   @property
   def pos(self):
       return self._pos
   @pos.setter
   def pos(self, val):
       self.pos = int(val)
   @property
   def lot(self):
       return self._lot
   @lot.setter
   def lot(self, val):
       self._lot = round(val,3)
   @property
   def product_code(self):
       return self._product_code
   @product_code.setter
   def product_code(self, val):
       self._product_code = val
   
   
   def judgeForTest(self, df_candleStick):
       """
       バックテスト用の売り買い判断を行う関数．judgementリストは[買いエントリー，売りエントリー，買いクローズ（売り），売りクローズ（買い）]のリスト(つまり「二次元リスト)になっている．リスト内リストの要素は，0（シグナルなし）,シグナル点灯時価格（シグナル点灯時のみ）を取る．
       if Trueの部分にシグナル点灯条件を入れる．
       """
       judgement = [[0,0,0,0] for i in range(len(df_candleStick.index))]

       for i in range(len(df_candleStick.index)):
           #ロングエントリー
           if True:
               judgement[i][0] = 1
           #ショートエントリー
           if True:
               judgement[i][1] = 1
           #ロングクローズ
           if True:
               judgement[i][2] = 1
           #ショートクローズ
           if True:
               judgement[i][3] = 1
       return judgement

   def judgeForLoop(self):
       """
       実働時用の売り買い判断．judgementリストは[買いエントリー，売りエントリー，買いクローズ（売り），売りクローズ（買い）]のリストになっている．（値は0or1）
       """
       judgement = [0,0,0,0]
       #ロングエントリー
       if True:
           judgement[0] = 1
       #ショートエントリー
       if True:
           judgement[1] = 1
       #ロングクローズ
       if True:
           judgement[2] = 1
       #ショートクローズ
       if True:
           judgement[3] = 1
       return judgement

   def backtest(self, judgement, df_candleStick, lot, cost):
       #実際のエントリーポイント，クローズポイントを入れるリスト．(すでにポジションを持っている時など，シグナル点灯時に必ずトレードするとは限らないので．)
       longEntrySignals = []
       shortEntrySignals = []
       longCloseSignals = []
       shortCloseSignals = []
       #トレード回数を保存しておく変数．
       nOfTrade = 0
       #ポジション管理変数．1:ロング保持．-1:ショート保持．0:ノーポジ．
       pos = 0
       #損益を保存する変数．
       pl = []
       pl.append(0)
       #トレードごとの損益
       plPerTrade = []
       #取引時の価格を入れる配列．この価格でバックテストのplを計算する．（ので，どの価格で約定すると仮定するかはテストのパフォーマンスに大きく影響を与える．）
       longEntryPrice = []
       longClosePrice = []
       shortEntryPrice = []
       shortClosePrice = []

       for i in range(len(judgement)):
           #とりあえず現在のplは1回前のplと同額として代入しておき，このループでポジションをクローズする場合に更新する．
           if i > 0:
               lastPL = pl[-1]
               pl.append(lastPL)
           #エントリーロジック
           if pos == 0:
               #ロングエントリー
               if judgement[i][0] != 0:
                   pos += 1
                   longEntryPrice.append(judgement[i][0])
                   longEntrySignals.append(df_candleStick.index[i])
               #ショートエントリー
               elif judgement[i][1] != 0:
                   pos -= 1
                   shortEntryPrice.append(judgement[i][1])
                   shortEntrySignals.append(df_candleStick.index[i])
           #以下クローズロジック
           elif pos == 1:
               #ロングクローズ
               if judgement[i][2] != 0:
                   nOfTrade += 1
                   pos -= 1
                   longCloseSignals.append(df_candleStick.index[i])
                   longClosePrice.append(judgement[i][2])
                   #値幅
                   plRange = longClosePrice[-1] - longEntryPrice[-1] - cost
                   #plを更新．
                   pl[-1] = pl[-2] + plRange / longEntryPrice[-1] * lot
                   plPerTrade.append(plRange/longEntryPrice[-1]*lot)
           elif pos == -1:
               #ショートクローズ
               if judgement[i][3] != 0:
                   nOfTrade += 1
                   pos += 1
                   shortCloseSignals.append(df_candleStick.index[i])
                   shortClosePrice.append(judgement[i][3])
                   #plを更新
                   plRange = shortEntryPrice[-1] - shortClosePrice[-1] -cost
                   pl[-1] = pl[-2] + plRange / shortEntryPrice[-1] * lot
                   plPerTrade.append(plRange/shortEntryPrice[-1]*lot)
           #さらに，クローズしたと同時にエントリーシグナルが出ていた場合のロジック．
           if pos == 0:
               #ロングエントリー
               if judgement[i][0] != 0:
                   pos += 1
                   longEntryPrice.append(judgement[i][0])
                   longEntrySignals.append(df_candleStick.index[i])
               #ショートエントリー
               elif judgement[i][1] != 0:
                   pos -= 1
                   shortEntryPrice.append(judgement[i][1])
                   shortEntrySignals.append(df_candleStick.index[i])
       #最後にポジションを持っていたら，期間最後のローソク足の終値で反対売買．
       if pos == 1:
           longClosePrice.append(df_candleStick["close"][-1])
           longCloseSignals.append(df_candleStick.index[-1])
           plRange = longClosePrice[-1] - longEntryPrice[-1]
           pl[-1] = pl[-2] + plRange /longEntryPrice[-1] * lot
           pos -= 1
           nOfTrade += 1
           plPerTrade.append(plRange/longEntryPrice[-1]*lot)
       elif pos ==-1:
           shortCloseSignals.append(df_candleStick.index[-1])
           shortClosePrice.append(df_candleStick["close"][-1])
           plRange = shortEntryPrice[-1] - shortClosePrice[-1]
           pl[-1] = pl[-2] + plRange / shortEntryPrice[-1] * lot
           pos +=1
           nOfTrade += 1
           plPerTrade.append(plRange/shortEntryPrice[-1]*lot)
       return (pl, longEntrySignals, shortEntrySignals, longCloseSignals, shortCloseSignals, nOfTrade, plPerTrade)

   def describeResult(self, cost=0):
       """
       signalsは買い，売り，中立が入った配列
       """
       #比較が楽なようにロットを1枚にする．（値幅でバックテスト）
       #self.lot = 1
       import matplotlib.pyplot as plt
       
       if self.candleTerm == "5T":
           df_candleStick = self.getCandlestick()
       else:
           df_candleStick = self.processCandleStick()

       judgement = self.judgeForTest(df_candleStick)
       pl, buyEntrySignals, sellEntrySignals, buyCloseSignals, sellCloseSignals, nOfTrade, plPerTrade = self.backtest(judgement, df_candleStick, self.lot, self.cost)

       plt.figure()
       plt.subplot(211)
       plt.plot(df_candleStick.index, df_candleStick["close"])
       plt.ylabel("Price(USD)")
       ymin = min(df_candleStick["low"]) - 200
       ymax = max(df_candleStick["high"]) + 200
       plt.vlines(buyEntrySignals, ymin , ymax, "blue", linestyles='dashed', linewidth=1)
       plt.vlines(sellEntrySignals, ymin , ymax, "red", linestyles='dashed', linewidth=1)
       plt.vlines(buyCloseSignals, ymin , ymax, "black", linestyles='dashed', linewidth=1)
       plt.vlines(sellCloseSignals, ymin , ymax, "green", linestyles='dashed', linewidth=1)
       plt.subplot(212)
       plt.plot(df_candleStick.index, pl)
       plt.hlines(y=0, xmin=df_candleStick.index[0], xmax=df_candleStick.index[-1], colors='k', linestyles='dashed')
       plt.ylabel("PL(JPY)")

       #各統計量の計算および表示．
       winTrade = sum([1 for i in plPerTrade if i > 0])
       loseTrade = sum([1 for i in plPerTrade if i < 0])
       winPer = round(winTrade/(winTrade+loseTrade) * 100,2)

       winTotal = sum([i for i in plPerTrade if i > 0])
       loseTotal = sum([i for i in plPerTrade if i < 0])
       profitFactor = round(winTotal/-loseTotal, 3)

       maxProfit = max(plPerTrade)
       maxLoss = min(plPerTrade)
       
       print("start_time:", df_candleStick.index[0])
       print("end_time:", df_candleStick.index[-1])
       print("Total pl: {}USD".format(int(pl[-1])))
       print("Total pl: {}USD".format(int(pl[-1])))
       print("The number of Trades: {}".format(nOfTrade))
       print("The Winning percentage: {}%".format(winPer))
       print("The profitFactor: {}".format(profitFactor))
       print("The maximum Profit and Loss: {}USD, {}USD".format(maxProfit, maxLoss))

       plt.show()

   def getCandlestick(self):
       """
       length:データの取得期間．period:ローソク足の期間（文字列で分数を指定，Ex:5分足なら"5"）
       """

       now = datetime.datetime.now().strftime('%s') # 現在時刻の取得
       r = requests.get('https://www.bitmex.com/api/udf/history?symbol=XBTUSD&resolution='+ self.candlePeriod 
                        +'&from=' +str(int(now)-3600*self.candleLength) + '&to=' + now) # 過去xx時間分の過去データ取得
       res = r.json()
       
       df_res = pd.DataFrame(res)
       date_datetime = map(datetime.datetime.fromtimestamp, df_res["t"])
       dti = pd.DatetimeIndex(date_datetime)
       df_res = df_res.set_index(dti)
       df_res = df_res.rename(columns={'o': 'open', 'h': 'high', 'l': 'low', 'c': 'close'})
       
       #ローソク足取得
       return df_res

   def processCandleStick(self):
       """
       1分足データから各時間軸のデータを作成.timeScaleには5T（5分），H（1時間）などの文字列を入れる
       """
       df_candleStick = self.getCandlestick()
       processed_candleStick = df_candleStick.resample(self.candleTerm).agg({'open': 'first','high':'max','low': 'min','close': 'last'})
       processed_candleStick = processed_candleStick.dropna()
       return processed_candleStick
       

   def lineNotify(self, message, fileName=None):
       """
       Lineに通知を送信．
       画像ファイルの有無で処理を分ける
       """
       payload = {'message': message}
       headers = {'Authorization': 'Bearer ' + self.line_notify_token}
       if fileName == None:
           try:
               requests.post(self.line_notify_api, data=payload, headers=headers)
           except:
               pass
       else:
           try:
               files = {"imageFile": open(fileName, "rb")}
               requests.post(self.line_notify_api, data=payload, headers=headers, files = files)
           except:
               pass
       

   def loop(self,candleTerm=None):
       """
       注文の実行ループを回す関数
       """
       pos = 0
           
       pl = []
       pl.append(0)
       lot = self.lot
       
       while True:
           try:
               """
               ローソク足の取得
               """
               try:
                   if self.candleTerm == "5T":
                       df_candleStick = self.getCandlestick()
                   else:
                       df_candleStick = self.processCandleStick()
               except:
                   print("Unknown error happend when you requested candleStick")
               finally:
                   pass
                              
               """
               エントリー、クローズ判定
               """
               judgement = self.judgeForLoop(df_candleStick)
    
               """
               ここからエントリー、クローズ処理
               """
               if pos == 0:
                   
                   #ロングエントリー
                   if judgement[0]:
                       self.latest_order_time = datetime.datetime.now()
                       self.order.market(size=lot, side="buy")
                       pos += 1
                       message = "Long entry"
                       self.lineNotify(message)
                       #エントリー時の足の時刻を取得
                       self.entry_candle_time = df_candleStick.index[-1]
                       
                   #ショートエントリー
                   elif judgement[1]:
                       self.latest_order_time = datetime.datetime.now()
                       self.order.market(size=lot,side="sell")
                       pos -= 1
                       message = "Short entry"
                       self.lineNotify(message)
                       
               elif pos == 1:
                   #ロングクローズ
                          
                   if judgement[2]:
                       
                       self.latest_order_time = datetime.datetime.now()
                       self.order.market(size=lot,side="sell")
                       pos -= 1
    
                       message = "Long close"
                       print(message)
                       
                       self.lineNotify(message)
               elif pos == -1:
                   
                   #ショートクローズ
                   if judgement[3]:
    
                       self.latest_order_time = datetime.datetime.now()
                       self.order.market(size=lot, side="buy")
                       pos += 1
                       #ラインに通知
                       message = "Short close"
                       print(message)
                       self.lineNotify(message)
                       
    #           さらに，クローズと同時にエントリーシグナルが出ていたときの処理．
               if pos == 0:
                   #ロングエントリー
                   if judgement[0]:
                       self.latest_order_time = datetime.datetime.now()
                       self.order.market(size=lot, side="buy")
                       pos += 1
                       message = "Long entry"
                       self.lineNotify(message)
                   #ショートエントリー
                   elif judgement[1]:
                       self.latest_order_time = datetime.datetime.now()
                       self.order.market(size=lot,side="sell")
                       pos -= 1
                       message = "Short entry"
                       self.lineNotify(message)
                       
               try:
                   message = self.order.get_pos_info()
               except:
    #               print("error")
                   message = "Waiting."
                   pass
               #5分ごとに通知
               if datetime.datetime.now().minute % 5 == 0 and datetime.datetime.now().second < 30:
                   print(message)
                   self.lineNotify(message)
        
           except:
               print("unknown error occurred")
        
           time.sleep(30)

if __name__ == '__main__':
   pass
