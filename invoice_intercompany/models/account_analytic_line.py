# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    #### BOOLEAN ####
    is_invoiced = fields.Boolean(default=False)

    #### RELATION ####
    account_move_ids = fields.Many2many(string="Factures IS", comodel_name="account.move")
