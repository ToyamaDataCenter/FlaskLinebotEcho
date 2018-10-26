import http.client
import urllib.request
import urllib.parse
import urllib.error
import base64

class AnalyzeImage( object ):
    """ Azure Computer Vision の Analyze Image """

    EndPoint    = r"japaneast.api.cognitive.microsoft.com";

    # コンストラクタ
    def __init__( self, key ):
        super (AnalyzeImage, self ).__init__()
        self.params = urllib.parse.urlencode({
            # Request parameters
            'visualFeatures'    : 'Categories,Description,Faces,Adult ',
            'details'           : 'Celebrities,Landmarks',
            'language'          : 'en',
        })
        self._key   = key;
    #}def __init__

    def Request( self, image ):
        """
        Azure Computer Vision の Analyze Image にリクエストを送信します。
        """

        szRet   = "AnalyzeImage.Request() : スタート";

        try:
            szRet   = "AnalyzeImage.Request() : headers 作成";
            headers = {
                # Request headers
                #'Content-Type': 'application/json',
                "Content-Type"  : "application/octet-stream",
                'Ocp-Apim-Subscription-Key': self._key,
            }
            szRet   = "AnalyzeImage.Request() : HTTPSConnection 作成";
            conn = http.client.HTTPSConnection( AnalyzeImage.EndPoint )
            #with conn:
            szRet   = "conn.request";
            conn.request(
                "POST",
                "/vision/v1.0/analyze?%s" % self.params,
                image,
                headers
            );
            szRet   = "conn.getresponse";
            response = conn.getresponse()
            with response:
                if( 200 != response.status ):
                    raise Exception( "HTTP ステータスコード '{0}' でした。".format( response.status ) );
                szRet   = "response.json";
                data = response.read();
                #print(data)

                szRet    = data.decode('utf-8');
            #}with
            conn.close()

        except Exception as e:
            #print("[Errno {0}] {1}".format(e.errno, e.strerror))
            pass;
            #raise;
        #}try

        return( szRet );
    #}def

#}class
