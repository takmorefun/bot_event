#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 31 16:32:09 2018

@author: matsumototakuya
"""
#テクニカル系botの基底クラス．ローソク足でのバックテスト．注文処理を実装．
import pybitflyer
import json
import csv
import math
import pandas as pd
import time
import requests
import datetime

class Order:
   def __init__(self, key, secret):
       self.product_code = "FX_BTC_JPY"
       self.key = key
       self.secret = secret
       self.api = pybitflyer.API(self.key, self.secret)
       #最新の注文リスト
       self.latest_exec_info = []

   def limit(self, side, price, size, minute_to_expire=None):
       print("Order: Limit. Side : {}".format(side))
       response = {"status":"internalError in order.py"}
       try:
           response = self.api.sendchildorder(product_code=self.product_code, child_order_type="LIMIT", side=side, price=price, size=size, minute_to_expire = minute_to_expire)
       except:
           pass
       while "status" in response:
           try:
               response = self.api.sendchildorder(product_code=self.product_code, child_order_type="LIMIT", side=side, price=price, size=size, minute_to_expire = minute_to_expire)
           except:
               pass
           time.sleep(3)
       return response

   def market(self, side, size, minute_to_expire= None):
       print("Order: Market. Side : {}".format(side))
       response = {"status": "internalError in order.py"}
       try:
           response = self.api.sendchildorder(product_code=self.product_code, child_order_type="MARKET", side=side, size=size, minute_to_expire = minute_to_expire)
           print(response)
       except:
           pass
       while "status" in response:
           try:
               response = self.api.sendchildorder(product_code=self.product_code, child_order_type="MARKET", side=side, size=size, minute_to_expire = minute_to_expire)
               print(response)
           except:
               pass
           time.sleep(3)
       return response

   def stop(self, side, size, trigger_price, minute_to_expire=None):
       print("Order: Stop. Side : {}".format(side))
       response = {"status": "internalError in order.py"}
       try:
           response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "STOP", "side": side, "size": size,"trigger_price": trigger_price, "minute_to_expire": minute_to_expire}])
       except:
           pass
       while "status" in response:
           try:
               response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "STOP", "side": side, "size": size,"trigger_price": trigger_price, "minute_to_expire": minute_to_expire}])
           except:
               pass
           time.sleep(3)
       return response

   def stop_limit(self, side, size, trigger_price, price, minute_to_expire=None):
       print("Side : {}".format(side))
       response = {"status": "internalError in order.py"}
       try:
           response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "STOP_LIMIT", "side": side, "size": size,"trigger_price": trigger_price, "price": price, "minute_to_expire": minute_to_expire}])
       except:
           pass
       while "status" in response:
           try:
               response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "STOP_LIMIT", "side": side, "size": size,"trigger_price": trigger_price, "price": price, "minute_to_expire": minute_to_expire}])
           except:
               pass
       return response

   def trailing(self, side, size, offset, minute_to_expire=None):
       print("Side : {}".format(side))
       response = {"status": "internalError in order.py"}
       try:
           response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "TRAIL", "side": side, "size": size, "offset": offset, "minute_to_expire": minute_to_expire}])
       except:
           pass
       while "status" in response:
           try:
               response = self.api.sendparentorder(order_method="SIMPLE", parameters=[{"product_code": self.product_code, "condition_type": "TRAIL", "side": side, "size": size, "offset": offset, "minute_to_expire": minute_to_expire}])
           except:
               pass
       return response
       
   
       
   """
   現状のポジションの損益を送付する
   """
   def get_pos_info(self):
       message = "waiting..."
       position_list = self.api.getpositions(product_code="FX_BTC_JPY")
       df_position_list = pd.DataFrame(position_list)
       
       if len(df_position_list) > 0:
           message = "SIDE:" +  df_position_list.iloc[0]["side"] + ", PRICE:" + str(df_position_list["price"].mean()) + ", PL:" + str(df_position_list["pnl"].sum())
       return message
   """
   現状のポジション、利益の取得
   """
   def get_current_position(self):
       position_list = self.api.getpositions(product_code="FX_BTC_JPY")
       df_position_list = pd.DataFrame(position_list)
       if len(df_position_list) == 0:
           side = 'NO POSITION'
           size = 0
           price = 0
           collateral = 0
           profit = 0
       else:
           side = df_position_list.iloc[0]["side"]
           size = df_position_list["size"].sum()

           df_position_list["price_unit"] = df_position_list["price"] *df_position_list["size"]
           price = df_position_list["price_unit"].sum() / df_position_list["size"].sum()
           
           collateral = df_position_list["require_collateral"].sum()
           profit = df_position_list["pnl"].sum()

       return {"side":side, "size":size, "price":price, "collateral":collateral, "profit":profit}


class Bot:
   def __init__(self, key, secret, line_token):
       
       self._lot = 0.1
       self._product_code = "FX_BTC_JPY"
       #何分足のデータを使うか．初期値は1分足．
       self._candleTerm = "1T"
       self._period = "60"
       self._number = 300
       
       #現在のポジション．1ならロング．-1ならショート．0ならポジションなし．
       self._pos = 0
       self.order = Order(key, secret)

       #ラインに稼働状況を通知
       self.line_notify_token = line_token
       self.line_notify_api = 'https://notify-api.line.me/api/notify'
       
       #注文執行コスト
       self._cost = 0

   @property
   def cost(self):
       return self._cost

   @cost.setter
   def cost(self, value):
       self._cost = value

   @property
   def margin(self):
       return self._margin
   @margin.setter
   def margin(self, val):
       self._margin = val
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
   def executions(self):
       return self._executions
   @executions.setter
   def executions(self, val):
       self._executions = val
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
   @property
   def period(self):
       return self._period
   @period.setter
   def period(self, val):
       self._period = val
   @property
   def number(self):
       return self._number
   @number.setter
   def number(self, val):
       self._number = val

   def calculateLot(self, margin):
       """
       証拠金からロットを計算する関数．
       """
       lot = math.floor(margin*10**(-4))*10**(-2)
       return round(lot,2)
       
   
   
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
                   pl[-1] = pl[-2] + plRange * lot
                   plPerTrade.append(plRange*lot)
           elif pos == -1:
               #ショートクローズ
               if judgement[i][3] != 0:
                   nOfTrade += 1
                   pos += 1
                   shortCloseSignals.append(df_candleStick.index[i])
                   shortClosePrice.append(judgement[i][3])
                   #plを更新
                   plRange = shortEntryPrice[-1] - shortClosePrice[-1] -cost
                   pl[-1] = pl[-2] + plRange * lot
                   plPerTrade.append(plRange*lot)
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
           pl[-1] = pl[-2] + plRange * lot
           pos -= 1
           nOfTrade += 1
           plPerTrade.append(plRange*lot)
       elif pos ==-1:
           shortCloseSignals.append(df_candleStick.index[-1])
           shortClosePrice.append(df_candleStick["close"][-1])
           plRange = shortEntryPrice[-1] - shortClosePrice[-1]
           pl[-1] = pl[-2] + plRange * lot
           pos +=1
           nOfTrade += 1
           plPerTrade.append(plRange*lot)
       return (pl, longEntrySignals, shortEntrySignals, longCloseSignals, shortCloseSignals, nOfTrade, plPerTrade)

   def describeResult(self):
       """
       signalsは買い，売り，中立が入った配列
       """
       import matplotlib.pyplot as plt
       
       candleStick = self.getCandlestick()
           

       if self.candleTerm != "1D":
           df_candleStick = self.fromListToDF(candleStick)
       else:
           df_candleStick = self.processCandleStick(candleStick)
           

       judgement = self.judgeForTest(df_candleStick)
       pl, buyEntrySignals, sellEntrySignals, buyCloseSignals, sellCloseSignals, nOfTrade, plPerTrade = self.backtest(judgement, df_candleStick, self.lot, self.cost)

       plt.figure()
       plt.subplot(211)
       plt.plot(df_candleStick.index, df_candleStick["close"])
       plt.ylabel("Price(JPY)")
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

       print("Total pl: {}JPY".format(int(pl[-1])))
       print("The number of Trades: {}".format(nOfTrade))
       print("The Winning percentage: {}%".format(winPer))
       print("The profitFactor: {}".format(profitFactor))
       print("The maximum Profit and Loss: {}JPY, {}JPY".format(maxProfit, maxLoss))

       plt.show()

   def getCandlestick(self):
       """
       number:ローソク足の数．period:ローソク足の期間（文字列で秒数を指定，Ex:1分足なら"60"）．cryptowatchはときどきおかしなデータ（price=0）が含まれるのでそれを除く．
       """
       #ローソク足の時間を指定
       periods = [self.period]
       #クエリパラメータを指定
       query = {"periods":','.join(periods)}
       #ローソク足取得
       res = json.loads(requests.get("https://api.cryptowat.ch/markets/bitflyer/btcfxjpy/ohlc",params=query).text)["result"]
       #ローソク足のデータを入れる配列．
       data = []
       for i in periods:
           row = res[i]
           length = len(row)
           for column in row[:length-(self.number+1):-1]:
               #dataへローソク足データを追加．
               if column[4] != 0:
                   column = column[0:6]
                   data.append(column)
       return data[::-1]

   def fromListToDF(self, candleStick):
       """
       Listのローソク足をpandasデータフレームへ．
       """
       date = [price[0] for price in candleStick]
       priceOpen = [int(price[1]) for price in candleStick]
       priceHigh = [int(price[2]) for price in candleStick]
       priceLow = [int(price[3]) for price in candleStick]
       priceClose = [int(price[4]) for price in candleStick]
       date_datetime = map(datetime.datetime.fromtimestamp, date)
       dti = pd.DatetimeIndex(date_datetime)
       df_candleStick = pd.DataFrame({"open" : priceOpen, "high" : priceHigh, "low": priceLow, "close" : priceClose}, index=dti)
       return df_candleStick

   def processCandleStick(self, candleStick):
       """
       1分足データから各時間軸のデータを作成.timeScaleには5T（5分），H（1時間）などの文字列を入れる
       """
       df_candleStick = self.fromListToDF(candleStick)
       processed_candleStick = df_candleStick.resample(self.candleTerm).agg({'open': 'first','high':'max','low': 'min','close': 'last'})
       processed_candleStick = processed_candleStick.dropna()
       return processed_candleStick

   def readDataFromFile(self,filename):
       """
       csvファイル（ヘッダなし）からohlcデータを作成．
       """
       for i in range(1, 10, 1):
           with open(filename, 'r', encoding="utf-8") as f:
               reader = csv.reader(f)
               header = next(reader)
               for row in reader:
                   candleStick = [row for row in reader if row[4] != "0"]
       dtDate = [datetime.datetime.strptime(data[0], '%Y-%m-%d %H:%M:%S') for data in candleStick]
       dtTimeStamp = [dt.timestamp() for dt in dtDate]
       for i in range(len(candleStick)):
           candleStick[i][0] = dtTimeStamp[i]
       candleStick = [[float(i) for i in data] for data in candleStick]
       return candleStick

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

   def describePLForNotification(self, pl, df_candleStick):
       """
       LineNotifyに損益グラフを送るための関数．
       """
       import matplotlib
       matplotlib.use('Agg')
       import matplotlib.pyplot as plt
       close = df_candleStick["close"]
       index = range(len(pl))
       # figure
       fig = plt.figure(figsize=(20,12))
       #for price
       ax = fig.add_subplot(2, 1, 1)
       ax.plot(df_candleStick.index, close)
       ax.set_xlabel('Time')
       # y axis
       ax.set_ylabel('The price[JPY]')
       #for PLcurve
       ax = fig.add_subplot(2, 1, 2)
       # plot
       ax.plot(index, pl, color='b', label='The PL curve')
       # x axis
       ax.set_xlabel('The number of Trade')
       # y axis
       ax.set_ylabel('The estimated Profit/Loss(JPY)')
       # legend and title
       ax.legend(loc='best')
       ax.set_title('The PL curve(Time span:{})'.format(self.candleTerm))
       # save as png
       today = datetime.datetime.now().strftime('%Y%m%d')
       number = "_" + str(len(pl))
       fileName = today + number + ".png"
       plt.savefig(fileName)
       plt.close()
       return fileName

   def loop(self,candleTerm=None, period=None):
       """
       注文の実行ループを回す関数
       """
       pos = 0
       pl = []
       pl.append(0)
       lastPositionPrice = 0
       lot = self.lot
       
       current_pos = self.order.get_current_position()
       if current_pos["side"] == "SELL":
           pos -= 1
       elif current_pos["side"] == "BUY":
           pos += 1           
           
       while True:
           
           try:
               try:
                   candleStick = self.getCandlestick()
               except:
                   print("Unknown error happend when you requested candleStick")
               finally:
                   pass
               
               if candleTerm != "1D":
                   df_candleStick = self.fromListToDF(candleStick)
               else:
                   df_candleStick = self.processCandleStick(candleStick)
                   
               #ポジションの判定処理
               judgement = self.judgeForLoop(df_candleStick)
               
               try :
                   ticker = self.order.api.ticker(product_code=self.product_code)
                   best_ask = ticker["best_ask"]
                   best_bid = ticker["best_bid"]
               except:
                   print("Unknown error happend when you requested ticker.")
               finally:
                   pass
               
               message = ""
               
               """
               ここからエントリー，クローズ処理
               """
               
               if pos == 0:
                   #ロングエントリー
                   #現在のpositionをチェックし、既に存在する場合はpositionをセットする
                   try:
                       position_list = self.order.api.getpositions(product_code="FX_BTC_JPY")
                       df_position_list = pd.DataFrame(position_list)
                       
                       if len(df_position_list) > 0:
                           side_ = df_position_list.iloc[0]["side"]
                           if side_ == "BUY":
                               message = "long position already exist"
                               self.lineNotify(message)
                               pos += 1
                           else:
                               message = "short position already exist"
                               self.lineNotify(message)                           
                               pos -= 1
                   except:
                       pass
                   
                   if judgement[0]:
                       print(datetime.datetime.now())
                       self.order.market(size=lot, side="BUY")
                       pos += 1
                       message = "Long entry. Lot:{}, Price:{}".format(lot, best_ask)
                       self.lineNotify(message)
                       
                       lastPositionPrice = best_ask
                   #ショートエントリー
                   elif judgement[1]:
                       print(datetime.datetime.now())
                       self.order.market(size=lot,side="SELL")
                       pos -= 1
                       message = "Short entry. Lot:{}, Price:{}, ".format(lot, best_bid)
                       self.lineNotify(message)
                       
                       lastPositionPrice = best_bid
               elif pos == 1:
                   #ロングクローズ
                   #現在のpositionをチェック
                   try:
                       current_pos = self.order.get_current_position()
                       
                       
                       #現在のpositionをチェックし、longじゃない場合の処理
                       if current_pos["side"] == "NO POSITION":
                           message = "long position closed manually, currently no position"
                           self.lineNotify(message)
                           pos -= 1
                           continue
                       elif current_pos["side"] == "SELL":
                           message = "long position closed manually, currently short position"
                           self.lineNotify(message)
                           pos -= 2
                           continue
                           
                       #証拠金に対する利益率を計算
                       profit_rate = current_pos["profit"] / current_pos["collateral"]
                       print("証拠金(JPY):",current_pos["collateral"],"証拠金利益率(%):", profit_rate*100)

                       if profit_rate > self.profit_threshold:
                           message = "profit_rate over profit threshold, close position"
                           self.order.market(size=lot, side="SELL")
                           
                           print(message)
                           self.lineNotify(message)
                           pos -= 1
                           continue
                           
                       elif profit_rate < self.loss_threshold:
                           message = "profit_rate over loss threshold, close position"
                           self.order.market(size=lot, side="SELL")
                           
                           print(message)
                           self.lineNotify(message)
                           pos -= 1
                           continue
                   except:
                       #exception発生時はpass(ネットワークエラー発生のため)
                       pass
                   
                   if judgement[2]:
                       
                       print(datetime.datetime.now())
                       self.order.market(size=lot,side="SELL")
                       pos -= 1
                       plRange = best_bid - lastPositionPrice
                       pl.append(pl[-1] + plRange * lot)
    
                       message = "Long close. Lot:{}, Price:{}, pl:{}".format(lot, best_bid, pl[-1])
                       print(message)
                       
    #                   fileName = self.describePLForNotification(pl, df_candleStick)
                       self.lineNotify(message)
               elif pos == -1:
                   #ショートクローズ
                   #現在のpositionをチェック
                   try:
                       current_pos = self.order.get_current_position()
                       
                       
                       #現在のpositionをチェックし、longじゃない場合の処理
                       if current_pos["side"] == "NO POSITION":
                           message = "short position closed manually, currently no position"
                           self.lineNotify(message)
                           pos += 1
                           continue
                       elif current_pos["side"] == "BUY":
                           message = "short position closed manually, currently short position"
                           self.lineNotify(message)
                           pos += 2
                           continue
                           
                       #証拠金に対する利益率を計算
                       profit_rate = current_pos["profit"] / current_pos["collateral"]
                       print("証拠金(JPY):",current_pos["collateral"],"証拠金利益率(%):", profit_rate*100)

                       if profit_rate > self.profit_threshold:
                           message = "profit_rate over profit threshold, close position"
                           self.order.market(size=lot, side="BUY")
                           
                           print(message)
                           self.lineNotify(message)
                           pos += 1
                           continue
                           
                       elif profit_rate < self.loss_threshold:
                           message = "profit_rate over loss threshold, close position"
                           self.order.market(size=lot, side="BUY")
                           
                           print(message)
                           self.lineNotify(message)
                           pos += 1
                           continue
                   except:
                       #exception発生時はpass(ネットワークエラー発生のため)
                       pass
                   
                   if judgement[3]:

                       print(datetime.datetime.now())
                       self.order.market(size=lot, side="BUY")
                       pos += 1
                       plRange = lastPositionPrice - best_ask
                       pl.append(pl[-1] + plRange * lot)
                       #ラインに通知
                       message = "Short close. Lot:{}, Price:{}, pl:{}".format(lot, best_ask, pl[-1])
                       print(message)
    #                   fileName = self.describePLForNotification(pl, df_candleStick)
                       self.lineNotify(message)
                       
    #           さらに，クローズと同時にエントリーシグナルが出ていたときの処理．
               if pos == 0:
                   #ロングエントリー
                   if judgement[0]:
                       print(datetime.datetime.now())
                       self.order.market(size=lot, side="BUY")
                       pos += 1
                       message = "Long entry. Lot:{}, Price:{}".format(lot, best_ask)
                       self.lineNotify(message)
                       lastPositionPrice = best_ask
                   #ショートエントリー
                   elif judgement[1]:
                       print(datetime.datetime.now())
                       self.order.market(size=lot,side="SELL")
                       pos -= 1
                       message = "Short entry. Lot:{}, Price:{}".format(lot, best_bid)
                       self.lineNotify(message)
                       lastPositionPrice = best_bid
               try:
                   message = self.order.get_pos_info()
               except:
                   print("error occurred during get current position")
                   message = "Waiting."
                   pass
               #5分ごとに通知
               if datetime.datetime.now().minute % 5 == 0 and datetime.datetime.now().second < 30:
                   print(message)
                   self.lineNotify(message)
           except:
               print("error occurred during processing")
               pass
           
           #次の判例処理まで待機
           time.sleep(29)

if __name__ == '__main__':
   pass
