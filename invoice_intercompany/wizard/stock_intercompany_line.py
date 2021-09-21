# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockIntercompanyLine(models.TransientModel):
    _name = 'stock.intercompany.line'

    product_id = fields.Many2one(string="Product", comodel_name="product.product")
    quantity = fields.Float(string="Quantity")
    lot_id = fields.Many2one(string="Serial number", comodel_name="stock.production.lot")
    intercompany_id = fields.Many2one(string="Move", comodel_name="stock.intercompany")
