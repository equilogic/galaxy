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

class wiz_sale_register_report_list(models.TransientModel):
    _name = "wiz.sale.register.report.list"
    
    
    start_date = fields.Date('Start Date',required=True ,default=datetime.now().date().strftime("%Y-%m-01"))
    end_date = fields.Date('End Date',required=True, default=datetime.now().date())
    
    @api.multi
    def print_report(self):
        domain = []
        if self.start_date and self.end_date:
            domain = [("date", ">=", self.start_date), ("date", "<=", self.end_date)]
        return {
                'type':'ir.actions.act_window',
                'name':'Sale Register',
                'res_model':'sale.register.report.list.new',
                'view_type':'form',
                'view_mode':'tree,form',
            }

class sale_register_report_new(models.Model):
    _name='sale.register.report.list.new'
    _auto=False
    
    invoice_no = fields.Char('Invoice #',readonly=True)
    sales_no = fields.Char('Sales #',readonly=True)
    date = fields.Date('Date',readonly=True)
    customer_po_no = fields.Char('Customer Po No.',readonly=True)
    customer_name = fields.Char('Customer Name',readonly=True)
    amount = fields.Char('Amount',readonly=True)
    amount_due = fields.Char('Amount Due',readonly=True)


    _order = "date"

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'sale_register_report_list_new')
        cr.execute("""create or replace view sale_register_report_list_new as
            (SELECT inv.id,inv.number as invoice_no,inv.date_invoice as date,
                inv.customer_po as customer_po_no, rp.name as customer_name,
                concat(rc.name,rc.symbol,inv.amount_total) as amount, 
                concat(rc.name,rc.symbol,inv.residual) as amount_due,
                (SELECT string_agg(CAST(s_ord_rel.order_id as varchar), ',') FROM sale_order_invoice_rel s_ord_rel, sale_order s_ord where
                inv.id = s_ord_rel.invoice_id and s_ord.id = s_ord_rel.order_id) as sales_no
                FROM account_invoice inv
                INNER JOIN res_partner rp ON rp.id = inv.partner_id
                INNER JOIN res_currency rc on rc.id=inv.currency_id
                where inv.type = 'out_invoice'
                )""")



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

