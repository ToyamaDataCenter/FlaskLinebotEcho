
""" LINE BOT アプリ """

#///////////////////////////////////////////////////////////////////////////////////////
#// インポート
#// 
import os
import io
import sys
import json
import datetime
import time
import traceback
import uuid

import pyqrcode

import AnalyzeImage
import TranslatorText
import LogWriter

from PIL import(
    Image
)

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
    ImageSendMessage,
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

COMPUTER_VISION_KEY = os.getenv( 'AZURE_COMPUTER_VISION_KEY',   None );
TRANSLATOR_TEXT_KEY = os.getenv( 'AZURE_TRANSLATOR_TEXT_KEY',   None );
TEXT_ANALYTICS_KEY  = os.getenv( 'AZURE_TEXT_ANALYTICS_KEY',    None );

STORAGE_NAME        = os.getenv( 'AZURE_STORAGE_ACCOUNT_NAME', None );
STORAGE_KEY         = os.getenv( 'AZURE_STORAGE_ACCOUNT_KEY',  None );

if( DEBUG_MODE ):
    print( "STORAGE_NAME = '{0}'".format( STORAGE_NAME ) );
    print( "STORAGE_KEY = '{0}'".format( STORAGE_KEY ) );
#}if

# get channel_secret and channel_access_token from your environment variable

channel_access_token    = os.getenv( 'LINE_CHANNEL_ACCESS_TOKEN', None )
channel_secret          = os.getenv( 'LINE_CHANNEL_SECRET', None )

if not DEBUG_MODE and channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)

if not DEBUG_MODE and channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

if( not DEBUG_MODE ):
    line_bot_api    = LineBotApi( channel_access_token )
    parser          = WebhookParser( channel_secret )
else:
    line_bot_api    = None;
    parser          = None;
#}if

# Flask route decorators map / and /hello to the hello function.
# To add other resources, create functions that generate the page contents
# and add decorators to define the appropriate resource locators for them.

@app.route('/')
@app.route('/hello')
def hello():
    szRet   = r"Hello Python!"
    if( DEBUG_MODE ):
        szRet   += "\r\nDebug Mode.";
    #}if

    return( szRet );
#}def hello()

@app.route( '/ver', methods = [ 'GET' ] )
def ver():
    """ バージョン情報を表示する """
    szText  = "";
    try:
        #//logWriter = LogWriter.LogWriter( STORAGE_NAME, STORAGE_KEY );
        #//szText = logWriter.WriteLog( "Call uri /ver" );
        szText  = "OK";
        if( szText == "OK" ):
            szText = sys.version;
    except Exception as e:
        szText  = str( e );
    #}try

    return szText
#}def ver()

def MakeQRCode( szText ):
    pOrgBuffer      = None;
    pThumbBuffer    = None;

    qrcode  = pyqrcode.create( szText.encode('utf-8'), encoding="utf8");

    with io.BytesIO() as qrbuffer:
        qrcode.png( qrbuffer );
        
        qrbuffer.seek( 0, 0 );
        img = Image.open( qrbuffer );
        if( ( 1024 < img.width ) or ( 1024 < img.height ) ):
            img = img.thumbnail( ( 1024, 1024 ), Image.ANTIALIAS );
        #}if

        #// オリジナルサイズ
        pbyBuffer   = None;
        with io.BytesIO() as jpgbuffer:
            img.save( jpgbuffer, "JPEG" );  #JPEG は大文字でないとエラーになる
            pOrgBuffer  = jpgbuffer.getvalue();
        #}with

        #// サムネイル
        img.thumbnail( ( 240, 240 ), Image.ANTIALIAS )
        with io.BytesIO() as jpgbuffer:
            img.save( jpgbuffer, "JPEG" );  #JPEG は大文字でないとエラーになる
            pThumbBuffer    = jpgbuffer.getvalue();
        #}with

        img.close();
    #}with

    return( pOrgBuffer, pThumbBuffer );
#}def

@app.route( '/qr', methods = [ 'GET' ] )
def qr():
    szText  = "";
    pRet    = None;
    try:
        pRet    = MakeQRCode( "Hello, Python!" );
        
        if( ( pRet[ 0 ] is not None ) and ( pRet[ 1 ] is not None ) ):
            szText  = "OK";
        else:
            szText  = "NG";
        #}if
    except Exception as e:
        szText  = ""
        szText  += str( type( e ) );
        szText  += "\r\n";
        szText  += str( e );
        szText  += "\r\n";
        szText  += traceback.format_exc();
        print( szText );
    #}try

    return( szText );
#}def

