import hashlib, hmac
from base64 import b64encode
from odoo import api, fields, models

REQUEST_PARAMS = [
    'req_time',
    'merchant_id',
    'tran_id',
    'amount',
    'payment_option',
    'return_url',
    'continue_success_url'
]


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'
    code = fields.Selection(
        selection_add=[('abapay', "ABAPay")], ondelete={'abapay': 'set default'}
    )
    aba_merchant_id = fields.Char(
        string="ABA Merchant ID",
        help="The Merchant ID solely used to identify your ABA account.",
        required_if_provider='abapay',
    )
    aba_currency_id = fields.Many2one(
        string="ABA Currency",
        help="The currency associated to your ABA account.",
        comodel_name='res.currency',
        required_if_provider='abapay',
    )
    aba_api_key = fields.Char(
        string="ABA API Key",
        required_if_provider='abapay',
        groups='base.group_system',
    )
    icon_payment_img = fields.Binary("Icon", help="Select icon here")
    sort_code_payment = fields.Integer('Sort Code')

    payment_icon_data_ids = fields.Many2many(
        'payment.icon', 'payment_icon_rel', 'src_pay_id', 'dest_pay_id',
        string='Payment Icon')
    icon_payment_credit = fields.Binary("Icon Cart", help="Payment Icon")
    payment_instruction = fields.Text('Payment Instruction')

    @api.model
    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        """ Override of `payment` to filter out ABAPay providers for unsupported currencies. """
        providers = super()._get_compatible_providers(*args, currency_id=currency_id, **kwargs)

        currency = self.env['res.currency'].browse(currency_id).exists()
        if currency:
            providers = providers.filtered(
                lambda p: p.code != 'abapay' or currency == p.aba_currency_id
            )

        return providers

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'abapay').update({
            'support_fees': True,
        })

    def _abapay_get_api_url(self):
        """ Return the URL of the API corresponding to the provider's state.

        :return: The API URL.
        :rtype: str
        """
        self.ensure_one()

        if self.state == 'enabled':
            return 'https://checkout.payway.com.kh/api/payment-gateway/v1/payments/purchase'
        else:  # 'test'
            return 'https://checkout-sandbox.payway.com.kh/api/payment-gateway/v1/payments/purchase'

    def _abapay_hash(self, data):
        """ Compute hash using Base64 encode of hash hmac sha512 encryption

        :param dict data: The data of transaction
        :return: Hash.
        :rtype: str
        """
        data_to_sign = [str(data[p]) for p in REQUEST_PARAMS if data.get(p, False)]
        signing_string = ''.join(data_to_sign)
        hash = hmac.HMAC(bytes(self.aba_api_key, encoding='utf-8'), bytes(signing_string, encoding='utf-8'), digestmod=hashlib.sha512)
        return b64encode(hash.digest()).decode('utf-8')
