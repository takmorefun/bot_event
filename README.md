# bot_event
document for bot event

# python環境構築
## anacondaのインストール
以下URLよりanacondaサイトにアクセスし、python3.6をダウンロードしてください。

【windows】
https://www.anaconda.com/download/#windows

【macos】
https://www.anaconda.com/download/#macos

　ダウンロードしたインストーラパッケージをダブルクリックして起動します。
 
 指示通りに進めていけばインストール完了です。
 
## 必要なパッケージのインストール
ボットの構築するために、追加でインストールしなければならないのは以下パッケージになります。

- pybitflyer(bitflyerを使う場合)
- ccxt(bitmexを使う場合)

パッケージのインストールはpipコマンドを使用して行います。

ターミナル（windowsだとコマンドプロンプト）を起動して、以下コマンドを実行して下さい

$ pip install pybtflyer

$ pip install ccxt

これで、環境構築は完了です。


