# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PartnerFamily(models.Model):
    _name = 'partner.family'

    #### TEXT ####
    name = fields.Char(string="Nom", required=True)
    description = fields.Text(string="Description")

    #### RELATION ####
    partner_ids = fields.One2many(string="Contacts", comodel_name="res.partner", inverse_name="family_id")
    account_move_ids = fields.One2many(string="Factures", comodel_name="account.move", inverse_name="partner_family_id")
