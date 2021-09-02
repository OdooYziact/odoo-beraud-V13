# -*- coding: utf-8 -*-

from odoo import models, fields, api


class InvoiceIntercompany(models.TransientModel):
    _name = 'invoice.intercompany'

    end_date = fields.Date(string="Date de fin")

    def get_timesheets(self):
        """
        timesheet recovery
        :return: uninvoiced timesheets with a company different of the user one
        """
        invoiceable_timesheets = False

        if self.end_date:
            timesheets = self.env['account.analytic.line'].sudo().search([
                ('is_timesheet', '=', True),
                ('is_invoiced', '=', False),
                ('date', '<=', self.end_date)
            ])

            # filter according to the company
            if timesheets:
                invoiceable_timesheets = timesheets.filtered(lambda x: x.company_id != x.user_id.company_id)
                
        return invoiceable_timesheets

    def get_stock_moves(self):
        """
        stock move recovery
        :return: uninvoiced stock moves with a company different of the user one
        """
        invoiceable_stock_moves = False

        if self.end_date:
            # select only the done stock moves of type receipt
            receipt_picking_types = self.env['stock.picking.type'].search([('code', '=', 'incoming')])

            stock_moves = self.env['stock.move'].sudo().search([
                ('picking_id.picking_type_id', 'in', receipt_picking_types.ids),
                ('picking_id.date_done', '<=', self.end_date),
                ('state', '=', 'done'),
                ('is_invoiced', '=', False)
            ])

            if stock_moves:
                # select the moves with a company different of the user one
                invoiceable_stock_moves = stock_moves.filtered(lambda x: x.company_id != x.picking_id.user_id.company_id)

        return invoiceable_stock_moves

    def get_time_to_invoice_per_company(self, invoiceable_timesheets):
        """
        sort timesheets per company
        :param invoiceable_timesheets: timesheets to sort
        :return: dict like {'res.company(x,)': [list of timesheet_ids], 'res.company(y,)': [12, 15, 98, 966]}
        """
        companies = self.env['res.company'].search([])
        timesheet_per_companies = {}

        for company_id in companies:
            # create an entry for each company
            if company_id not in timesheet_per_companies:
                timesheet_per_companies[company_id] = []

            # sort timesheets
            for timesheet in invoiceable_timesheets:
                if timesheet.company_id == company_id and timesheet.user_id.company_id != company_id:
                    timesheet_per_companies[company_id].append(timesheet.id)
                    
        return timesheet_per_companies

    def get_products_to_invoice_per_company(self, invoiceable_stock_moves):
        """
        sort stock moves per company
        :param invoiceable_stock_moves: stock moves to sort
        :return: dict like {'res.company(x,)': [list of stock_move_ids], 'res.company(y,)': [12, 15, 98, 966]}
        """
        companies = self.env['res.company'].search([])
        stock_moves_per_companies = {}

        for company_id in companies:
            # create an entry for each company
            if company_id not in stock_moves_per_companies:
                stock_moves_per_companies[company_id] = []

            # sort stock moves
            for stock_move in invoiceable_stock_moves:
                if stock_move.company_id == company_id and stock_move.picking_id.user_id.company_id != company_id:
                    stock_moves_per_companies[company_id].append(stock_move.id)

        return stock_moves_per_companies

    def create_invoices(self, timesheet_per_companies, stock_move_per_companies):
        """
        create invoices (purchase and sale)
        :param timesheet_per_companies: timesheets to invoice
        :param stock_move_per_companies: stock moves to invoice
        """
        company_env = self.env['res.company']
        analytic_line_env = self.env['account.analytic.line']
        stock_move_env = self.env['stock.move']
        companies = company_env.search([])
        time_spent_product_id = self.env.ref('invoice_intercompany.product_time_spent')
        
        for company_id in companies:
            lines = analytic_line_env.browse(timesheet_per_companies[company_id])
            stock_lines = stock_move_env.browse(stock_move_per_companies[company_id])

            if lines or stock_lines:
                # loading client (partner) and vendor (company) for sale invoice
                sale_company_id = company_env.search([('id', '!=', company_id.id)])  # not the current company_id
                sale_partner_id = company_id.partner_id  # partner linked to the current company

                # loading client (partner) and vendor (company) for purchase invoice
                purchase_company_id = company_id  # customer
                purchase_partner_id = company_env.search([('id', '!=', company_id.id)]).partner_id  # supplier / vendor

                # preparing invoice values
                sale_invoice_values = self._prepare_account_move_values('in_invoice', sale_partner_id)  # supplier / vendor
                purchase_invoice_values = self._prepare_account_move_values('out_invoice', purchase_partner_id)  # customer

                # preparing invoice lines values
                sale_invoice_lines = []
                purchase_invoice_lines = []

                if lines:
                    sale_invoice_lines += self._prepare_account_move_line_values(sum(lines.mapped('amount')), time_spent_product_id, sale_company_id)
                    purchase_invoice_lines += self._prepare_account_move_line_values(sum(lines.mapped('amount')), time_spent_product_id, purchase_company_id)

                if stock_lines:
                    sale_invoice_lines += self._prepare_invoice_lines_values_stock(stock_move_per_companies, sale_company_id)
                    purchase_invoice_lines += self._prepare_account_move_line_values_stock(stock_move_per_companies, purchase_company_id)

                # add lines values to invoice values
                sale_invoice_values['invoice_line_ids'] = sale_invoice_lines
                purchase_invoice_values['invoice_line_ids'] = purchase_invoice_lines

                # creating invoice with values
                is_sale_invoice_created = self.env['account.move'].with_context({'force_company': sale_company_id.id}).create(sale_invoice_values)
                is_purchase_invoice_created = self.env['account.move'].with_context({'force_company': purchase_company_id.id}).create(purchase_invoice_values)

                if is_sale_invoice_created and is_purchase_invoice_created:
                    lines.write({'is_invoiced': True})
                    stock_lines.write({'is_invoiced': True})
                    # TODO: does it work to give an array with a 6 ?
                    is_sale_invoice_created.write({'account_analytic_line_ids': [(6, False, sale_invoice_lines.ids)]})
                    is_purchase_invoice_created.write({'account_analytic_line_ids': [(6, False, purchase_invoice_lines.ids)]})

    def _prepare_account_move_values(self, type, partner_id):
        """
        prepare values to create an account move
        :param type: out_invoice or in_invoice, so sale or purchase
        :param partner_id
        :return: dict of values for creation
        """
        return {
            'type': type,
            'partner_id': partner_id,
            'invoice_line_ids': []
        }
    
    def _prepare_account_move_line_values(self, product_quantity, product_id, company_id):
        """
        prepare values to create an account move line (timesheets)
        :param product_quantity
        :param product_id
        :param company_id
        :return: dict of values for creation
        """
        return [(0, False, {
            'product_id': product_id.with_context({'force_company': company_id.id}).id,
            'quantity': product_quantity,
            'price_unit': product_id.list_price,
        })]

    def _prepare_account_move_lines_values_stock(self, stock_moves_per_companies, company_id):
        """
        prepare values to create account move lines (stock moves)
        :param stock_moves_per_companies: stock moves to use to create the lines
        :param company_id
        :return: dict of values for creation
        """
        account_move_line_values = []

        for stock_move in stock_moves_per_companies:
            account_move_line_values.append(
                (0, False, {
                    'product_id': stock_move.product_id.with_context({'force_company': company_id.id}).id,
                    'quantity': stock_move.quantity_done,
                    'price_unit': stock_move.product_id.list_price
                })
            )

        return account_move_line_values

    def run(self):
        """
        intercompany invoicing
        :return: action to reload
        """
        timesheets = self.sudo().get_timesheets()
        stock_moves = self.sudo().get_stock_moves()

        if timesheets or stock_moves:
            ordered_timesheets = self.sudo().get_time_to_invoice_per_company(timesheets)
            ordered_stock_moves = self.sudo().get_products_to_invoice_per_company(stock_moves)
            self.create_invoices(ordered_timesheets, ordered_stock_moves)

        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }
    
    def clear_is_invoiced_bool(self, aal_ids=[], sm_ids=[]):
        """
        clear all the is_invoiced fields
        this function can not be run in web, use this by shell
        :param aal_ids: timesheets to clear
        :param sm_ids: stock moves to clear
        :return: boolean
        """
        aal_env = self.env['account.analytic.line']
        sm_env = self.env['stock.move']
        aal = sm = False

        aal = aal_env.search([('is_invoiced', '=', True)]) if not aal_ids else aal_env.browse(aal_ids)
        sm = sm_env.search([('is_invoiced', '=', True)]) if not sm_ids else sm_env.browse(sm_ids)

        aal.write({'is_invoiced': False})
        sm.write({'is_invoiced': False})

        return True
