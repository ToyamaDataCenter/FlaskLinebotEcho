import os
import sys
import json
import datetime
import time
from flask import Flask, request, jsonify
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

from azure.storage.blob import BlockBlobService, AppendBlobService, PublicAccess

# メモ
# 新しいパッケージをインストールしたときは
# requirements.txt を更新しましょう。
# [Python 環境] - [env] を右クリックするとメニューにあります。
#
# そして、Azure に発行したあとに、Kudu で requirements.txt を元にパッケージを更新しましょう。
# Kudu に移動するには https://[app name].scm.azurewebsites.net/
# app name と azurewebsites の間に .scm. を入れる。
# Python フォルダーに移動してから
# python -m pip install --upgrade -r /home/site/wwwroot/requirements.txt
#
# あとは、Azure の App service を先起動すると安心するかも。


# Create an instance of the Flask class that is the WSGI application.
# The first argument is the name of the application module or package,
# typically __name__ when using a single module.
app = Flask(__name__)
app.config[ 'JSON_AS_ASCII' ]   = False


account_name        = r'linebotpythonsample';
account_key         = r'9mE0ZNgDyv8VOE0l1hG8ZJtptXI/xiwlPsTiETjKRsN1cwHZUyc+O//G8teqP+F9T0FUu/nDTjL5NBYufiRzMg==';
log_container_name  = r'log-files';
log_file_name       = r"{0:%Y-%m-%dT%H-%M-%S.log}".format( datetime.datetime.now() )


# get channel_secret and channel_access_token from your environment variable

channel_access_token    = os.getenv( 'LINE_CHANNEL_ACCESS_TOKEN', None )
channel_secret          = os.getenv( 'LINE_CHANNEL_SECRET', None )

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)

if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api    = LineBotApi( channel_access_token )
handler         = WebhookHandler( channel_secret )


hellopython = "Hello Python!";

def CreateLogFile():
    """ ログファイルを作成する。WriteLog を呼び出す前に実行すること。 """
    szRet = "";
    try:
        szRet = "AppendBlobService";
        blob_service    = AppendBlobService(
            account_name,
            account_key
        );
        szRet = "create_container";
        bIsExists = blob_service.exists(
            log_container_name
        );
        if bIsExists:
            pass;
        else:
            blob_service.create_container(
                log_container_name,
                public_access=PublicAccess.Blob
            );
        bIsExists = blob_service.exists(
            log_container_name,
            log_file_name
        );
        if bIsExists:
            szRet = "already blob."
        else:
            szRet = "create_blob";
            blob_service.create_blob(
                log_container_name,
                log_file_name
            );
        szRet = "OK";
    except:
        #szRet = "Log exception";
        pass;
    return szRet;

def WriteLog( txt ):
    """ ログファイルにテキストを出力する。末尾に改行コードが追加される。 """
    szRet = "";
    try:
        szRet = "AppendBlobService";
        blob_service    = AppendBlobService(
            account_name,
            account_key
        );
        szRet = "append_blob_from_text";
        blob_service.append_blob_from_text(
            log_container_name,
            log_file_name,
            r"{0:%Y-%m-%d %H:%M:%S}".format( datetime.datetime.now() ) + r" : " + txt + "\r\n"
        )
        szRet = "OK";
    except:
        #szRet = "Log exception";
        pass;
    return szRet;
#

def WriteBlob( blob_name, txt ):
    """ 単一 BLOB ファイルを作成しテキストを保存する。 """
    try:
        #blob_name = r'sample.txt';

        hellopython = "BlockBlobService"
        blob_service = BlockBlobService(account_name, account_key)

        hellopython = "create_container"
        blob_service.create_container(
            log_container_name,
            public_access=PublicAccess.Blob
        )

        hellopython = "create_blob_from_bytes"
        #blob_service.create_blob_from_bytes(
        #    log_container_name,
        #    log_blob_name,
        #    b'<center><h1>Hello World!</h1></center>',
        #    content_settings=ContentSettings('text/html')
        #)

        hellopython = "create_blob_from_text"
        blob_service.create_blob_from_text(
            log_container_name,
            blob_name,
            txt
        )

        hellopython = "make_blob_url"
        print(blob_service.make_blob_url(log_container_name, log_blob_name))
        hellopython = "Hello Python!"
    except:
        print( r"Exception.")
#def WriteBlob( blob_name, txt ):

# ログファイルを作成する
CreateLogFile();

# Flask route decorators map / and /hello to the hello function.
# To add other resources, create functions that generate the page contents
# and add decorators to define the appropriate resource locators for them.

@app.route('/')
@app.route('/hello')
def hello():
    return hellopython

@app.route( '/ver', methods = [ 'GET' ] )
def ver():
    """ バージョン情報を表示する """
    szText = WriteLog( "Show version info." );
    if "OK" == szText:
        szText = sys.version;
    return szText


@app.route( '/callback', methods=[ 'POST' ] )
def LinePost():
    """  LINE からメッセージがポストされたとき  """
    szProgress = "";
    WriteLog( "LinePost() called." )
    try:
        szText  = "";

        szProgress = "for でヘッダーリスト作成中";
        for szKey, szValue in request.headers.items():
            szText += str( szKey ) + " : " + str( szValue ) + "\r\n"
        #for
        szText += "\r\n"

        # get request body as text
        szProgress = "body データ取得中";
        body = request.get_data( as_text = True )
        app.logger.info( "Request body: " + body )
        szText += body;
        WriteBlob( "linepost.txt", body );

        szProgress = "ヘッダーから 'X-Line-Signature' 取得中";
        signature = request.headers[ 'X-Line-Signature' ]

        # parse webhook body
        szProgress = "webhook body を解析中";
        try:
            events = parser.parse( body, signature )
        except InvalidSignatureError as e:
            WriteLog( "parser.parse() failed." + "\r\n" + e.message );
            abort(400)

        # if event is MessageEvent and message is TextMessage, then echo text
        szProgress = "events を解析中";
        for event in events:
            if not isinstance( event, MessageEvent ):
                continue

            if not isinstance( event.message, TextMessage ):
                continue

            try:
                szProgress = "リプライメッセージ送信中";
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(
                       text = event.message.text
                    )
                )
            except Exception as e:
                WriteLog( "line_bot_api.reply_message() failed." + "\r\n" + e.message );
        #for event in events:
    except Exception as e:
        WriteLog( szProgress + "でエラー発生。" + "\r\n" + e.message );
        abort(400)

    WriteLog( "Exit LinePost()." );
    return 'OK'

@app.route( '/callback', methods=[ 'GET' ] )
def LineGet():
    return "Ok.This uri is exists.";

# 何か
if __name__ == '__main__':
    # Run the app server on localhost:4449
    app.run( host = 'localhost', port = 4449 )
