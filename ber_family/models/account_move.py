# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    #### RELATION ####
    product_family_id = fields.Many2one(string="Famille d'article", comodel_name="product.family")
    partner_family_id = fields.Many2one(string="Famille de contact", comodel_name="partner.family")
