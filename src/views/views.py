import logging
import urlparse
from requests.models import RequestEncodingMixin as encoder
from tornado.escape import parse_qs_bytes
from tornado.web import asynchronous
from websocket import WebSocketException
from core.base import BaseHandler, disallowed_headers
from core.exceptions import UnexpectedReuqestDataException, InvalidWebSocketURLException


class SQLMapHandler(BaseHandler):
    def get(self):
        self.post()

    @asynchronous
    def post(self):
        _url = self.get_argument('url', default=None)
        data = self.get_argument('data', default=None)

        self.client.is_params = False if self.get_argument('is_params', default=False) == '0' else True
        if not _url:
            raise UnexpectedReuqestDataException

        if not _url.startswith('ws://') and not _url.startswith('wss://'):
            raise InvalidWebSocketURLException

        url = urlparse.urlparse(_url)
        # `query_str` is the query string of websocket
        query_str = url.query
        url = '%s://%s%s' % (url.scheme, url.netloc, url.path)
        if self.request.body:
            query_str = query_str + '&' + self.request.body
        query_str = encoder._encode_params(parse_qs_bytes(query_str))

        if not data and not query_str:
            logging.warning('No query strings in url, is it HTTP headers injection?')
        #    raise UnexpectedReuqestDataException

        if query_str:
            logging.info('Request query string: %s' % query_str)
        if data:
            logging.info('Request message: %s' % data)

        if not self.client.ws:
            self.run_websocket('%s?%s' % (url, query_str))
        else:
            self.client.has_send = False
            try:
                self.client.ws.send(data if data else '')
            except WebSocketException, e:
                self.client.ws.close()
                self.client.ws = None
                logging.error('Error occur: %s' % str(e))
                self.finish()

    def get_argument(self, name, default=None, strip=True):
        return self._get_argument(name, default=default,
                                  source=parse_qs_bytes(self.request.query),
                                  strip=strip)


class MainHandler(BaseHandler):
    def get(self):
        self.render('index.html')
