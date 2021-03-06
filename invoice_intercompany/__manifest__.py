# -*- coding: utf-8 -*-
{
    'name': "Invoice Inter-company",
    'summary': "Invoice Inter-company",
    'author': "Yziact (VRA)",
    'maintainer': "CCA",
    'category': "Invoicing",
    'version': "0.1",
    'depends': [
        'base',
        'purchase',
        'sale',
        'product',
        'account',
        'account_accountant'
    ],

    'data': [
        'data/data.xml',
        'wizard/invoice_intercompany.xml',
        'wizard/stock_intercompany.xml',
        'views/account_move.xml',
        'security/ir.model.access.csv'
    ]
}
