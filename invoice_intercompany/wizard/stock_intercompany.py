# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class StockIntercompany(models.TransientModel):
    _name = 'stock.intercompany'

    #### RELATION ####
    source_company_id = fields.Many2one(string="Société source", comodel_name="res.company", required=True)
    destination_company_id = fields.Many2one(string="Société de destination", comodel_name="res.company", required=True)
    source_location_id = fields.Many2one(string="Emplacement source", comodel_name="stock.location", required=True, domain="[('company_id', '=', source_company_id)]")
    destination_location_id = fields.Many2one(string="Emplacement de destination", comodel_name="stock.location", required=True, domain="[('company_id', '=', destination_company_id)]")
    line_ids = fields.One2many(string="Articles à transférer", comodel_name="stock.intercompany.line", inverse_name="stock_intercompany_id")

    #### TEXT ####
    origin = fields.Char(string="Origine", required=True)

    def _check_data(self):
        """
        check data of the wizard
        :return:
        """
        if len(self.line_ids) == 0:
            raise UserError("Vous devez saisir au moins une ligne")
        elif self.source_company_id == self.destination_company_id:
            raise UserError("Les sociétés doivent être différentes")
        elif not self.source_location_id.company_id or not self.destination_location_id.company_id:
            raise UserError("Les emplacements ne sont pas tous liés à une société")
        elif self.source_location_id.company_id == self.destination_location_id.company_id:
            raise UserError("Les emplacements doivent appartenir à deux sociétés différentes")

        if not self.origin:
            self.update({'origin': "Intersociété"})

    def _prepare_stock_picking_values(self, picking_type):
        """
        prepare values for a picking according to its type
        :param picking_type: delivery or receipt
        :return:
        """
        values = {'origin': self.origin}

        # the picking type determines locations, partner and company
        if picking_type == "delivery":
            picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'outgoing'), ('company_id', '=', self.source_company_id.id)], limit=1)

            if not picking_type_id:
                raise UserError("Le type de transfert n'a pas été trouvé")

            values.update({
                'partner_id': self.destination_company_id.partner_id.id,
                'company_id': self.source_company_id.id,
                'location_id': self.source_location_id.id,
                'picking_type_id': picking_type_id.id
            })
        elif picking_type == "receipt":
            picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('company_id', '=', self.destination_company_id.id)], limit=1)

            if not picking_type:
                raise UserError("Le type de transfert n'a pas été trouvé")

            values.update({
                'partner_id': self.source_company_id.partner_id.id,
                'company_id': self.destination_company_id.id,
                'location_dest_id': self.destination_location_id.id,
                'picking_type_id': picking_type_id.id
            })
        else:
            raise UserError("Le type de transfert est mauvais")

        return values

    def _prepare_stock_picking_lines_values(self):
        """
        prepare lines for a picking, with the lines given in the wizard
        :return:
        """
        lines = []

        for line in self.line_ids:
            lines.append((0, False, {
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'lot_id': line.lot_id.id
            }))

        return lines

    def cancel_pickings(self, pickings):
        """
        cancel the given pickings
        :param pickings:
        :return:
        """
        for picking in pickings:
            picking.action_cancel()

        raise UserError("Quelque chose s'est mal passé durant la création des transferts, le processus est annulé")

    def update_lots(self, pickings):
        """
        change the state of the given pickings and modify their lots
        :param pickings:
        :return:
        """
        for picking in pickings:
            # change the state to create the stock move lines
            picking.action_confirm()
            picking.action_assign()

            # check that the lines have been created
            if len(picking.move_line_ids_without_package) == 0 or \
                    sum([line.product_uom_qty for line in picking.move_line_ids_without_package]) != \
                    sum([line.quantity for line in self.line_ids]):
                self.cancel_pickings(pickings)

            # reset lots
            picking.move_line_ids_without_package.write({'lot_id': False})

            # affect lots given in the wizard
            for line in self.line_ids:
                matching_lines = picking.move_line_ids_without_package.filtered(lambda rec: rec.product_id == line.product_id and not rec.lot_id)

                # if there is no matching line, something went wrong during the creation of the lines
                if not matching_lines:
                    self.cancel_pickings(pickings)

                matching_lines[0].write({'lot_id': line.lot_id.id})

    def run(self):
        """
        create delivery and receipt pickings to transfer stock between companies
        :return:
        """
        self.ensure_one()

        self._check_data()

        delivery_picking_values = self._prepare_stock_picking_values("delivery")
        receipt_picking_values = self._prepare_stock_picking_values("receipt")

        delivery_picking_values['move_ids_without_package'] = receipt_picking_values['move_ids_without_package'] = self._prepare_stock_picking_lines_values()

        delivery_picking = self.env['stock.picking'].create(delivery_picking_values)
        receipt_picking = self.env['stock.picking'].create(receipt_picking_values)

        self.update_lots([delivery_picking, receipt_picking])

        delivery_picking.button_validate()
        receipt_picking.button_validate()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }
