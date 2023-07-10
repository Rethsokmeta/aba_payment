-- disable abapay payment provider
UPDATE payment_provider
   SET aba_merchant_id = NULL,
       aba_currency_id = NULL,
       aba_api_key = NULL;