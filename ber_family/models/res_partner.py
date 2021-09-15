# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    #### RELATION ####
    family_id = fields.Many2one(string="Famille", comodel_name="partner.family")
