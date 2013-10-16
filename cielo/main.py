# coding: utf-8
import os
from datetime import date, datetime
import xml.dom.minidom
from decimal import Decimal

import requests
from util import moneyfmt

VISA, MASTERCARD, DINERS, DISCOVER, ELO, AMEX = 'visa', \
    'mastercard', 'diners', 'discover', 'elo', 'amex'
CARD_TYPE_C = (
    (VISA, u'Visa'),
    (MASTERCARD, u'Mastercard'),
    (DINERS, u'Diners'),
    (DISCOVER, u'Discover'),
    (ELO, u'ELO'),
    (AMEX, u'American express'),
)

CASH, INSTALLMENT_STORE, INSTALLMENT_CIELO = 1, 2, 3
TRANSACTION_TYPE_C = (
    (CASH, u'À vista'),
    (INSTALLMENT_STORE, u'Parcelado (estabelecimento)'),
    (INSTALLMENT_CIELO, u'Parcelado (Cielo)'),
)

SANDBOX_URL = 'https://qasecommerce.cielo.com.br/servicos/ecommwsec.do'
PRODUCTION_URL = 'https://ecommerce.cbmp.com.br/servicos/ecommwsec.do'
CIELO_MSG_ERRORS = {
    '001': u'A mensagem XML está fora do formato especificado pelo arquivo ecommerce.xsd (001-Mensagem inválida)',
    '002': u'Impossibilidade de autenticar uma requisição da loja virtual. (002-Credenciais inválidas)',
    '003': u'Não existe transação para o identificador informado. (003-Transação inexistente)',
    '010': u'A transação, com ou sem cartão, está divergente com a permissão do envio dessa informação. (010-Inconsistência no envio do cartão)',
    '011': u'A transação está configurada com uma modalidade de pagamento não habilitada para a loja. (011-Modalidade não habilitada)',
    '012': u'O número de parcelas solicitado ultrapassa o máximo permitido. (012-Número de parcelas inválido)',
    '019': u'A URL de Retorno é obrigatória, exceto para recorrência e autorização direta.',
    '020': u'Não é permitido realizar autorização para o status da transação. (020-Status não permite autorização)',
    '021': u'Não é permitido realizar autorização, pois o prazo está vencido. (021-Prazo de autorização vencido)',
    '022': u'EC não possui permissão para realizar a autorização.(022-EC não autorizado)',
    '030': u'A captura não pode ser realizada, pois a transação não está autorizada.(030-Transação não autorizada para captura)',
    '031': u'A captura não pode ser realizada, pois o prazo para captura está vencido.(031-Prazo de captura vencido)',
    '032': u'O valor solicitado para captura não é válido.(032-Valor de captura inválido)',
    '033': u'Não foi possível realizar a captura.(033-Falha ao capturar)',
    '040': u'O cancelamento não pode ser realizado, pois o prazo está vencido.(040-Prazo de cancelamento vencido)',
    '041': u'O atual status da transação não permite cancelament.(041-Status não permite cancelamento)',
    '042': u'Não foi possível realizar o cancelamento.(042-Falha ao cancelar)',
    '099': u'Falha no sistema.(099-Erro inesperado)',
}


class GetAuthorizedException(Exception):
    def __init__(self, id, message=None):
        self.id = id
        self.message = message

    def __str__(self):
        return u'%s - %s' % (self.id, self.message)


class CaptureException(Exception):
    pass


class TokenException(Exception):
    pass


class CieloToken(object):
    create_token_template = 'token.xml'

    def __init__(
            self,
            affiliation_id,
            api_key,
            card_type,
            card_number,
            exp_month,
            exp_year,
            card_holders_name,
            sandbox=False):

        if len(str(exp_year)) == 2:
            exp_year = '20%s' % exp_year

        self.url = SANDBOX_URL if sandbox else PRODUCTION_URL
        self.card_type = card_type
        self.affiliation_id = affiliation_id
        self.api_key = api_key
        self.exp_month = exp_month
        self.exp_year = exp_year
        self.expiration = '%s%s' % (exp_year, exp_month)
        self.card_holders_name = card_holders_name
        self.card_number = card_number
        self.sandbox = sandbox

    def _get_real_path(self, filename):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    def create_token(self):
        template = open(self._get_real_path(self.create_token_template)).read()
        payload = template % self.__dict__

        self.response = requests.post(
            self.url,
            data={'mensagem': payload, },
            headers={'user-agent': 'python-cielo'},
        )
        self.dom = xml.dom.minidom.parseString(self.response.content)

        if self.dom.getElementsByTagName('erro'):
            raise TokenException('Erro ao gerar token!')

        self.token = self.dom.getElementsByTagName(
            'codigo-token')[0].childNodes[0].data
        self.status = self.dom.getElementsByTagName(
            'status')[0].childNodes[0].data
        self.card = self.dom.getElementsByTagName(
            'numero-cartao-truncado')[0].childNodes[0].data
        return True


