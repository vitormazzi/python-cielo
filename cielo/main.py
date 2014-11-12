# coding: utf-8
import os
from datetime import date, datetime
from decimal import Decimal
import requests
import xmltodict
from xml.parsers.expat import ExpatError

from .exceptions import CieloException, GetAuthorizedException, CaptureException, TokenException
from .constants import *
from .util import moneyfmt

__all__ = ['PaymentAttempt', 'TokenPaymentAttempt', 'BuyPageCieloAttempt', 'CieloToken']


class CieloRequest(object):
    """
    Base class containg the http communication and processing logic
    """
    def __init__(self, **kwargs):
        # Required arguments
        try:
            self.fetch_required_arguments(**kwargs)
        except KeyError as e:
            raise TypeError(u"'{0[0]}' is required".format(e.args))

        # Required arguments with default values
        self.sandbox = kwargs.get('sandbox', False)
        self.url_redirect = kwargs.get('url_redirect', '')

        self.url = SANDBOX_URL if self.sandbox else PRODUCTION_URL

        self.validate()

    def fetch_required_arguments(self, **kwargs):
        self.affiliation_id = kwargs['affiliation_id']
        self.api_key = kwargs['api_key']

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

        try:
            response_dict = xmltodict.parse(self.cielo_response.content, encoding='latin-1')
        except ExpatError as e:
            self.error = {
                'type': e.__class__.__name__,
                'args': repr(e.args),
                'response': {
                    'status_code': self.cielo_response.status_code,
                    'content': self.cielo_response.content,
                }
            }
            raise

        if 'erro' in response_dict:
            self.error = response_dict['erro']
            self.error_id = self.error['codigo']
            self.error_message = CIELO_MSG_ERRORS.get(self.error_id, self.error['mensagem'])
            raise CieloException(self.error_id, self.error_message, self.cielo_response.content)

        return response_dict

    def handle_response(self, response):
        self.transaction = response['transacao']
        self.status = self.transaction['status']
        self.transaction_id = self.transaction['tid']


class WithCardData(object):
    """
    Mixin which handles the credit card parameters, expects be used in a subclass of CieloRequest
    """

    def __init__(self, **kwargs):
        super(WithCardData, self).__init__(**kwargs)
        self.expiration = self.expiration_date.strftime('%Y%m')

    def fetch_required_arguments(self, **kwargs):
        super(WithCardData, self).fetch_required_arguments(**kwargs)

        self.card_type = kwargs['card_type']
        self.card_number = kwargs['card_number']
        self.exp_month = kwargs['exp_month']
        self.exp_year = kwargs['exp_year']
        self.card_holders_name = kwargs['card_holders_name']

    def validate(self):
        super(WithCardData, self).validate()

        exp_year_length = len(str(self.exp_year))
        if exp_year_length == 2:
            self.exp_year += 2000
        elif exp_year_length != 4:
            reason = 'exp_year must be composed of 2 or 4 digits (it has {0})'.format(exp_year_length)
            raise ValueError(reason)

        today = date.today()
        self.expiration_date = date(self.exp_year, self.exp_month, 1)
        if self.expiration_date < date(today.year, today.month, 1):
            reason = 'Card expired since {0}/{1}'.format(self.exp_month, self.exp_year)
            raise ValueError(reason)


class WithReturnURL(object):
    """
    Mixin which handles payments which need to redirect the customer.
    """

    def fetch_required_arguments(self, **kwargs):
        super(WithReturnURL, self).fetch_required_arguments(**kwargs)

        self.url_redirect = kwargs['url_redirect']


