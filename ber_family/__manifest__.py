# -*- coding: utf-8 -*-
{
    'name': "Product and partner families",
    'summary': """ The module adds new tables (families) to qualify partners and products. """,
    'author': "Apik",
    'maintainer': "CCA",
    'category': "Invoicing-Product-CRM",
    'version': "0.1",
    'depends': [
        'base',
        'product',
        'account',
        'stock',
        'contact'
    ],

    'data': [
        'views/account_move.xml',
        'views/partner_family.xml',
        'views/product_family.xml',
        'views/product_template.xml',
        'views/res_partner.xml',

        'security/ir.model.access.csv'
    ]
}
