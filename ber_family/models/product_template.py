# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    #### RELATION ####
    family_id = fields.Many2one(string="Famille", comodel_name="product.family")
