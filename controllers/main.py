import logging
import pprint
import json

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request


_logger = logging.getLogger(__name__)


class ABAPayController(http.Controller):
    _return_url = '/v1/payment/abapay/return'
    _webhook_url = '/v1/payment/abapay/webhook'

    @http.route(_return_url, type='http', auth='public', methods=['GET'])
    def abapay_return_from_checkout(self):
        _logger.info("partner id from return %d", request.env.user.partner_id.id)
        return request.redirect('/payment/status')

    @http.route(_webhook_url, type='json', auth='public', methods=['POST'], csrf=False)
    def abapay_webhook(self):
        """ Process the notification data sent by ABAPay to the webhook.
        """
        data = json.loads(request.httprequest.data)
        _logger.info("Notification received from ABAPay with data:\n%s", pprint.pformat(data))
        try:
            # Check the integrity of the notification data.
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'abapay', data
            )

            # Handle the notification data.
            tx_sudo._handle_notification_data('abapay', data)
        except ValidationError:  # Acknowledge the notification to avoid getting spammed.
            _logger.exception("Unable to handle the notification data; skipping to acknowledge.")
