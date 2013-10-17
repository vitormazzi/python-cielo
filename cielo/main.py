# coding: utf-8
import os
from datetime import date, datetime
from decimal import Decimal

import requests
from exceptions import CieloException, GetAuthorizedException, CaptureException, TokenException
from constants import *
from util import moneyfmt, xmltodict

__all__ = ['PaymentAttempt', 'TokenPaymentAttempt', 'CieloToken']


class CieloRequest(object):
    """
    Base class containg the http communication and processing logic
    """

    def __init__(self, **kwargs):
        # Required arguments for all request types
        try:
            self.fetch_required_arguments(**kwargs)
        except KeyError as e:
            raise TypeError(u"'{0[0]}' is required".format(e.args))

        # Required arguments with default values
        self.sandbox = kwargs.pop('sandbox', False)
        self.url_redirect = kwargs.pop('url_redirect', 'null')

        self.url = SANDBOX_URL if self.sandbox else PRODUCTION_URL

        self.validate()

    def fetch_required_arguments(self, **kwargs):
        self.affiliation_id = kwargs.pop('affiliation_id')
        self.api_key = kwargs.pop('api_key')
        self.card_type = kwargs.pop('card_type')

    def validate(self):
        pass

    def make_request(self, url, template_name):
        template_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'templates', template_name
        )
        payload = open(template_path).read() % self.__dict__

        self.cielo_response = requests.post(
            url,
            data={'mensagem': payload},
            headers={'user-agent': 'python-cielo'},
            timeout=30,
        )

        response_dict = xmltodict(self.cielo_response.content)

        if 'erro' in response_dict:
            erro = response_dict['erro']
            self.error_id = erro['codigo'][0]
            self.error_message = CIELO_MSG_ERRORS.get(self.error_id, erro['mensagem'][0])
            raise CieloException(self.error_id, self.error_message, self.cielo_response.content)

        return response_dict


class WithCardData(object):
    """
    Mixin which handles the credit card parameters
    """

    def __init__(self, **kwargs):
        super(WithCardData, self).__init__(**kwargs)
        self.expiration = '%s%s' % (self.exp_year, self.exp_month)

    def fetch_required_arguments(self, **kwargs):
        super(WithCardData, self).fetch_required_arguments(**kwargs)

        self.card_number = kwargs.pop('card_number')
        self.exp_month = kwargs.pop('exp_month')
        self.exp_year = kwargs.pop('exp_year')
        self.card_holders_name = kwargs.pop('card_holders_name')

    def validate(self):
        super(WithCardData, self).validate()

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


class CieloToken(WithCardData, CieloRequest):
    """
    Tokenizes a credit card without charging it.
    """
    create_token_template = 'token.xml'

    def create_token(self):
        response_dict = self.make_request(self.url, self.create_token_template)

        dados_token = response_dict['retorno-token']['token'][0]['dados-token'][0]
        self.token = dados_token['codigo-token'][0]
        self.status = dados_token['status'][0]
        self.card = dados_token['numero-cartao-truncado'][0]
        return True


class Attempt(CieloRequest):
    """
    Base class implementing the methods for authorizing and capturing a transaction.
    May be used with the credit card data or with a token.

    TODO:
    - authorization and capture in a single step
    - authorization with tokenization
    """

    authorization_template = None
    capture_template = 'capture.xml'

    def __init__(self, **kwargs):
        # Required arguments with default values
        self.installments = kwargs.pop('installments', 1)
        self.transaction_type = kwargs.pop('transaction', CASH) # para manter assinatura do pyrcws
        self._authorized = False

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

        response_dict = self.make_request(self.url, self.authorization_template)

        transacao = response_dict['transacao']
        status = int(transacao['status'][0])
        if status != 4:
            self._authorized = False
            autorizacao = transacao['autorizacao'][0]
            error_id = autorizacao['codigo'][0]
            error_message = autorizacao['mensagem'][0]
            raise GetAuthorizedException(error_id, error_message)

        self.transaction_id = transacao['tid'][0]
        self.pan = transacao['pan'][0]

        self._authorized = True
        return True

    def capture(self):
        assert self._authorized, \
            u'get_authorized(...) must be called before capture(...)'

        response_dict = self.make_request(self.url, self.capture_template)

        transacao = response_dict['transacao']
        status = int(transacao['status'][0])
        if status != 6:
            # 6 = capturado
            raise CaptureException()

        return True


class TokenPaymentAttempt(Attempt):
    """
    Interface for creating payments using tokenized credit cards.
    """
    authorization_template = 'authorize_token.xml'

    def __init__(self, **kwargs):
        # Required arguments for attempts using tokens
        try:
            self.token = kwargs.pop('token')

        except KeyError as e:
            raise TypeError(u"'{0[0]}' is required".format(e.args))

        super(TokenPaymentAttempt, self).__init__(**kwargs)


class PaymentAttempt(WithCardData, Attempt):
    """
    Interface for creating payments using the credit card data.
    """
    authorization_template = 'authorize.xml'

    def fetch_required_arguments(self, **kwargs):
        super(PaymentAttempt, self).fetch_required_arguments(**kwargs)

        self.cvc2 = kwargs.pop('cvc2')
