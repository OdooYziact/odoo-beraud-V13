# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    #### RELATION ####
    account_analytic_line_ids = fields.One2many(string="Lignes de temps facturées", comodel_name="account.analytic.line", inverse_name="account_move_id")
    stock_move_ids = fields.One2many(string="Mouvements de stock facturés", comodel_name="stock.move", inverse_name="account_move_id")
