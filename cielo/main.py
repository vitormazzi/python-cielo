# coding: utf-8
import os
from datetime import date, datetime
import xml.dom.minidom
from decimal import Decimal

import requests
from exceptions import GetAuthorizedException, CaptureException, TokenException
from constants import *
from util import moneyfmt

__all__ = ['PaymentAttempt', 'TokenPaymentAttempt', 'CieloToken']

class CieloRequest(object):

    def __init__(self, **kwargs):
        # Required arguments for all request types
        try:
            self.fetch_required_arguments(**kwargs)
        except KeyError as e:
            raise TypeError(u"'{0[0]}' is required".format(e.args))

        # Required arguments with default values
        self.sandbox = kwargs.pop('sandbox', False)
        self.url_redirect = kwargs.pop('url_redirect', None)

        self.url = SANDBOX_URL if self.sandbox else PRODUCTION_URL
        self._authorized = False

        self.validate()

    def fetch_required_arguments(self, **kwargs):
        self.affiliation_id = kwargs.pop('affiliation_id')
        self.api_key = kwargs.pop('api_key')
        self.card_type = kwargs.pop('card_type')

    def validate(self):
        pass

    def make_request(self, url, template_name):
        template_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), template_name
        )
        template = open(template_path).read()
        payload = template % self.__dict__

        self.response = requests.post(
            url,
            data={'mensagem': payload, },
            headers={'user-agent': 'python-cielo'},
            timeout=30,
        )
        return xml.dom.minidom.parseString(self.response.content)


class RequestWithCardData(CieloRequest):

    def __init__(self, **kwargs):
        super(RequestWithCardData, self).__init__(**kwargs)
        self.expiration = '%s%s' % (self.exp_year, self.exp_month)

    def fetch_required_arguments(self, **kwargs):
        super(RequestWithCardData, self).fetch_required_arguments(**kwargs)

        self.card_number = kwargs.pop('card_number')
        self.exp_month = kwargs.pop('exp_month')
        self.exp_year = kwargs.pop('exp_year')
        self.card_holders_name = kwargs.pop('card_holders_name')

    def validate(self):
        super(RequestWithCardData, self).validate()

        exp_year_length = len(str(self.exp_year))
        if exp_year_length == 2:
            self.exp_year += 2000
        elif exp_year_length != 4:
            reason = 'exp_year must be composed of 2 or 4 digits (it has {0})'.format(exp_year_length)
            raise ValueError(reason)

        today = date.today()
        expiration_date = date(self.exp_year, self.exp_month, 1)
        if expiration_date < date(today.year, today.month, 1):
            reason = 'Card expired since {0}/{1}'.format(self.exp_month, self.exp_year)
            raise ValueError(reason)


class CieloToken(RequestWithCardData):
    create_token_template = 'token.xml'

    def create_token(self):
        self.dom = self.make_request(self.url, self.create_token_template)

        if self.dom.getElementsByTagName('erro'):
            raise TokenException('Erro ao gerar token!')

        self.token = self.dom.getElementsByTagName(
            'codigo-token')[0].childNodes[0].data
        self.status = self.dom.getElementsByTagName(
            'status')[0].childNodes[0].data
        self.card = self.dom.getElementsByTagName(
            'numero-cartao-truncado')[0].childNodes[0].data
        return True


class Attempt(CieloRequest):
    authorization_template = None
    capture_template = 'capture.xml'

    def __init__(self, **kwargs):
        # Required arguments with default values
        self.installments = kwargs.pop('installments', 1)
        self.transaction_type = kwargs.pop('transaction', CASH) # para manter assinatura do pyrcws

        super(Attempt, self).__init__(**kwargs)

    def fetch_required_arguments(self, **kwargs):
        super(Attempt, self).fetch_required_arguments(**kwargs)

        self.order_id = kwargs.pop('order_id')
        self.total = moneyfmt(kwargs.pop('total'), sep='', dp='')

    def validate(self):
        super(Attempt, self).validate()
        assert self.installments in range(1, 13), u'installments must be a integer between 1 and 12'
        assert (self.installments == 1 and self.transaction_type == CASH) \
                    or self.installments > 1 and self.transaction_type != CASH, \
                    u'if installments = 1 then transaction must be None or "cash"'

    def get_authorized(self):
        self.date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        self.dom = self.make_request(self.url, self.authorization_template)

        if self.dom.getElementsByTagName('erro'):
            self.error_id = self.dom.getElementsByTagName(
                'erro')[0].getElementsByTagName('codigo')[0].childNodes[0].data
            try:
                self.error_message = CIELO_MSG_ERRORS[self.error_id]
            except IndexError:
                self.error_message = u'Erro não especificado, ver documentação (código %s)' % self.error_id
            raise GetAuthorizedException(self.error_id, self.error_message)

        self.status = int(
            self.dom.getElementsByTagName('status')[0].childNodes[0].data)
        if self.status != 4:
            self.error_id = self.dom.getElementsByTagName(
                'autorizacao')[0].getElementsByTagName(
                    'codigo')[0].childNodes[0].data
            self.error_message = self.dom.getElementsByTagName(
                'autorizacao')[0].getElementsByTagName(
                    'mensagem')[0].childNodes[0].data
            self._authorized = False
            raise GetAuthorizedException(self.error_id, self.error_message)

        self.transaction_id = self.dom.getElementsByTagName(
            'tid')[0].childNodes[0].data
        self.pan = self.dom.getElementsByTagName('pan')[0].childNodes[0].data

        self._authorized = True
        return True

    def capture(self):
        assert self._authorized, \
            u'get_authorized(...) must be called before capture(...)'

        self.dom = self.make_request(self.url, self.authorization_template)

        status = int(self.dom.getElementsByTagName('status')[0].childNodes[0].data)

        if status != 6:
            # 6 = capturado
            raise CaptureException()
        return True


class TokenPaymentAttempt(Attempt):
    authorization_template = 'authorize_token.xml'

    def __init__(self, **kwargs):
        # Required arguments for attempts using tokens
        try:
            self.token = kwargs.pop('token')

        except KeyError as e:
            raise TypeError(u"'{0[0]}' is required".format(e.args))

        super(TokenPaymentAttempt, self).__init__(**kwargs)


class PaymentAttempt(Attempt, RequestWithCardData):
    authorization_template = 'authorize.xml'

    def fetch_required_arguments(self, **kwargs):
        super(PaymentAttempt, self).fetch_required_arguments(**kwargs)

        self.cvc2 = kwargs.pop('cvc2')
