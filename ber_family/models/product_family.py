# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductFamily(models.Model):
    _name = 'product.family'

    #### TEXT ####
    name = fields.Char(string="Nom", required=True)
    description = fields.Text(string="Description")

    #### RELATION ####
    product_ids = fields.One2many(string="Articles", comodel_name="product.product", inverse_name="family_id")
    account_move_ids = fields.One2many(string="Factures", comodel_name="account.move", inverse_name="product_family_id")
