# -*- coding: utf-8 -*-
from os import path
import unittest
from vcr import VCR
from freezegun import freeze_time

from decimal import Decimal
from cielo import *
from cielo.exceptions import *
from cielo.constants import *


class MainTest(unittest.TestCase):

    cassettes = path.join(path.dirname(__file__), 'cassettes')
    vcr = VCR(cassette_library_dir=cassettes)

    def setUp(self):
        self.freezer = freeze_time("2009-12-14 12:00:01")
        self.freezer.start()

    def tearDown(self):
        self.freezer.stop()

    def test_payment_attempt_authorized(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertFalse(attempt._captured)

    def test_payment_attempt_unauthorized(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.01'),  # when amount does not end with .00 attempt is automatically cancelled
            'order_id': '7DSD63A1H1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_failure'):
            self.assertRaises(CieloException, attempt.get_authorized)

        self.assertFalse(attempt._authorized)
        self.assertFalse(attempt._captured)

    def test_payment_attempt_capture(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)

        with MainTest.vcr.use_cassette('capture_success'):
            self.assertTrue(attempt.capture())

        self.assertTrue(attempt._captured)

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
        with MainTest.vcr.use_cassette('token_creation_success'):
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

        with MainTest.vcr.use_cassette('token_creation_failure'):
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

        with MainTest.vcr.use_cassette('token_creation_success'):
            token.create_token()

        self.assertEqual(token.status, '1')
        self.assertTrue('1112' in token.card)

        params = {
            'affiliation_id': token.affiliation_id,
            'api_key': token.api_key,
            'card_type': token.card_type,
            'total': Decimal('1.00'),
            'order_id': '7DSD163AH1',
            'token': token.token,
            'installments': 1,
            'transaction': CASH,
            'sandbox': token.sandbox,
        }
        attempt = TokenPaymentAttempt(**params)

        with MainTest.vcr.use_cassette('authorization_success_with_token'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)

        with MainTest.vcr.use_cassette('capture_success_with_token'):
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

        with MainTest.vcr.use_cassette('token_creation_success'):
            token.create_token()

        self.assertEqual(token.status, '1')
        self.assertTrue('1112' in token.card)

        params = {
            'affiliation_id': token.affiliation_id,
            'api_key': token.api_key,
            'card_type': token.card_type,
            'total': Decimal('1.01'),  # when amount does not end with .00 attempt is automatically cancelled
            'order_id': '7DSD163AH1',
            'token': token.token,
            'installments': 1,
            'transaction': CASH,
            'sandbox': token.sandbox,
        }
        attempt = TokenPaymentAttempt(**params)

        with MainTest.vcr.use_cassette('authorization_failure_with_token'):
            self.assertTrue(attempt.get_authorized())

        with MainTest.vcr.use_cassette('capture_failure_with_token'):
            self.assertTrue(attempt.capture())

        self.assertFalse(attempt._authorized)
        self.assertFalse(attempt._captured)

    def test_payment_attempt_expired_card(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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
            'order_id': '7DSD163AH1',  # strings are allowed here
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
            'order_id': '7DSD163AH1',  # strings are allowed here
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
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertFalse(attempt._captured)

    def test_payment_attempt_failed_bad_api_key(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_bad_api_key'):
            self.assertRaises(CieloException, attempt.get_authorized)

        self.assertFalse(attempt._authorized)
        self.assertFalse(attempt._captured)

    def test_payment_attempt_failed_bad_affiliation_id(self):
        params = {
            'affiliation_id': '1',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_bad_affiliation_id'):
            self.assertRaises(CieloException, attempt.get_authorized)

        self.assertFalse(attempt._authorized)
        self.assertFalse(attempt._captured)

    def test_payment_attempt_with_capture_authorized(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)

    def test_payment_attempt_with_capture_unauthorized(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.01'),  # when amount does not end with .00 attempt is automatically cancelled
            'order_id': '7DSD63A1H1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_with_capture_failure'):
            self.assertRaises(CieloException, attempt.get_authorized)

        self.assertFalse(attempt._authorized)
        self.assertFalse(attempt._captured)

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

        with MainTest.vcr.use_cassette('token_creation_success'):
            token.create_token()

        self.assertEqual(token.status, '1')
        self.assertTrue('1112' in token.card)

        params = {
            'affiliation_id': token.affiliation_id,
            'api_key': token.api_key,
            'card_type': token.card_type,
            'total': Decimal('1.00'),
            'order_id': '7DSD163AH1',
            'token': token.token,
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': token.sandbox,
        }
        attempt = TokenPaymentAttempt(**params)

        with MainTest.vcr.use_cassette('token_authorization_with_capture_success'):
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

        with MainTest.vcr.use_cassette('token_creation_success'):
            token.create_token()

        self.assertEqual(token.status, '1')
        self.assertTrue('1112' in token.card)

        params = {
            'affiliation_id': token.affiliation_id,
            'api_key': token.api_key,
            'card_type': token.card_type,
            'total': Decimal('1.01'),  # when amount does not end with .00 attempt is automatically cancelled
            'order_id': '7DSD163AH1',
            'token': token.token,
            'installments': 1,
            'transaction': CASH,
            'capture': True,
            'sandbox': token.sandbox,
        }
        attempt = TokenPaymentAttempt(**params)

        with MainTest.vcr.use_cassette('token_authorization_with_capture_failure'):
            self.assertRaises(CieloException, attempt.get_authorized)

        self.assertFalse(attempt._authorized)
        self.assertFalse(attempt._captured)

    def test_payment_attempt_with_tokenization(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_and_tokenization'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertFalse(attempt._captured)
        self.assertEquals(attempt.transaction['token'], {
            u'dados-token': {
                u'status': u'1',
                u'numero-cartao-truncado': u'401200******1112',
                u'codigo-token': u'O/sN7IgUNo4FKXy6SeQRc+BbuZiFvYo4Sqdph0EWaoI='
            }
        })

    def test_payment_attempt_with_capture_and_tokenization(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_capture_and_tokenization'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)
        self.assertEquals(attempt.transaction['token'], {
            u'dados-token': {
                u'status': u'1',
                u'numero-cartao-truncado': u'401200******1112',
                u'codigo-token': u'O/sN7IgUNo4FKXy6SeQRc+BbuZiFvYo4Sqdph0EWaoI='
            }
        })

    def test_cancel_transaction_after_authorization(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertFalse(attempt._captured)

        with MainTest.vcr.use_cassette('cancel_authorized_transaction'):
            self.assertTrue(attempt.cancel(amount=attempt.total))

    def test_cancel_transaction_after_capture(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)

        with MainTest.vcr.use_cassette('cancel_captured_transaction'):
            self.assertTrue(attempt.cancel(amount=attempt.total))

    def test_cancel_transaction_using_tid(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        new_attempt = PaymentAttempt(**params)

        with MainTest.vcr.use_cassette('cancel_transaction_using_tid'):
            self.assertTrue(new_attempt.cancel(amount=attempt.total, transaction_id=attempt.transaction_id))

    def test_cancel_partial_amount(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)

        with MainTest.vcr.use_cassette('cancel_partial_amount'):
            self.assertTrue(attempt.cancel(amount=Decimal('0.5')))

    def test_cancelation_amount_bigger_than_transaction_amount(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)

        with MainTest.vcr.use_cassette('cancelation_amount_bigger_than_transaction_amount'):
            self.assertRaises(CieloException, attempt.cancel, amount=Decimal('5'))

        self.assertEquals(attempt.error, {
            u'@xmlns': u'http://ecommerce.cbmp.com.br',
            u'codigo': u'043',
            u'mensagem': u"Não é possível cancelar a transação [tid='10069930690A28C91001']: valor de cancelamento é maior que valor capturado."
        })

    def test_transaction_already_cancelled(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)

        with MainTest.vcr.use_cassette('cancel_captured_transaction'):
            self.assertTrue(attempt.cancel(amount=attempt.total))

        self.assertTrue(attempt._cancelled)

        with MainTest.vcr.use_cassette('transaction_already_canceled'):
            self.assertRaises(CieloException, attempt.cancel, amount=attempt.total)

        self.assertEquals(attempt.error, {
            u'@xmlns': u'http://ecommerce.cbmp.com.br',
            u'codigo': u'041',
            u'mensagem': u'Transação com o Tid [10069930690A29531001] já está cancelada.'
        })

    def test_status_for_authorized_transaction(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertFalse(attempt._captured)

        with MainTest.vcr.use_cassette('status_for_authorized_transaction'):
            self.assertTrue(attempt.refresh())

        self.assertEquals(attempt.transaction['status'], '4')

    def test_status_for_captured_transaction(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)

        with MainTest.vcr.use_cassette('status_for_captured_transaction'):
            self.assertTrue(attempt.refresh())

        self.assertEquals(attempt.transaction['status'], '6')

    def test_status_for_cancelled_transaction(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('authorization_with_capture_success'):
            self.assertTrue(attempt.get_authorized())

        self.assertTrue(attempt._authorized)
        self.assertTrue(attempt._captured)

        with MainTest.vcr.use_cassette('cancel_captured_transaction'):
            self.assertTrue(attempt.cancel(amount=attempt.total))

        self.assertTrue(attempt._cancelled)

        with MainTest.vcr.use_cassette('status_for_canceled_transaction'):
            self.assertTrue(attempt.refresh())

        self.assertEquals(attempt.transaction['status'], '9')

    def test_status_for_invalid_transaction(self):
        params = {
            'affiliation_id': '1006993069',
            'api_key': '25fbb99741c739dd84d7b06ec78c9bac718838630f30b112d033ce2e621b34f3',
            'card_type': VISA,
            'total': Decimal('1.00'),  # when amount ends with .00 attempt is automatically authorized
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('status_for_invalid_transaction'):
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
            'order_id': '7DSD163AH1',  # strings are allowed here
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

        with MainTest.vcr.use_cassette('status_for_unknown_transaction'):
            self.assertRaises(CieloException, attempt.refresh, transaction_id='00000000000000000000')

        self.assertEquals(attempt.error, {
            u'@xmlns': u'http://ecommerce.cbmp.com.br',
            u'codigo': u'003',
            u'mensagem': u"Não foi encontrada transação para o Tid '00000000000000000000'."
        })


if __name__ == '__main__':
    unittest.main()