class Attempt(CieloRequest):
    """
    Base class implementing the methods for authorizing and capturing a transaction.
    May be used with the credit card data or with a token.
    """

    authorization_template = None
    capture_template = 'capture.xml'
    cancelation_template = 'cancel.xml'
    status_template = 'status_using_tid.xml'

    def __init__(self, **kwargs):
        # Required arguments with default values
        self.installments = kwargs.get('installments', 1)
        self.transaction_type = kwargs.get('transaction', CASH) # para manter assinatura do pyrcws
        self.auto_capture = 'true' if kwargs.get('capture', False) else 'false'
        self.tokenize = 'true' if kwargs.get('tokenize', False) else 'false'

        self._authorized = False
        self._captured = False
        self._cancelled = False

        super(Attempt, self).__init__(**kwargs)

    def fetch_required_arguments(self, **kwargs):
        super(Attempt, self).fetch_required_arguments(**kwargs)

        self.order_id = kwargs['order_id']
        self.total = moneyfmt(kwargs['total'], sep='', dp='')

    def validate(self):
        if self.installments not in range(1, 13):
            raise ValueError(u'installments must be a integer between 1 and 12')
        elif (self.transaction_type == CASH) and (self.installments != 1):
            raise ValueError('Payments in cash must have installments = 1')

        super(Attempt, self).validate()

    def handle_response(self, response):
        super(Attempt, self).handle_response(response)

        if self.status == '4':
            self._authorized = True
        elif self.status == '6':
            self._authorized = True
            self._captured = True
        elif self.status == '9':
            self._cancelled = True

    def get_authorized(self):
        self.date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        response_dict = self.make_request(self.url, self.authorization_template)
        self.handle_response(response_dict)
        return True

    def capture(self, **kwargs):
        if hasattr(self, 'transaction_id'):
            if self._captured:
                raise ValueError('Already captured')
            if not self._authorized:
                raise ValueError(u'get_authorized(...) must be called before capture(...)')
        else:
            self.transaction_id = kwargs['transaction_id']

        response_dict = self.make_request(self.url, self.capture_template)
        self.handle_response(response_dict)
        return True

    def cancel(self, **kwargs):
        if not hasattr(self, 'transaction_id'):
            self.transaction_id = kwargs['transaction_id']

        self.amount_to_cancel = moneyfmt(kwargs.get('amount'), sep='', dp='')
        response_dict = self.make_request(self.url, self.cancelation_template)
        self.handle_response(response_dict)
        return True

    def refresh(self, **kwargs):
        if not hasattr(self, 'transaction_id'):
            self.transaction_id = kwargs['transaction_id']

        response_dict = self.make_request(self.url, self.status_template)
        self.handle_response(response_dict)
        return True


class TokenPaymentAttempt(Attempt):
    """
    Interface for creating payments using tokenized credit cards.
    """
    authorization_template = 'authorize_token.xml'

    def fetch_required_arguments(self, **kwargs):
        super(TokenPaymentAttempt, self).fetch_required_arguments(**kwargs)

        self.card_type = kwargs['card_type']
        self.token = kwargs['token']


class PaymentAttempt(WithCardData, Attempt):
    """
    Interface for creating payments using the credit card data.
    """
    authorization_template = 'authorize.xml'

    def fetch_required_arguments(self, **kwargs):
        super(PaymentAttempt, self).fetch_required_arguments(**kwargs)

        self.cvc2 = kwargs['cvc2']


class BuyPageCieloAttempt(WithReturnURL, Attempt):
    """
    Interface for creating payments with card data collected my cielo
    """
    authorization_template = 'authorize_buypagecielo.xml'

    def fetch_required_arguments(self, **kwargs):
        super(BuyPageCieloAttempt, self).fetch_required_arguments(**kwargs)

        self.description = kwargs['description']
        self.card_type = kwargs['card_type']

    def get_authorized(self):
        super(BuyPageCieloAttempt, self).get_authorized()

        if self.status == '0':
            self.authentication_url = self.transaction['url-autenticacao']

        return True


class CieloToken(WithCardData, CieloRequest):
    """
    Tokenizes a credit card without charging it.
    """
    create_token_template = 'token.xml'

    def create_token(self):
        response_dict = self.make_request(self.url, self.create_token_template)

        dados_token = response_dict['retorno-token']['token']['dados-token']
        self.token = dados_token['codigo-token']
        self.status = dados_token['status']
        self.card = dados_token['numero-cartao-truncado']
        return True
