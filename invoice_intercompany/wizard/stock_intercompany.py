# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.Exceptions import UserError


class StockIntercompany(models.TransientModel):
    _name = 'stock.intercompany'

    source_company_id = fields.Many2one(string="Source company", comodel_name="res.company", required=True)
    destination_company_id = fields.Many2one(string="Destination company", comodel_name="res.company", required=True)
    source_location_id = fields.Many2one(string="Destination location", comodel_name="stock.location", required=True)
    destination_location_id = fields.Many2one(string="Destination location", comodel_name="stock.location", required=True)
    origin = fields.Char(string="Origin", required=True)
    line_ids = fields.One2many(string="Products to transfer", comodel_name="stock.intercompany.line", inverse_name="intercompany_id", required=True)

    def _check_data(self):
        """
        check data given by the user
        :return:
        """
        if len(self.line_ids) == 0:
            raise UserError("You must enter at least one line")
        elif self.source_company_id == self.destination_company_id:
            raise UserError("Companies must be different")
        elif not self.source_location_id.company_id or not self.destination_location_id.company_id:
            raise UserError("Locations are incorrect")
        elif self.source_location_id.company_id == self.destination_location_id.company_id:
            raise UserError("Locations can't have the same company")

        if not self.origin:
            self.update({'origin': "Intercompany"})

    def _prepare_stock_picking_values(self, type):
        """
        prepare values for a picking according to his type
        :param type: delivery or receipt
        :return:
        """
        values = {'origin': self.origin}

        if type == "delivery":
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'outgoing'), ('company_id', '=', self.source_company_id.id)], limit=1)

            if not picking_type:
                raise UserError("Picking type can't be found")

            values.update({
                'partner_id': self.destination_company_id.partner_id.id,
                'company_id': self.source_company_id,
                'location_id': self.source_location_id,
                'picking_type_id': picking_type.id
            })
        elif type == "receipt":
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('company_id', '=', self.destination_company_id.id)], limit=1)

            if not picking_type:
                raise UserError("Picking type can't be found")

            values.update({
                'partner_id': self.source_company_id.partner_id.id,
                'company_id': self.destination_company_id,
                'location_dest_id': self.destination_location_id,
                'picking_type_id': picking_type.id
            })
        else:
            raise UserError("The picking can't be created")

        return values

    def _prepare_stock_picking_lines_values(self):
        """
        prepare lines for a picking, with the lines given in the wizard
        :return:
        """
        lines = []

        for line in self.line_ids:
            lines.append((0, False, {
                'product_id': line.product_id,
                'product_uom_qty': line.quantity,
                'lot_id': line.lot_id
            }))

        return lines

    def cancel_pickings(self, pickings):
        for picking in pickings:
            picking.action_cancel()

        raise UserError("Something went wrong during the pickings creation, the process is canceled")

    def update_lots(self, pickings):
        for picking in pickings:
            picking.action_confirm()
            picking.action_assign()

            if len(picking.move_line_ids_without_package) == 0 or \
                    sum([line.product_uom_qty for line in picking.move_line_ids_without_package]) != \
                    sum([line.quantity for line in self.line_ids]):
                self.cancel_pickings(pickings)

            picking.move_line_ids_without_package.write({'lot_id': False})

            for line in self.line_ids:
                matching_lines = picking.move_line_ids_without_package.filtered(lambda rec: rec.product_id == line.product_id and not rec.lot_id)

                if not matching_lines:
                    self.cancel_pickings(pickings)

                matching_lines[0].write({'lot_id': line.lot_id})

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
