# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockIntercompanyLine(models.TransientModel):
    _name = 'stock.intercompany.line'

    def _get_lot_id_domain(self):
        return [
            ('product_id', '=', self.product_id.id),
            ('company_id', '=', self.stock_intercompany_id.source_company_id.id)
        ]

    #### RELATION ####
    product_id = fields.Many2one(string="Article", comodel_name="product.product", required=True)
    lot_id = fields.Many2one(string="Numéro de série", comodel_name="stock.production.lot", domain=_get_lot_id_domain, required=True)
    stock_intercompany_id = fields.Many2one(string="Transfert IS", comodel_name="stock.intercompany")

    #### NUMBER ####
    quantity = fields.Float(string="Quantité")
