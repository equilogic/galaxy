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

class wiz_product_wise_sale_report_1(models.TransientModel):
    _name = "wiz.product.wise.sale.report.1"
    
    
    start_date = fields.Date('Start Date',required=True ,default=datetime.now().date().strftime("%Y-%m-01"))
    end_date = fields.Date('End Date',required=True, default=datetime.now().date())
    
    @api.multi
    def print_report(self):
        domain = []
        if self.start_date and self.end_date:
            domain = [("date", ">=", self.start_date), ("date", "<=", self.end_date)]
        return {
                'type':'ir.actions.act_window',
                'name':'product wise sale report 1',
                'res_model':'product.wise.sale.report.1',
                'view_type':'form',
                'domain':domain,
                'view_mode':'tree,form',
            }

class product_wise_sale_report_1(models.Model):
    _name='product.wise.sale.report.1'
    _auto=False
    
    date = fields.Date('date')
    customer_name = fields.Char('Customer Name',readonly=True)
    product_name = fields.Char('Product Name',readonly=True)
    qty = fields.Float('Qty',readonly=True)
    amt_in_actual_currency = fields.Float('Amount In Actual Currency',readonly=True)
    amt_in_sgd = fields.Float('Amt In Sgd',readonly=True)

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'product_wise_sale_report_1')

        cr.execute("""create or replace view product_wise_sale_report_1 as
            (SELECT so.id,rp.name as customer_name,sol.name as product_name,
                sol.product_uom_qty as qty,so.date_order as date,
                so.amount_total as amt_in_actual_currency,so.amount_total as amt_in_sgd
                FROM sale_order so
                INNER JOIN res_partner rp ON rp.id = so.partner_id
                INNER JOIN sale_order_line sol ON sol.order_id = so.id
                )""")



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

