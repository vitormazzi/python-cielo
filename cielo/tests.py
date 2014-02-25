# -*- coding: utf-8 -*-
from os import path
import unittest
from vcr import VCR
from freezegun import freeze_time

from decimal import Decimal
import requests
from xml.parsers.expat import ExpatError

from cielo import *
from cielo.exceptions import *
from cielo.constants import *

__all__ = [
    'BuyPageLojaTest', 'BuyPageCieloTest',
    'CancelTransactionTest', 'RefreshTransactionTest',
    'CreateTokenTest',
]


class FrozenTimeTest(unittest.TestCase):

    def setUp(self):
        self.freezer = freeze_time("2009-12-14 12:00:01")
        self.freezer.start()

    def tearDown(self):
        self.freezer.stop()


class BuyPageLojaTest(FrozenTimeTest):

    cassettes = path.join(path.dirname(__file__), 'cassettes', 'buypageloja')
    vcr = VCR(cassette_library_dir=cassettes, match_on = ['url', 'method', 'headers', 'body'])

    def test_payment_attempt_authorized(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHBPL1',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with BuyPageLojaTest.vcr.use_cassette('authorization_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertFalse(attempt._captured)

    def test_payment_attempt_unauthorized(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.01'),  # when amount does not end with .00 attempt is automatically cancelled
            'order_id': '7DSD63A1HBLP2',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with BuyPageLojaTest.vcr.use_cassette('authorization_failure'):
            self.assertTrue(attempt.get_authorized())

        self.assertEquals(TRANSACTION_STATUS[attempt.status], u'Não autorizada')

    def test_payment_attempt_capture(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHBPL3',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with BuyPageLojaTest.vcr.use_cassette('authorization_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)

        with BuyPageLojaTest.vcr.use_cassette('capture_success'):
            self.assertTrue(attempt.capture())

        self.assertTrue(attempt._captured)

    def test_payment_attempt_expired_card(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHBPL4',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2009,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }

        self.assertRaises(ValueError, PaymentAttempt, **params)

    def test_payment_attempt_invalid_exp_year(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHBPL5',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 9,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }

        self.assertRaises(ValueError, PaymentAttempt, **params)

    def test_payment_attempt_invalid_exp_month(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHBPL6',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 13,
            'exp_year': 10,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }

        self.assertRaises(ValueError, PaymentAttempt, **params)

    def test_payment_attempt_authorized_using_exp_year_as_2_digits(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHBPL7',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 10,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with BuyPageLojaTest.vcr.use_cassette('authorization_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertFalse(attempt._captured)

    def test_payment_attempt_authorized_using_exp_month_as_1_digit(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHBPL7',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with BuyPageLojaTest.vcr.use_cassette('authorization_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertFalse(attempt._captured)

    def test_payment_attempt_failed_bad_api_key(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHBPL8',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with BuyPageLojaTest.vcr.use_cassette('authorization_bad_api_key'):
            self.assertRaises(CieloException, attempt.get_authorized)

        self.assertFalse(attempt._authorized)
        self.assertFalse(attempt._captured)

    def test_payment_attempt_failed_bad_affiliation_id(self):
        params = {
            'affiliation_id': '1',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHBPL9',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with BuyPageLojaTest.vcr.use_cassette('authorization_bad_affiliation_id'):
            self.assertRaises(CieloException, attempt.get_authorized)

        self.assertFalse(attempt._authorized)
        self.assertFalse(attempt._captured)

    def test_payment_attempt_with_capture_authorized(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHBPL10',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with BuyPageLojaTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)

    def test_payment_attempt_with_capture_unauthorized(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.01'),  # when amount does not end with .00 attempt is automatically cancelled
            'order_id': '7DSD63A1HBLP11',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with BuyPageLojaTest.vcr.use_cassette('authorization_with_capture_failure'):
            self.assertTrue(attempt.get_authorized())

        self.assertEquals(TRANSACTION_STATUS[attempt.status], u'Não autorizada')

    def test_payment_attempt_with_tokenization(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHBLP12',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'tokenize': True,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with BuyPageLojaTest.vcr.use_cassette('authorization_and_tokenization'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertFalse(attempt._captured)
        self.assertEquals(attempt.transaction['token'], {
            u'dados-token': {
                u'status': u'1',
                u'numero-cartao-truncado': u'401200******1112',
                u'codigo-token': u'mgbM+Tuo4hmxThAT+xdJ1ibra3jjeQ/mL914D68gbi4='
            }
        })

    def test_payment_attempt_with_capture_and_tokenization(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHBLP12',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'tokenize': True,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with BuyPageLojaTest.vcr.use_cassette('authorization_capture_and_tokenization'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)
        self.assertEquals(attempt.transaction['token'], {
            u'dados-token': {
                u'status': u'1',
                u'numero-cartao-truncado': u'401200******1112',
                u'codigo-token': u'mgbM+Tuo4hmxThAT+xdJ1ibra3jjeQ/mL914D68gbi4='
            }
        })

    def test_authorization_fails_if_buypagecielo_is_enabled(self):
        params = {
            'affiliation_id': '1001734898',
            'api_key': 'e84827130b9837473681c2787007da5914d6359947015a5cdb2b8843db0fa832',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHBLP13',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with BuyPageLojaTest.vcr.use_cassette('authorization_failure_if_buypagecielo_is_enabled'):
            self.assertRaises(CieloException, attempt.get_authorized)

        self.assertEquals(attempt.error, {
            u'@xmlns': u'http://ecommerce.cbmp.com.br',
            u'codigo': u'010',
            u'mensagem': u'Não é permitido o envio do cartão.'
        })

    def test_error_parsing_xml_raises_ValueError(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHBPL1',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with BuyPageLojaTest.vcr.use_cassette('cielo_webservice_error'):
            self.assertRaises(ExpatError, attempt.get_authorized)

        self.assertFalse(attempt._authorized)
        self.assertFalse(attempt._captured)
        self.assertEquals(attempt.error, {
            'type': 'ExpatError',
            'args': "('mismatched tag: line 9, column 7',)",
            'response': {
                'status_code': 503,
                'content': (
                    '<HTML>\n<HEAD>\n<TITLE>Weblogic Bridge Message\n</TITLE>\n</HEAD>\n <BODY>\n'
                    '<H2>Failure of server APACHE bridge:</H2><P>\n<hr>No backend server available for connection: timed out after 4 seconds or idempotent set to OFF.\n<hr> '
                    '</BODY>\n</HTML>\n'
                )
            },
        })


class BuyPageCieloTest(FrozenTimeTest):

    cassettes = path.join(path.dirname(__file__), 'cassettes', 'buypagecielo')
    vcr = VCR(cassette_library_dir=cassettes, match_on = ['url', 'method', 'headers', 'body'])

    def test_authorization_request_only_creates_transaction(self):
        params = {
            'affiliation_id': '1001734898',
            'api_key': 'e84827130b9837473681c2787007da5914d6359947015a5cdb2b8843db0fa832',
            'card_type': VISA,
            'total': Decimal('1.00'),
            'order_id': '7DSD163AHBPC1',
            'description': 'Transacao teste BuyPage Cielo',
            'url_redirect': 'http://localhost:7777/orders/7DSD163AH2/',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        attempt = BuyPageCieloAttempt(**params)

        # Request authorization
        with BuyPageCieloTest.vcr.use_cassette('authorization_request'):
            self.assertTrue(attempt.get_authorized())
        self.assertEquals(TRANSACTION_STATUS[attempt.status], u'Criada')

    def test_viewing_authentication_page_updates_transaction_status(self):
        params = {
            'affiliation_id': '1001734898',
            'api_key': 'e84827130b9837473681c2787007da5914d6359947015a5cdb2b8843db0fa832',
            'card_type': VISA,
            'total': Decimal('1.00'),
            'order_id': '7DSD163AHBPC2',
            'description': 'Transacao teste BuyPage Cielo',
            'url_redirect': 'http://localhost:7777/orders/7DSD163AH2/',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        attempt = BuyPageCieloAttempt(**params)

        # Request authorization
        with BuyPageCieloTest.vcr.use_cassette('authorization_request'):
            self.assertTrue(attempt.get_authorized())
            self.assertEquals(attempt.status, '0')
            authentication_url = attempt.transaction['url-autenticacao'] 

        # Customer gets the authentication page
        with BuyPageCieloTest.vcr.use_cassette('customer_viewing_authentication_page'):
            authentication_page = requests.get(authentication_url, headers={'user-agent': 'python-cielo tests'})

        # Refresh the transaction status
        with BuyPageCieloTest.vcr.use_cassette('authorization_request_being_processed'):
            self.assertTrue(attempt.refresh())
            self.assertEquals(TRANSACTION_STATUS[attempt.status], u'Em andamento')

    def test_buypagecielo_payment_attempt_authorized(self):
        params = {
            'affiliation_id': '1001734898',
            'api_key': 'e84827130b9837473681c2787007da5914d6359947015a5cdb2b8843db0fa832',
            'card_type': VISA,
            'total': Decimal('1.00'),
            'order_id': '7DSD163AHBPC3',
            'description': 'Transacao teste BuyPage Cielo',
            'url_redirect': 'http://localhost:7777/orders/7DSD163AHBPC3/',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        attempt = BuyPageCieloAttempt(**params)

        # Request authorization
        with BuyPageCieloTest.vcr.use_cassette('authorization_request'):
            self.assertTrue(attempt.get_authorized())
            self.assertEquals(attempt.status, '0')
            authentication_url = attempt.transaction['url-autenticacao'] 

        # Customer gets the authentication page
        with BuyPageCieloTest.vcr.use_cassette('customer_viewing_authentication_page', record_mode='new_episodes'):
            authentication_page = requests.get(authentication_url, headers={'user-agent': 'python-cielo tests'})

        # Refresh the transaction status
        with BuyPageCieloTest.vcr.use_cassette('authorization_request_being_processed', record_mode='new_episodes'):
            self.assertTrue(attempt.refresh())
            self.assertEquals(TRANSACTION_STATUS[attempt.status], u'Em andamento')

        # Customer authenticates the transaction
        auth_id = authentication_url.split('?id=')[1]
        with BuyPageCieloTest.vcr.use_cassette('customer_authenticating_transaction', record_mode='new_episodes'):
            post_url = 'https://qasecommerce.cielo.com.br/web/verify.cbmp'
            authenticated_transaction = requests.post(post_url, {
                'numeroCartao': '4012001037141112',
                'mes': '05',
                'ano': '18',
                'codSeguranca': '123',
                'bandeira': 'visa',
                'id': auth_id,
                'bin': '0',
                'cancelar': 'false',
            }, allow_redirects=False, headers={'user-agent': 'python-cielo tests'})
            self.assertEquals(authenticated_transaction.status_code, 302)
            self.assertEquals(
                authenticated_transaction.headers['location'],
                'http://localhost:7777/orders/7DSD163AHBPC3/'
            )

        # Refresh the transaction status
        with BuyPageCieloTest.vcr.use_cassette('authorization_ok'):
            self.assertTrue(attempt.refresh())
            self.assertEquals(TRANSACTION_STATUS[attempt.status], u'Autorizada')

    def test_buypagecielo_with_capture(self):
        params = {
            'affiliation_id': '1001734898',
            'api_key': 'e84827130b9837473681c2787007da5914d6359947015a5cdb2b8843db0fa832',
            'card_type': VISA,
            'total': Decimal('1.00'),
            'order_id': '7DSD163AHBPC4',
            'description': 'Transacao teste BuyPage Cielo',
            'url_redirect': 'http://localhost:7777/orders/7DSD163AHBPC4/',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': True,
        }
        attempt = BuyPageCieloAttempt(**params)

        # Request authorization
        with BuyPageCieloTest.vcr.use_cassette('authorization_with_capture_request'):
            self.assertTrue(attempt.get_authorized())
            self.assertEquals(attempt.status, '0')
            authentication_url = attempt.transaction['url-autenticacao'] 

        # Customer gets the authentication page
        with BuyPageCieloTest.vcr.use_cassette('customer_viewing_authentication_page', record_mode='new_episodes'):
            authentication_page = requests.get(authentication_url, headers={'user-agent': 'python-cielo tests'})

        # Refresh the transaction status
        with BuyPageCieloTest.vcr.use_cassette('authorization_request_being_processed', record_mode='new_episodes'):
            self.assertTrue(attempt.refresh())
            self.assertEquals(TRANSACTION_STATUS[attempt.status], u'Em andamento')

        # Customer authenticates the transaction
        auth_id = authentication_url.split('?id=')[1]
        with BuyPageCieloTest.vcr.use_cassette('customer_authenticating_transaction', record_mode='new_episodes'):
            post_url = 'https://qasecommerce.cielo.com.br/web/verify.cbmp'
            authenticated_transaction = requests.post(post_url, {
                'numeroCartao': '4012001037141112',
                'mes': '05',
                'ano': '18',
                'codSeguranca': '123',
                'bandeira': 'visa',
                'id': auth_id,
                'bin': '0',
                'cancelar': 'false',
            }, allow_redirects=False, headers={'user-agent': 'python-cielo tests'})
            self.assertEquals(authenticated_transaction.status_code, 302)
            self.assertEquals(
                authenticated_transaction.headers['location'],
                'http://localhost:7777/orders/7DSD163AHBPC4/'
            )

        # Refresh the transaction status
        with BuyPageCieloTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.refresh())
            self.assertEquals(TRANSACTION_STATUS[attempt.status], u'Capturada')

    def test_buypagecielo_with_capture_and_tokenization(self):
        params = {
            'affiliation_id': '1001734898',
            'api_key': 'e84827130b9837473681c2787007da5914d6359947015a5cdb2b8843db0fa832',
            'card_type': VISA,
            'total': Decimal('1.00'),
            'order_id': '7DSD163AHBPC5',
            'description': 'Transacao teste BuyPage Cielo',
            'url_redirect': 'http://localhost:7777/orders/7DSD163AHBPC5/',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'tokenize': True,
            'sandbox': True,
        }
        attempt = BuyPageCieloAttempt(**params)

        # Request authorization
        with BuyPageCieloTest.vcr.use_cassette('authorization_capture_and_tokenization'):
            self.assertTrue(attempt.get_authorized())
            self.assertEquals(attempt.status, '0')
            authentication_url = attempt.transaction['url-autenticacao'] 

        # Customer gets the authentication page
        with BuyPageCieloTest.vcr.use_cassette('customer_viewing_authentication_page', record_mode='new_episodes'):
            authentication_page = requests.get(authentication_url, headers={'user-agent': 'python-cielo tests'})

        # Refresh the transaction status
        with BuyPageCieloTest.vcr.use_cassette('authorization_request_being_processed', record_mode='new_episodes'):
            self.assertTrue(attempt.refresh())
            self.assertEquals(TRANSACTION_STATUS[attempt.status], u'Em andamento')

        # Customer authenticates the transaction
        auth_id = authentication_url.split('?id=')[1]
        with BuyPageCieloTest.vcr.use_cassette('customer_authenticating_transaction', record_mode='new_episodes'):
            post_url = 'https://qasecommerce.cielo.com.br/web/verify.cbmp'
            authenticated_transaction = requests.post(post_url, {
                'numeroCartao': '4012001037141112',
                'mes': '05',
                'ano': '18',
                'codSeguranca': '123',
                'bandeira': 'visa',
                'id': auth_id,
                'bin': '0',
                'cancelar': 'false',
            }, allow_redirects=False, headers={'user-agent': 'python-cielo tests'})
            self.assertEquals(authenticated_transaction.status_code, 302)
            self.assertEquals(
                authenticated_transaction.headers['location'],
                'http://localhost:7777/orders/7DSD163AHBPC5/'
            )

        # Refresh the transaction status
        with BuyPageCieloTest.vcr.use_cassette('authorization_capture_and_tokenization_success'):
            self.assertTrue(attempt.refresh())
            self.assertEquals(TRANSACTION_STATUS[attempt.status], u'Capturada')

        self.assertEquals(attempt.transaction['token'], {
            u'dados-token': {
                u'status': u'1',
                u'numero-cartao-truncado': u'401200******1112',
                u'codigo-token': u'zwAEf9pjznPteWQC/DjP4/m6j/d9LdWsvtjDWZSKhiQ='
            }
        })

    def test_buypagecielo_payment_attempt_unauthorized(self):
        params = {
            'affiliation_id': '1001734898',
            'api_key': 'e84827130b9837473681c2787007da5914d6359947015a5cdb2b8843db0fa832',
            'card_type': VISA,
            'total': Decimal('1.01'),  # when amount does not end with .00 attempt is automatically cancelled
            'order_id': '7DSD163AHBPC6',
            'description': 'Transacao teste BuyPage Cielo',
            'url_redirect': 'http://localhost:7777/orders/7DSD163AHBPC6/',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        attempt = BuyPageCieloAttempt(**params)

        # Request authorization
        with BuyPageCieloTest.vcr.use_cassette('authorization_failure_with_buypagecielo'):
            self.assertTrue(attempt.get_authorized())
            self.assertEquals(attempt.status, '0')
            authentication_url = attempt.transaction['url-autenticacao'] 

        # Customer gets the authentication page
        with BuyPageCieloTest.vcr.use_cassette('customer_viewing_authentication_page', record_mode='new_episodes'):
            authentication_page = requests.get(authentication_url, headers={'user-agent': 'python-cielo tests'})

        # Refresh the transaction status
        with BuyPageCieloTest.vcr.use_cassette('authorization_request_being_processed', record_mode='new_episodes'):
            self.assertTrue(attempt.refresh())
            self.assertEquals(TRANSACTION_STATUS[attempt.status], u'Em andamento')

        # Customer authenticates the transaction
        auth_id = authentication_url.split('?id=')[1]
        with BuyPageCieloTest.vcr.use_cassette('customer_authenticating_transaction', record_mode='new_episodes'):
            post_url = 'https://qasecommerce.cielo.com.br/web/verify.cbmp'
            authenticated_transaction = requests.post(post_url, {
                'numeroCartao': '4012001037141112',
                'mes': '05',
                'ano': '18',
                'codSeguranca': '123',
                'bandeira': 'visa',
                'id': auth_id,
                'bin': '0',
                'cancelar': 'false',
            }, allow_redirects=False, headers={'user-agent': 'python-cielo tests'})
            self.assertEquals(authenticated_transaction.status_code, 302)
            self.assertEquals(
                authenticated_transaction.headers['location'],
                'http://localhost:7777/orders/7DSD163AHBPC6/'
            )

        # Refresh the transaction status
        with BuyPageCieloTest.vcr.use_cassette('authentication_failed_with_buypagecielo'):
            self.assertTrue(attempt.refresh())

        self.assertEquals(TRANSACTION_STATUS[attempt.status], u'Não autorizada')

    def test_url_redirect_is_required(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),
            'order_id': '7DSD163AHBPC7',
            'description': 'Transacao teste BuyPage Cielo',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        self.assertRaises(TypeError, BuyPageCieloAttempt, **params)

    def test_authorization_fails_if_buypageloja_is_enabled(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.01'),  # when amount does not end with .00 attempt is automatically cancelled
            'order_id': '7DSD163AHBPC8',
            'description': 'Transacao teste BuyPage Cielo',
            'url_redirect': 'http://localhost:7777/orders/7DSD163AHBPC8/',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        attempt = BuyPageCieloAttempt(**params)

        with BuyPageCieloTest.vcr.use_cassette('authorization_failure_if_buypageloja_is_enabled'):
            self.assertRaises(CieloException, attempt.get_authorized)

        self.assertEquals(attempt.error, {
            u'@xmlns': u'http://ecommerce.cbmp.com.br',
            u'codigo': u'010',
            u'mensagem': u'O envio do cartão é obrigatório.'
        })

    def test_token_payment_attempt_with_capture_authorized(self):
        token = 'zwAEf9pjznPteWQC/DjP4/m6j/d9LdWsvtjDWZSKhiQ=' # from test_buypagecielo_with_capture_and_tokenization

        params = {
            'affiliation_id': '1001734898',
            'api_key': 'e84827130b9837473681c2787007da5914d6359947015a5cdb2b8843db0fa832',
            'card_type': VISA,
            'total': Decimal('1.00'),
            'order_id': '7DSD163AHBPC9',
            'token': token,
            'url_redirect': 'http://localhost:7777/orders/7DSD163AHBPC9/',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': True,
        }
        attempt = TokenPaymentAttempt(**params)

        with BuyPageCieloTest.vcr.use_cassette('token_authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)

    def test_token_payment_attempt_unauthorized(self):
        token = 'zwAEf9pjznPteWQC/DjP4/m6j/d9LdWsvtjDWZSKhiQ=' # from test_buypagecielo_with_capture_and_tokenization

        params = {
            'affiliation_id': '1001734898',
            'api_key': 'e84827130b9837473681c2787007da5914d6359947015a5cdb2b8843db0fa832',
            'card_type': VISA,
            'total': Decimal('1.01'),  # when amount does not end with .00 attempt is automatically cancelled
            'order_id': '7DSD163AHBPC10',
            'token': token,
            'url_redirect': 'http://localhost:7777/orders/7DSD163AHBPC10/',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': True,
        }
        attempt = TokenPaymentAttempt(**params)

        with BuyPageCieloTest.vcr.use_cassette('token_authorization_with_capture_failure'):
            self.assertTrue(attempt.get_authorized())

        self.assertEquals(TRANSACTION_STATUS[attempt.status], u'Não autorizada')


class CancelTransactionTest(FrozenTimeTest):

    cassettes = path.join(path.dirname(__file__), 'cassettes', 'cancel_transaction')
    vcr = VCR(cassette_library_dir=cassettes, match_on = ['url', 'method', 'headers', 'body'])

    def test_cancel_transaction_after_authorization(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHCAN1',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with CancelTransactionTest.vcr.use_cassette('authorization_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertFalse(attempt._captured)

        with CancelTransactionTest.vcr.use_cassette('cancel_authorized_transaction'):
            self.assertTrue(attempt.cancel(amount=attempt.total))

    def test_cancel_transaction_after_capture(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHCAN2',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with CancelTransactionTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)

        with CancelTransactionTest.vcr.use_cassette('cancel_captured_transaction'):
            self.assertTrue(attempt.cancel(amount=attempt.total))

    def test_cancel_transaction_using_tid(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHCAN3',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with CancelTransactionTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        new_attempt = PaymentAttempt(**params)

        with CancelTransactionTest.vcr.use_cassette('cancel_transaction_using_tid'):
            self.assertTrue(new_attempt.cancel(amount=attempt.total, transaction_id=attempt.transaction_id))

        self.assertEquals(new_attempt.transaction['cancelamentos'], {
            u'cancelamento': {
                u'codigo': u'9',
                u'data-hora': u'2014-02-25T16:34:29.224-03:00',
                u'mensagem': u'Transacao cancelada com sucesso',
                u'valor': u'100'
            }
        })

    def test_cancel_partial_amount(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHCAN4',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with CancelTransactionTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)

        with CancelTransactionTest.vcr.use_cassette('cancel_partial_amount'):
            self.assertTrue(attempt.cancel(amount=Decimal('0.5')))

        self.assertEquals(attempt.transaction['cancelamentos'], {
            u'cancelamento': {
                u'codigo': u'6',
                u'data-hora': u'2014-02-25T16:34:27.263-03:00',
                u'mensagem': u'Cancelamento parcial realizado com sucesso',
                u'valor': u'50'
            }
        })

    def test_cancelation_amount_bigger_than_transaction_amount(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHCAN5',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with CancelTransactionTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)

        with CancelTransactionTest.vcr.use_cassette('cancelation_amount_bigger_than_transaction_amount'):
            self.assertRaises(CieloException, attempt.cancel, amount=Decimal('5'))

        self.assertEquals(attempt.error, {
            u'@xmlns': u'http://ecommerce.cbmp.com.br',
            u'codigo': u'043',
            u'mensagem': u"Não é possível cancelar a transação [tid='%s']: valor de cancelamento é maior que valor capturado." % (
                attempt.transaction['tid']
            )
        })

    def test_transaction_already_cancelled(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHCAN6',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with CancelTransactionTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)

        with CancelTransactionTest.vcr.use_cassette('cancel_captured_transaction'):
            self.assertTrue(attempt.cancel(amount=attempt.total))

        self.assertTrue(attempt._cancelled)

        with CancelTransactionTest.vcr.use_cassette('transaction_already_canceled'):
            self.assertRaises(CieloException, attempt.cancel, amount=attempt.total)

        self.assertEquals(attempt.error, {
            u'@xmlns': u'http://ecommerce.cbmp.com.br',
            u'codigo': u'041',
            u'mensagem': u'Transação com o Tid [%s] já está cancelada.' % attempt.transaction['tid']
        })


class RefreshTransactionTest(FrozenTimeTest):

    cassettes = path.join(path.dirname(__file__), 'cassettes', 'refresh_transaction')
    vcr = VCR(cassette_library_dir=cassettes, match_on = ['url', 'method', 'headers', 'body'])

    def test_status_for_authorized_transaction(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHREF1',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with RefreshTransactionTest.vcr.use_cassette('authorization_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertFalse(attempt._captured)

        with RefreshTransactionTest.vcr.use_cassette('status_for_authorized_transaction'):
            self.assertTrue(attempt.refresh())

        self.assertEquals(attempt.transaction['status'], '4')

    def test_status_for_captured_transaction(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHREF2',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with RefreshTransactionTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)

        with RefreshTransactionTest.vcr.use_cassette('status_for_captured_transaction'):
            self.assertTrue(attempt.refresh())

        self.assertEquals(attempt.transaction['status'], '6')

    def test_status_for_cancelled_transaction(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHREF3',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with RefreshTransactionTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)

        with RefreshTransactionTest.vcr.use_cassette('cancel_captured_transaction'):
            self.assertTrue(attempt.cancel(amount=attempt.total))

        self.assertTrue(attempt._cancelled)

        with RefreshTransactionTest.vcr.use_cassette('status_for_canceled_transaction'):
            self.assertTrue(attempt.refresh())

        self.assertEquals(attempt.transaction['status'], '9')

    def test_status_for_invalid_transaction(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHREF4',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with RefreshTransactionTest.vcr.use_cassette('status_for_invalid_transaction'):
            self.assertRaises(CieloException, attempt.refresh, transaction_id=1)

        self.assertEquals(attempt.error, {
            u'@xmlns': u'http://ecommerce.cbmp.com.br',
            u'codigo': u'001',
            u'mensagem': u"O XML informado não é valido:\n- string value '1' does not match pattern for tidType in namespace http://ecommerce.cbmp.com.br: '<xml-fragment/>'"
        })

    def test_status_for_unknown_transaction(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AHREF5',  # strings are allowed here
            'card_number': '4012001037141112',
            'cvc2': 423,
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': True,
        }
        attempt = PaymentAttempt(**params)

        with RefreshTransactionTest.vcr.use_cassette('status_for_unknown_transaction'):
            self.assertRaises(CieloException, attempt.refresh, transaction_id='00000000000000000000')

        self.assertEquals(attempt.error, {
            u'@xmlns': u'http://ecommerce.cbmp.com.br',
            u'codigo': u'003',
            u'mensagem': u"Não foi encontrada transação para o Tid '00000000000000000000'."
        })


class CreateTokenTest(FrozenTimeTest):

    cassettes = path.join(path.dirname(__file__), 'cassettes', 'create_token')
    vcr = VCR(cassette_library_dir=cassettes, match_on = ['url', 'method', 'headers', 'body'])

    def test_create_cielo_token(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': 'visa',
            'card_number': '4012001037141112',
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'sandbox': True,
        }
        with CreateTokenTest.vcr.use_cassette('token_creation_success'):
            token = CieloToken(**params)
            token.create_token()

        self.assertEqual(token.status, '1')
        self.assertTrue('1112' in token.card)

    def test_raises_create_cielo_token(self):
        params = {
            'affiliation_id': '323298379',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': 'visa',
            'card_number': '4012001037141112',
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'sandbox': True,
        }
        token = CieloToken(**params)

        with CreateTokenTest.vcr.use_cassette('token_creation_failure'):
            self.assertRaises(CieloException, token.create_token)

    def test_token_payment_attempt_authorized(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': 'visa',
            'card_number': '4012001037141112',
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'sandbox': True,
        }
        token = CieloToken(**params)

        with CreateTokenTest.vcr.use_cassette('token_creation_success'):
            token.create_token()

        self.assertEqual(token.status, '1')
        self.assertTrue('1112' in token.card)

        params = {
            'affiliation_id': token.affiliation_id,
            'api_key': token.api_key,
            'card_type': token.card_type,
            'total': Decimal('1.00'),
            'order_id': '7DSD163AHTOK1',
            'token': token.token,
            'url_redirect': 'http://localhost:7777/orders/7DSD163AHTOK1/',
            'installments': 1,
            'transaction': CASH,
            'sandbox': token.sandbox,
        }
        attempt = TokenPaymentAttempt(**params)

        with CreateTokenTest.vcr.use_cassette('authorization_success_with_token'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)

        with CreateTokenTest.vcr.use_cassette('capture_success_with_token'):
            self.assertTrue(attempt.capture())

        self.assertTrue(attempt._captured)

    def test_token_payment_attempt_unauthorized(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': 'visa',
            'card_number': '4012001037141112',
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'sandbox': True,
        }
        token = CieloToken(**params)

        with CreateTokenTest.vcr.use_cassette('token_creation_success'):
            token.create_token()

        self.assertEqual(token.status, '1')
        self.assertTrue('1112' in token.card)

        params = {
            'affiliation_id': token.affiliation_id,
            'api_key': token.api_key,
            'card_type': token.card_type,
            'total': Decimal('1.01'),  # when amount does not end with .00 attempt is automatically cancelled
            'order_id': '7DSD163AHTOK2',
            'token': token.token,
            'url_redirect': 'http://localhost:7777/orders/7DSD163AHTOK2/',
            'installments': 1,
            'transaction': CASH,
            'sandbox': token.sandbox,
        }
        attempt = TokenPaymentAttempt(**params)

        with CreateTokenTest.vcr.use_cassette('authorization_failure_with_token'):
            self.assertTrue(attempt.get_authorized())

        self.assertEquals(TRANSACTION_STATUS[attempt.status], u'Não autorizada')

    def test_token_payment_attempt_with_capture_authorized(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': 'visa',
            'card_number': '4012001037141112',
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'sandbox': True,
        }
        token = CieloToken(**params)

        with CreateTokenTest.vcr.use_cassette('token_creation_success'):
            token.create_token()

        self.assertEqual(token.status, '1')
        self.assertTrue('1112' in token.card)

        params = {
            'affiliation_id': token.affiliation_id,
            'api_key': token.api_key,
            'card_type': token.card_type,
            'total': Decimal('1.00'),
            'order_id': '7DSD163AHTOK3',
            'token': token.token,
            'url_redirect': 'http://localhost:7777/orders/7DSD163AHTOK1/',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': token.sandbox,
        }
        attempt = TokenPaymentAttempt(**params)

        with CreateTokenTest.vcr.use_cassette('token_authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)

    def test_token_payment_attempt_unauthorized(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': 'visa',
            'card_number': '4012001037141112',
            'exp_month': 1,
            'exp_year': 2010,
            'card_holders_name': 'JOAO DA SILVA',
            'sandbox': True,
        }
        token = CieloToken(**params)

        with CreateTokenTest.vcr.use_cassette('token_creation_success'):
            token.create_token()

        self.assertEqual(token.status, '1')
        self.assertTrue('1112' in token.card)

        params = {
            'affiliation_id': token.affiliation_id,
            'api_key': token.api_key,
            'card_type': token.card_type,
            'total': Decimal('1.01'),  # when amount does not end with .00 attempt is automatically cancelled
            'order_id': '7DSD163AHTOK4',
            'token': token.token,
            'url_redirect': 'http://localhost:7777/orders/7DSD163AHTOK1/',
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': token.sandbox,
        }
        attempt = TokenPaymentAttempt(**params)

        with CreateTokenTest.vcr.use_cassette('token_authorization_with_capture_failure'):
            self.assertTrue(attempt.get_authorized())

        self.assertEquals(TRANSACTION_STATUS[attempt.status], u'Não autorizada')

if __name__ == '__main__':
    unittest.main()