class Attempt(object):
    authorization_template = None
    capture_template = 'capture.xml'

    def _get_real_path(self, filename):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    def get_authorized(self):
        self.date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        template = open(self._get_real_path(self.authorization_template)).read()
        payload = template % self.__dict__

        self.response = requests.post(
            self.url,
            data={'mensagem': payload, },
            headers={'user-agent': 'python-cielo'},
        )

        self.dom = xml.dom.minidom.parseString(self.response.content)

        if self.dom.getElementsByTagName('erro'):
            self.error = self.dom.getElementsByTagName(
                'erro')[0].getElementsByTagName('codigo')[0].childNodes[0].data
            self.error_id = None
            self.error_message = CIELO_MSG_ERRORS[self.error]
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

        template = open(self._get_real_path(self.capture_template)).read()
        payload = template % self.__dict__

        response = requests.post(
            self.url,
            data={'mensagem': payload, },
            headers={'user-agent': 'python-cielo'},
        )

        dom = xml.dom.minidom.parseString(response.content)
        status = int(dom.getElementsByTagName('status')[0].childNodes[0].data)

        if status != 6:
            # 6 = capturado
            raise CaptureException()
        return True


class BasePaymentAttempt(Attempt):

    def __init__(self, **kwargs):
        # Required arguments without default values
        try:
            self.affiliation_id = kwargs.pop('affiliation_id')
            self.api_key = kwargs.pop('api_key')
            self.order_id = kwargs.pop('order_id')
            self.card_type = kwargs.pop('card_type')
            self.total = moneyfmt(kwargs.pop('total'), sep='', dp='')

        except KeyError as e:
            raise TypeError(u"'{0[0]}' is required".format(e.args))

        # Required arguments with default values
        self.installments = kwargs.pop('installments', 1)
        self.transaction_type = kwargs.pop('transaction', CASH) # para manter assinatura do pyrcws
        self.sandbox = kwargs.pop('sandbox', False)
        self.url_redirect = kwargs.pop('url_redirect', None)

        self.url = SANDBOX_URL if self.sandbox else PRODUCTION_URL
        self._authorized = False

        self.validate()

    def validate(self):
        assert self.installments in range(1, 13), u'installments must be a integer between 1 and 12'
        assert (self.installments == 1 and self.transaction_type == CASH) \
                    or self.installments > 1 and self.transaction_type != CASH, \
                    u'if installments = 1 then transaction must be None or "cash"'


class PaymentAttempt(BasePaymentAttempt):
    authorization_template = 'authorize.xml'

    def __init__(self, **kwargs):
        # Required arguments for attempts using the credit card data
        try:
            self.card_number = kwargs.pop('card_number')
            self.cvc2 = kwargs.pop('cvc2')
            self.exp_month = kwargs.pop('exp_month')
            self.exp_year = kwargs.pop('exp_year')
            self.card_holders_name = kwargs.pop('card_holders_name')

        except KeyError as e:
            raise TypeError(u"'{0[0]}' is required".format(e.args))

        super(PaymentAttempt, self).__init__(**kwargs)
        self.expiration = '%s%s' % (self.exp_year, self.exp_month)

    def validate(self):
        super(PaymentAttempt, self).validate()
        self.validate_expiration()

    def validate_expiration(self):
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


class TokenPaymentAttempt(BasePaymentAttempt):
    authorization_template = 'authorize_token.xml'

    def __init__(self, **kwargs):
        # Required arguments for attempts using the credit card data
        try:
            self.token = kwargs.pop('token')

        except KeyError as e:
            raise TypeError(u"'{0[0]}' is required".format(e.args))

        super(TokenPaymentAttempt, self).__init__(**kwargs)
