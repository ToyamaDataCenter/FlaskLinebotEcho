#///////////////////////////////////////////////////////////////////////////////////////
#// インポート
#// 
import os
import datetime
import io

from azure.storage.blob import (
    BlockBlobService,
    AppendBlobService,
    PublicAccess
)

class LogWriter( object ):
    """description of class"""

    LOG_CONTAINER_NAME  = r'log-files';
    DEBUG_MODE  = bool(os.getenv( 'DEBUG_MODE', False ))

    # コンストラクタ
    def __init__( self, name, key, subFolderName = None):
        super( LogWriter, self ).__init__()

        self._name              = name;
        self._key               = key;
        self.m_szLogFileName    = "";
        self.m_szSubFolderName  = subFolderName;
        self.m_pBlobService     = AppendBlobService(
            name,
            key
        );
    #}def __init__

    def _CreateLogFile( self ):
        """ ログファイルを作成する。WriteLog を呼び出す前に実行すること。 """

        szRet = "";
        if( LogWriter.DEBUG_MODE ):
            return( "Debug モードのためスキップします。" );

        try:
            if( 0 == len( self.m_szLogFileName ) ):
                szRet = "create_container";
                bIsExists = self.m_pBlobService.exists(
                    LogWriter.LOG_CONTAINER_NAME
                );
                if bIsExists:
                    pass;
                else:
                    self.m_pBlobService.create_container(
                        LogWriter.LOG_CONTAINER_NAME,
                        public_access=PublicAccess.Blob
                    );

                #ログファイル名の決定
                #// 後ろに追加しているが len で 0 と調べているため空文字列
                if( ( self.m_szSubFolderName is not None ) and ( 0 < len( self.m_szSubFolderName ) ) ):
                    #// サブフォルダー名が指定されているときは追加する
                    self.m_szLogFileName   += self.m_szSubFolderName + "\\";
                #}if
                self.m_szLogFileName   += r"{0:%Y-%m-%dT%H-%M-%S.log}".format( datetime.datetime.now() );

                bIsExists = self.m_pBlobService.exists(
                    LogWriter.LOG_CONTAINER_NAME,
                    self.m_szLogFileName
                );
                if bIsExists:
                    szRet = "already blob."
                else:
                    szRet = "create_blob";
                    self.m_pBlobService.create_blob(
                        LogWriter.LOG_CONTAINER_NAME,
                        self.m_szLogFileName
                    );
                szRet = "OK";
            else:
                szRet   = "Already called."
                szRet   = "OK";
            #}if

        except Exception as e:
            #szRet = "Log exception";
            szRet   = szRet + "\r\n" + str( e );
            pass;
        return szRet;
    #}def

    def WriteLog( self, txt ):
        """ ログファイルにテキストを出力する。末尾に改行コードが追加される。 """
        szRet = "";
        szLogText   = r"{0:%Y-%m-%d %H:%M:%S}".format( datetime.datetime.now() ) + r" : " + txt + "\r\n";
        if( LogWriter.DEBUG_MODE ):
            print( szLogText );
            return( "Debug モードのためスキップしました。" );

        try:
            #ログファイルの作成
            self._CreateLogFile();

            szRet = "append_blob_from_text";
            self.m_pBlobService.append_blob_from_text(
                LogWriter.LOG_CONTAINER_NAME,
                self.m_szLogFileName,
                szLogText
            )
            szRet = "OK";
        except Exception as e:
            #szRet = "Log exception";
            szRet   = szRet + "\r\n" + str( e );
        #try

        return szRet;
    #}def

    def WriteBlob( self, blob_name, value ):
        """ 単一 BLOB ファイルを作成しテキストを保存する。 """
        szRet   = ""
        if( LogWriter.DEBUG_MODE ):
            return( "Debug モードのため書き込みをしません。" );

        try:
            #blob_name = r'sample.txt';

            szRet = "BlockBlobService"
            blob_service = BlockBlobService( self._name, self._key)

            szRet = "create_container"
            blob_service.create_container(
                LogWriter.LOG_CONTAINER_NAME,
                public_access=PublicAccess.Blob
            )

            szRet = "create_blob_from_bytes"
            #blob_service.create_blob_from_bytes(
            #    log_container_name,
            #    log_blob_name,
            #    b'<center><h1>Hello World!</h1></center>',
            #    content_settings=ContentSettings('text/html')
            #)

            if( isinstance( value, str ) ):
                szRet = "create_blob_from_text"
                blob_service.create_blob_from_text(
                    LogWriter.LOG_CONTAINER_NAME,
                    blob_name,
                    value
                )
            else:
                szRet = "create_blob_from_stream"
                blob_service.create_blob_from_stream(
                    LogWriter.LOG_CONTAINER_NAME,
                    blob_name,
                    io.BytesIO( value )
                )
            #}if

            #szRet = "make_blob_url"
            #print(blob_service.make_blob_url(log_container_name, log_blob_name))

            szRet = "OK"
        except:
            print( r"Exception.")
        #try

        return szRet;
    #def WriteBlob( blob_name, txt ):

    def MakeBlobUri( self, blob_name ):
        blob_service = BlockBlobService( self._name, self._key)
        szRet   = blob_service.make_blob_url(
            LogWriter.LOG_CONTAINER_NAME,
            blob_name
        );

        return( szRet );
    #}def

#}class