# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models, api, _
from openerp.exceptions import Warning
from datetime import datetime
from openerp.tools.sql import drop_view_if_exists
from openerp import tools


class wiz_sale_order_register_report(models.TransientModel):
    _name = "wiz.sale.order.register"

    start_date = fields.Date('Start Date', required = True , default = datetime.now().date().strftime("%Y-%m-01"))
    end_date = fields.Date('End Date', required = True, default = datetime.now().date())

    @api.multi
    def print_report(self):
        domain = []
        if self.start_date and self.end_date:
            domain = [("date", ">=", self.start_date), ("date", "<=", self.end_date)]
        return {
                'type':'ir.actions.act_window',
                'name':'Sale Order Register Report',
                'res_model':'sale.order.register.report',
                'view_type':'form',
                'view_mode':'tree,form',
            }

class temp_range(models.Model):
    _name = 'temp.range'
    _description = 'A Temporary table used for Dashboard view'

    no = fields.Integer('Range')
    sale_order_no = fields.Char('Sale Order No.')
    customer_po_no = fields.Char('Customer Po No.', readonly = True)
    customer_name = fields.Char('Customer Name', readonly = True)
    order_amt_in_actual_curr = fields.Float('Order In Actual Currency', readonly = True)
    tax_amt = fields.Char('Tax Amount', readonly = True)
    state = fields.Selection([
                            ('draft', 'Draft Quotation'),
                            ('sent', 'Quotation Sent'),
                            ('cancel', 'Cancelled'),
                            ('waiting_date', 'Waiting Schedule'),
                            ('progress', 'Sales Order'),
                            ('manual', 'Sale to Invoice'),
                            ('shipping_except', 'Shipping Exception'),
                            ('invoice_except', 'Invoice Exception'),
                            ('done', 'Done'),
                            ], 'Status', readonly = True)
    date = fields.Date('Date', readonly = True)

class sale_order_register_report(models.Model):
    _name = 'sale.order.register.report'
    _auto = False

    no = fields.Integer('Sl.No.', readonly = True)
    date = fields.Date('Date', readonly = True)
    sale_order_no = fields.Char('Sale Order No.', readonly = True)
    customer_po_no = fields.Char('Customer Po No.', readonly = True)
    customer_name = fields.Char('Customer Name', readonly = True)
    order_amt_in_actual_curr = fields.Float('Order In Actual Currency', readonly = True)
    tax_amt = fields.Char('Tax Amount', readonly = True)
    state = fields.Selection([
                            ('draft', 'Draft Quotation'),
                            ('sent', 'Quotation Sent'),
                            ('cancel', 'Cancelled'),
                            ('waiting_date', 'Waiting Schedule'),
                            ('progress', 'Sales Order'),
                            ('manual', 'Sale to Invoice'),
                            ('shipping_except', 'Shipping Exception'),
                            ('invoice_except', 'Invoice Exception'),
                            ('done', 'Done'),
                            ], 'Status', readonly = True)
    _order = "no"

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'sale_order_register_report')
        cr.execute('delete from temp_range')
        cr.execute("SELECT distinct(so.id) as id,so.name as sale_order_no,so.date_order as date,\
                        so.amount_tax as tax_amt,rp.name as customer_name,\
                        so.state as state,\
                        so.amount_total as order_amt_in_actual_curr,\
                        so.customer_po as customer_po_no \
                    FROM sale_order so \
                    INNER JOIN res_partner rp ON rp.id = so.partner_id \
                    INNER JOIN sale_order_line sol ON sol.order_id = so.id")
        recs = cr.fetchall()
        counter = 1
        for i in recs:
            self.pool['temp.range'].create(cr, 1,
                                                {
                                                 'no':counter,
                                                'sale_order_no':i[1],
                                                'date':i[2],
                                                'tax_amt':i[3],
                                                'customer_name':i[4],
                                                'state':i[5],
                                                'order_amt_in_actual_curr':i[6],
                                                'customer_po_no':i[7],
                                                 })
            counter += 1

        cr.execute("""
            create or replace view sale_order_register_report as (
                select id,no,sale_order_no,date,tax_amt,customer_name,state,order_amt_in_actual_curr,customer_po_no from temp_range
            )""")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

