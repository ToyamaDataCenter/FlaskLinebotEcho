import json
import http.client
import urllib.request
import urllib.parse
import urllib.error
import base64


class Translate( object ):
    """ Translator Text Api の Translate サービスを使用すためのクラスです。 """

    API_VERSION = r"3.0";
    EndPoint    = r"api.cognitive.microsofttranslator.com"

    # コンストラクタ
    def __init__( self, key ):
        super( Translate, self ).__init__()

        self._key   = key;
    #}def __init__

    def Request( self, text ):
        """ 指定されたテキストを翻訳します。(en->jp) """
        szRet   = "";

        #// ヘッダー作成
        headers = {
            "Content-Type"              : "application/json",
            "Ocp-Apim-Subscription-Key" : self._key,
        }

        #// クエリー作成
        params  = urllib.parse.urlencode({
            "api-version"       : Translate.API_VERSION,
            "from"              : "en",
            "to"                : "ja",
            "textType"          : "plain",
            "profanityAction"   : "NoAction",
        });

        #// ボディー (JSON) 作成
        #// note : { "text" : .... } は 25 個まで配列にできる。
        szBody  = json.dumps( [ { "text" : text } ] );

        #// REST 送信
        conn = http.client.HTTPSConnection( Translate.EndPoint )
        try:
            conn.request(
                "POST",
                "/translate?%s" % params,
                szBody,
                headers
            );
            response = conn.getresponse()
            with response:
                if( 200 != response.status ):
                    raise Exception( "HTTP ステータスコード '{0}' でした。".format( response.status ) );
                #}if
                data    = response.read();
                szRet   = data.decode( 'utf-8' );
            #}with
        finally:
            conn.close()
        #}try

        return( szRet );
    #}def Request
#}class