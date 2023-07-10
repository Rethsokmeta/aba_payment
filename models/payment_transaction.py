import base64
import logging
from odoo import _, api, models
from odoo.exceptions import ValidationError
from base64 import b64encode
from datetime import datetime


_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """ Override of `payment` to return ABAPay-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`.

        :param dict processing_values: The generic and specific processing values of the
                                       transaction.
        :return: The dict of provider-specific processing values.
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'abapay':
            return res

        rendering_values = {
            'req_time': datetime.today().strftime('%Y%m%d%H%M%S'),
            'merchant_id': self.provider_id.aba_merchant_id,
            'tran_id': self.reference,
            'amount': self.amount,
            'payment_option': 'cards',
            'return_url': b64encode(b"https://YOUR_DOMAIN.COM/v1/payment/abapay/webhook").decode('utf-8'),
            'continue_success_url': 'https://YOUR_DOMAIN.COM/v1/payment/abapay/return',
            'view_type': 'checkout',
        }
        rendering_values.update({
            'hash': self.provider_id._abapay_hash(rendering_values),
            'api_url': self.provider_id._abapay_get_api_url()
        })
        return rendering_values

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of `payment` to find the transaction based on ABAPay data.

        :param str provider_code: The code of the provider that handled the transaction.
        :param dict notification_data: The notification data sent by the provider.
        :return: The transaction if found.
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If inconsistent data are received.
        :raise ValidationError: If the data match no transaction.
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'abapay' or len(tx) == 1:
            return tx

        reference = notification_data.get('tran_id')
        if not reference:
            raise ValidationError(
                "ABAPay: " + _("Received data with missing reference %(ref)s.", ref=reference)
            )

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'abapay')])
        if not tx:
            raise ValidationError(
                "ABAPay: " + _("No transaction found matching reference %s.", reference)
            )

        return tx

    def _process_notification_data(self, notification_data):
        """ Override of `payment' to process the transaction based on ABAPay data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider.
        :return: None
        :raise ValidationError: If inconsistent data are received.
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'abapay':
            return

        self.provider_reference = notification_data.get('tran_id')

        success_code = notification_data.get('status')
        # if not success_code:
        #     raise ValidationError("ABAPay: " + _("Received data with missing status."))

        if success_code == 0:
            self._set_done()
        else:
            self._set_error(_(
                "An error occurred during the processing of your payment. Please try again."
            ))
