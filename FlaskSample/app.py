
""" LINE BOT アプリ """

#///////////////////////////////////////////////////////////////////////////////////////
#// 
#// 
import os
import sys
import json
import datetime
import time

from flask import (
   Flask,
   request,
   jsonify,
   abort
)

from linebot import (
    LineBotApi,
    WebhookHandler,
    WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent,
    TextMessage,
    ImageMessage,
    TextSendMessage,
)

from azure.storage.blob import (
    BlockBlobService,
    AppendBlobService,
    PublicAccess
)

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


#///////////////////////////////////////////////////////////////////////////////////////
#// 共有インスタンス
#// 
# Create an instance of the Flask class that is the WSGI application.
# The first argument is the name of the application module or package,
# typically __name__ when using a single module.
app = Flask(__name__)
app.config[ 'JSON_AS_ASCII' ]   = False

DEBUG_MODE  = bool(os.getenv( 'DEBUG_MODE', False ))

account_name        = os.getenv( 'AZURE_STORAGE_ACCOUNT_NAME', None );
account_key         = os.getenv( 'AZURE_STORAGE_ACCOUNT_KEY',  None );
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
parser          = WebhookParser( channel_secret )


hellopython = "Hello Python!";

def CreateLogFile():
    """ ログファイルを作成する。WriteLog を呼び出す前に実行すること。 """
    szRet = "";
    if( DEBUG_MODE ):
        return( "Debug モードのためスキップします。" );

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
    if( DEBUG_MODE ):
        print( r"{0:%Y-%m-%d %H:%M:%S}".format( datetime.datetime.now() ) + r" : " + txt + "\r\n" );
        return( "Debug モードのためスキップしました。" );

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
    #try

    return szRet;
#

def WriteBlob( blob_name, txt ):
    """ 単一 BLOB ファイルを作成しテキストを保存する。 """
    szRet   = ""
    if( DEBUG_MODE ):
        return( "Debug モードのため書き込みをしません。" );

    try:
        #blob_name = r'sample.txt';

        szRet = "BlockBlobService"
        blob_service = BlockBlobService(account_name, account_key)

        szRet = "create_container"
        blob_service.create_container(
            log_container_name,
            public_access=PublicAccess.Blob
        )

        szRet = "create_blob_from_bytes"
        #blob_service.create_blob_from_bytes(
        #    log_container_name,
        #    log_blob_name,
        #    b'<center><h1>Hello World!</h1></center>',
        #    content_settings=ContentSettings('text/html')
        #)

        szRet = "create_blob_from_text"
        blob_service.create_blob_from_text(
            log_container_name,
            blob_name,
            txt
        )

        szRet = "make_blob_url"
        print(blob_service.make_blob_url(log_container_name, log_blob_name))
        szRet = "OK"
    except:
        print( r"Exception.")
    #try

    return szRet;
#def WriteBlob( blob_name, txt ):

# ログファイルを作成する
CreateLogFile();

# Flask route decorators map / and /hello to the hello function.
# To add other resources, create functions that generate the page contents
# and add decorators to define the appropriate resource locators for them.

@app.route('/')
@app.route('/hello')
def hello():
    szRet   = r"Hello Python!"
    if( DEBUG_MODE ):
        szRet   += "\r\nDebug Mode.";

    return( szRet );

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
    szProgress = "処理開始中";
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
        WriteBlob( "linepost.txt", szText );

        szProgress = "ヘッダーから 'X-Line-Signature' 取得中";
        signature = request.headers[ 'X-Line-Signature' ]

        # parse webhook body
        szProgress = "webhook body を解析中";
        try:
            events = parser.parse( body, signature )
        except InvalidSignatureError as e:
            #WriteLog( "parser.parse() failed." + "\r\n" + e.message );
            WriteLog( "parser.parse() failed." );
            abort(400)

        # if event is MessageEvent and message is TextMessage, then echo text
        szProgress = "events を解析中";
        for event in events:
            #// MessageEvent 型ではない
            if not isinstance( event, MessageEvent ):
                continue

            if isinstance( event.message, TextMessage ):
                #// テキストメッセージ
                try:
                    szProgress = "リプライメッセージ送信中";
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(
                           text = event.message.text
                        )
                    )
                except Exception as e:
                    #WriteLog( "line_bot_api.reply_message() failed." + "\r\n" + e.message );
                    WriteLog( "line_bot_api.reply_message() failed." );
                #}try
            elif isinstance( event.message, ImageMessage ):
                #// 画像メッセージ
                pass;
            #}if
        #}for event in events:

        WriteLog( "OK");
    except Exception as e:
        #WriteLog( szProgress + "でエラー発生。" + "\r\n" + e.message );
        WriteLog( szProgress + "でエラー発生。" );
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
