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

class wiz_sale_register_report(models.TransientModel):
    _name = "wiz.sale.register.report"
    
    
    start_date = fields.Date('Start Date',required=True ,default=datetime.now().date().strftime("%Y-%m-01"))
    end_date = fields.Date('End Date',required=True, default=datetime.now().date())
    
    @api.multi
    def print_report(self):
        domain = []
        if self.start_date and self.end_date:
            domain = [("date", ">=", self.start_date), ("date", "<=", self.end_date)]
        return {
                'type':'ir.actions.act_window',
                'name':'Sale Register Report',
                'res_model':'sale.register.report.new',
                'view_type':'form',
                'view_mode':'tree,form',
            }

class sale_register_report(models.Model):
    _name='sale.register.report.new'
    _auto=False
    
    date = fields.Date('Date',readonly=True)
    sales_invoice_no = fields.Char('Invoice #',readonly=True)
    customer_po_no = fields.Char('Customer Po #',readonly=True)
    customer_name = fields.Char('Customer Name',readonly=True)
    total_amount = fields.Float('Amount', readonly=True)
    status = fields.Char('Status', readonly=True)
    residual_amount = fields.Float('Amount Due',readonly=True)

    _order = "date"

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'sale_register_report_new')
        cr.execute("""create or replace view sale_register_report_new as
                (
                    SELECT so.id,
                        so.name as sales_invoice_no,
                        so.date_order as date,
                        so.amount_tax as tax_amt,
                        so.amount_tax as tax_amt_in_sgd,
                        rp.name as customer_name,
                        so.amount_total as total_amount,
                        so.customer_po as customer_po_no,
                        0 as residual_amount,
                        so.state as status
                        
                    FROM sale_order so
                    INNER JOIN res_partner rp ON rp.id = so.partner_id
                    where so.direct_invoice ='f'
                    
                    
                )""")



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

