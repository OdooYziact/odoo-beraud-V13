# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    #### BOOLEAN ####
    is_invoiced = fields.Boolean(default=False)

    #### RELATION ####
    account_move_ids = fields.Many2many(string="Factures IS", comodel_name="account.move")
