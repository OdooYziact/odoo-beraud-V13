# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    
    is_invoiced = fields.Boolean(default=False)
    # TODO: what use ?
    account_move_id = fields.Many2one(string="Lignes de temps", comodel_name="account.move")
