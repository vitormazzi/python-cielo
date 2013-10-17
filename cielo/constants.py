# coding: utf-8

VISA, MASTERCARD, DINERS, DISCOVER, ELO, AMEX = (
    'visa', 'mastercard', 'diners', 'discover', 'elo', 'amex'
)
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


