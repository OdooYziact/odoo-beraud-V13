# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    # TODO: what use ?
    account_analytic_line_ids = fields.Many2many(relation="account_move_account_analytic_line_rel", column1="account_move_id", column2="analytic_line_ids", comodel_name="account.analytic.line")
    