import bot_bitmex
import numpy as np
import datetime

"""
"【買い注文】
5区間の移動平均線と30区間の移動平均線をみて、5区間の移動平均線が30区間の移動平均線を下から抜けた場合
【売り注文】
5分足の移動平均線と30分足の移動平均線をみて、5分足の移動平均線が30分足の移動平均線を上から抜けた場合
【ポジションクローズ】
移動平均線の交差が注文時点と逆になった時
【ローソク足】使用するローソク足の期間
5分足"
"""

class moving_average(bot_bitmex.Bot):
    def __init__(self, key, secret, line_token, isTestNet):
        
        self.MA_period_fast = 5
        self.MA_period_slow = 30
        
        super().__init__(key, secret, line_token, isTestNet)
        
    """
    function for backtest
    エントリー／クローズは、シグナル／逆シグナル点灯なので、あくまで参考程度にご使用ください
    """
    def judgeForTest(self,candle):
        
        Typical_price = (candle["close"] + candle["high"] + candle["low"]) / 3
                         
        candle["5SMA"] = candle["close"].rolling(self.MA_period_fast).mean()
        candle["30SMA"] = candle["close"].rolling(self.MA_period_slow).mean()
        
        
        judgement = [[0,0,0,0] for i in range(len(candle))]
        
        for loop_cnt in range(3, len(candle)):
            
            long_flag = (candle.iloc[loop_cnt-2]["5SMA"] < candle.iloc[loop_cnt-2]["30SMA"]) & \
                        (candle.iloc[loop_cnt-1]["5SMA"] > candle.iloc[loop_cnt-1]["30SMA"]) 
                        
            short_flag = (candle.iloc[loop_cnt-2]["5SMA"] > candle.iloc[loop_cnt-2]["30SMA"]) & \
                        (candle.iloc[loop_cnt-1]["5SMA"] < candle.iloc[loop_cnt-1]["30SMA"]) 
            
            if long_flag:
                judgement[loop_cnt][0] = Typical_price[loop_cnt]
                judgement[loop_cnt][3] = Typical_price[loop_cnt]

            if short_flag:
                judgement[loop_cnt][1] = Typical_price[loop_cnt]
                judgement[loop_cnt][2] = Typical_price[loop_cnt]

        return judgement 
    
    
    def judgeForLoop(self, df_candle_data):
        
        df_candle_data["5SMA"] = df_candle_data["close"].rolling(self.MA_period_fast).mean()
        df_candle_data["30SMA"] = df_candle_data["close"].rolling(self.MA_period_slow).mean()
        
        """
        ロング、ショートの判定
        """
        judgement = [0, 0, 0, 0]
        
        long_flag = (df_candle_data.iloc[-2]["5SMA"] < df_candle_data.iloc[-2]["30SMA"]) & \
                    (df_candle_data.iloc[-1]["5SMA"] > df_candle_data.iloc[-1]["30SMA"]) 
                    
        short_flag = (df_candle_data.iloc[-2]["5SMA"] > df_candle_data.iloc[-2]["30SMA"]) & \
                    (df_candle_data.iloc[-1]["5SMA"] < df_candle_data.iloc[-1]["30SMA"]) 
        
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("current_time:",now)
        print("5SMA:", int(df_candle_data.iloc[-2]["5SMA"]) ,"30SMA:" ,int(df_candle_data.iloc[-2]["30SMA"]))
        print("5SMA", int(df_candle_data.iloc[-1]["5SMA"])  ,"30SMA:"  ,int(df_candle_data.iloc[-1]["30SMA"]))
        print("long_flag:" + str(long_flag) + " short_flag:" + str(short_flag))
        
        if long_flag:
            judgement[0] = 1
            judgement[3] = 1
        
        if short_flag == True:
            judgement[1] = 1
            judgement[2] = 1
        
        return judgement
    
if __name__ == "__main__":
    
    
    """
    bitmex API key
    """
    key = "[自身のbitmexのAPIキーを入力]"
    secret = "[APIキーに対応するsecretキーを入力]"
    
    """
    line token
    tokenを登録すると、5分に一回現在のポジションと利益が通知されます
    通知不要であれば、特に設定する必要はありません
    tokenの取得方法についてはこちらを参照ください
    https://qiita.com/iitenkida7/items/576a8226ba6584864d95
    
    """
    line_token = "[line notify tokenを入力]"
    isTestNet = False
    
    #botの初期化
    MA_bot = moving_average(key, secret, line_token, isTestNet)
    
    #パラメーターを調整(使用するローソク足)
    MA_bot.candleTerm = "15T"
    MA_bot.candlePeriod = "5"
    MA_bot.candleLength = 100
    
    """
    ロットの設定
    自身の資産に併せてロットを設定してください
    """
    MA_bot.lot = 0.1
    
    """
    バックテストを実行したい場合は、test_flg = Trueに設定して実行してください
    """
    test_flg = True
    
    if test_flg:
        MA_bot.describeResult()
    else:
        MA_bot.loop()
    
    
    