@app.route( '/callback', methods=[ 'POST' ] )
def LinePost():
    """  LINE からメッセージがポストされたとき  """
    logWriter       = LogWriter.LogWriter( STORAGE_NAME, STORAGE_KEY )

    logWriter.WriteLog( "***** メッセージが LINE から POST されました。 *****" )
    try:
        szText  = "";

        for szKey, szValue in request.headers.items():
            szText += str( szKey ) + " : " + str( szValue ) + "\r\n"
        #for
        szText += "\r\n"

        # get request body as text
        body = request.get_data( as_text = True )
        app.logger.info( "Request body: " + body )
        szText += body;
        logWriter.WriteLog(
            "HTTP の内容\r\n" + szText
        );

        logWriter.WriteLog( "ヘッダーから 'X-Line-Signature' 取得中……" );
        signature = request.headers[ 'X-Line-Signature' ]

        # parse webhook body
        logWriter.WriteLog( "webhook body を解析中……" );
        try:
            events = parser.parse( body, signature )
        except InvalidSignatureError as e:
            #WriteLog( "parser.parse() failed." + "\r\n" + e.message );
            logWriter.WriteLog( "X-Line-Signature と LINE_CHANNEL_SECRET が一致しません。" );
            abort(400)
        except:
            raise;
        #}try

        # if event is MessageEvent and message is TextMessage, then echo text
        logWriter.WriteLog( "events を解析……" );
        for event in events:
            #// MessageEvent 型ではない
            if not isinstance( event, MessageEvent ):
                continue

            logWriter.WriteLog( "ユーザー ID 取得中……" );
            szUserID    = "";
            szUserName  = "";
            try:
                if( event.source.type == "user" ):
                    szUserID    = event.source.user_id;
                    logWriter.WriteLog( "ユーザー名取得中……" );
                    pProfile    = line_bot_api.get_profile( szUserID );
                    szUserName  = pProfile.display_name + " さん";
                    logWriter.WriteLog( szUserName );
                #}if
            except Exception as e:
                logWriter.WriteLog( str( e ) );
            #}try

            if isinstance( event.message, TextMessage ):
                logWriter.WriteLog( "テキスト メッセージです。" );
                szMessage   = "{0}\r\n「{1}」の QR コードを作成しました。".format( szUserName, event.message.text );

                #logWriter.WriteLog( "QR コードを作成中です。" );
                #pQrBuffer   = MakeQRCode( event.message.text );
                #szFileName  = szUserID + "\\qr-" + str( uuid.uuid4() );

                ##// オリジナル画像をストレージに保存する
                #logWriter.WriteLog( "オリジナル画像を保存中です。" );
                #szTempFileName  = szFileName + ".jpg";
                #logWriter.WriteBlob( szTempFileName, pQrBuffer[ 0 ] );
                #szOrgUri    = logWriter.MakeBlobUri( szTempFileName );
                #logWriter.WriteLog( "場所 '{0}'".format( szOrgUri ) );

                ##// サムネイル画像をストレージに保存する
                #logWriter.WriteLog( "サムネイル画像を保存中です。" );
                #szTempFileName  = szFileName + "_s.jpg";
                #logWriter.WriteBlob( szTempFileName, pQrBuffer[ 1 ] );
                #szThumbUri  = logWriter.MakeBlobUri( szTempFileName );
                #logWriter.WriteLog( "場所 '{0}'".format( szThumbUri ) );

                ReplyMessage(
                    event,
                    [
                    TextSendMessage(
                        text = szMessage
                    ),
                    #ImageSendMessage(
                    #    original_content_url    = szOrgUri,
                    #    preview_image_url       = szThumbUri
                    #)
                    TextSendMessage(
                        text = "かと思ったら、ライブラリー内でエラーが発生するため頓挫しました。"
                    ),
                    ]
                )
            elif isinstance( event.message, ImageMessage ):
                logWriter.WriteLog( "画像 メッセージです。" );

                logWriter.WriteLog( "画像コンテンツを取得中……" );
                message_id      = event.message.id
                message_content = line_bot_api.get_message_content( message_id )

                szImageFileName = szUserID + "\\" + str( uuid.uuid4() ) + r".jpg";
                logWriter.WriteLog( "画像コンテンツをストレージに保存しています。(ファイル名:" + szImageFileName + ")" );
                logWriter.WriteBlob( szImageFileName, message_content.content );

                image = io.BytesIO( message_content.content )

                logWriter.WriteLog( "Azure Computer Vision にインスタンス作成。" );
                pRestApi    = AnalyzeImage.AnalyzeImage( COMPUTER_VISION_KEY );
                logWriter.WriteLog( "Azure Computer Vision にリクエスト送信。" );
                szJson      = pRestApi.Request( image );

                logWriter.WriteLog( szJson );

                pRoot   = json.loads( szJson );

                szReply     = "";
                szExplicit  = "";

                #//  とりあえず説明文を取得する
                pDesc   = pRoot[ "description" ];
                szCaption       = "";
                lfConfidence    = 0.0;

                for pCap in pDesc[ "captions" ]:
                    if( lfConfidence < pCap[ "confidence" ] ):
                        szCaption       = pCap[ "text" ];
                        lfConfidence    = pCap[ "confidence" ];
                    #}if
                #}for

                #// Explicit
                #"adult":{"isAdultContent":false,"isRacyContent":false,"adultScore":0.045499119907617569,"racyScore":0.034160565584897995}
                pAdult  = pRoot[ "adult" ];
                szExplicit  += "KENZEN ポイント: {0}pt.".format( int( pAdult[ "adultScore" ] * 100 ) );
                szExplicit  += "\r\n";
                szExplicit  += "判定: ";
                if( pAdult[ "isAdultContent" ] ):
                    szExplicit  += "けしからん";
                else:
                    szExplicit  += "健全";
                #}if
                szExplicit  += "\r\n";
                szExplicit  += "ギリギリポイント: {0}pt.".format( int( pAdult[ "racyScore" ] * 100 ) );
                szExplicit  += "\r\n";
                szExplicit  += "判定: ";
                if( pAdult[ "isRacyContent" ] ):
                    szExplicit  += "けしからん";
                else:
                    szExplicit  += "健全";
                #}if
                szExplicit  += "\r\n";

                if( 0 < len( szCaption ) ):
                    #// 英語の解説を日本語に変換
                    pTransApi   = TranslatorText.Translate( TRANSLATOR_TEXT_KEY );
                    logWriter.WriteLog( "英語を日本語に翻訳中。({0})".format( szCaption ) );
                    szJson      = pTransApi.Request( szCaption );
                    logWriter.WriteLog( szJson );
                    pRoot       = json.loads( szJson );
                    szTrans     = "";
                    for pTransRoot in pRoot:
                        #logWriter.WriteLog( str( pTransRoot ) );
                        for pTrans in pTransRoot[ "translations" ]:
                            logWriter.WriteLog( str( pTrans ) );
                            szTrans += pTrans[ "text" ];
                            #for pTextRoot in pTrans:
                            #    logWriter.WriteLog( str( pTextRoot ) );
                    #}for

                    szReply = szUserName + "、この絵は「" + szTrans  + "(" + szCaption + ")」"
                    if( 0.8 <= lfConfidence ):
                        szReply += "です。";
                    elif( 0.6 <= lfConfidence ):
                        szReply += "かと思います。";
                    elif( 0.4 <= lfConfidence ):
                        szReply += "かな。";
                    elif( 0.2 <= lfConfidence ):
                        szReply += "です。たぶん……";
                    else:
                        szReply += "だと思うけど違っていそうです。";
                    #}if
                    szReply += "(正確度:{0}%)".format( int( lfConfidence * 100 ) );
                else:
                    szReply = szUserName + "、申し訳ありませんが、何の絵か全くわかりません。";
                #}if

                pReplyList  = list();
                if( 0 < len( szReply ) ):
                    pReplyList.append(
                        TextSendMessage(
                            text = szReply
                        )
                    )
                #}if
                if( 0 < len( szExplicit ) ):
                    pReplyList.append(
                        TextSendMessage(
                            text = szExplicit
                        )
                    )
                #}if

                ReplyMessage(
                    event,
                    pReplyList
                )
            else:
                logWriter.WriteLog( "type:{0} のメッセージです。現在、サポートしていません。".format( type( event ) ) );
                ReplyMessage(
                    event,
                    TextSendMessage(
                        text = "Sorry, this input resource is not supported."
                    )
                );
            #}if
        #}for event in events:

        logWriter.WriteLog( "OK" );
    except Exception as e:
        #WriteLog( szProgress + "でエラー発生。" + "\r\n" + e.message );
        szMsg   = str( e ) + "\r\n" + "でエラー発生。";
        ReplyMessage(
            event,
            TextSendMessage(
                text = szMsg
            )
        );
        logWriter.WriteLog( szMsg + "\r\n" + traceback.format_exc() );
        abort(400)
    #}try

    logWriter.WriteLog( "Exit LinePost()." );

    return 'OK'
#}def

def ReplyMessage( event, messages ):
    """ 応答メッセージを送信します。 """
    try:
        #WriteLog( "リプライ メッセージ送信中……" );
        line_bot_api.reply_message(
            event.reply_token,
            messages=messages,
        )
    except:
        #WriteLog( "リプライ メッセージ送信失敗。" );
        pass;
    #}try
#}def

@app.route( '/callback', methods=[ 'GET' ] )
def LineGet():
    return "Ok.This uri is exists.";
#}def

# 何か
if __name__ == '__main__':
    # Run the app server on localhost:4449
    app.run( host = '0.0.0.0', port = 4449 )
    #app.run( host = 'localhost', port = 4449 )
