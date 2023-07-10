# -*- coding: utf-8 -*-
{
    'name': "Payment Provider: ABA Bank",
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'summary': "ABA payment accquirer",
    'depends': ['payment'],
    'data': [
        'views/payment_aba_template.xml',
        'views/payment_provider_view.xml',
        'data/payment_provider_data.xml',
    ],
    'installable': True,
    'application': True,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}
