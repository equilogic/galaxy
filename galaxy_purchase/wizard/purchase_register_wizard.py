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
from openerp import tools

class wiz_purchase_register_report(models.TransientModel):
    _name = "wiz.purchase.register"
    
    
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    
    @api.multi
    def print_report(self):
        domain = []
        if self.start_date and self.end_date:
            domain = [("pdate", ">=", self.start_date), ("pdate", "<=", self.end_date)]
        return {
                'type':'ir.actions.act_window',
                'name':'Purchase Order Register Report',
                'res_model':'purchase.register.report',
                'view_type':'form',
                'domain': domain,
                'view_mode':'tree,form',
            }

class purchase_register_report(models.Model):
    _name='purchase.register.report'
    _auto=False
    
    pdate = fields.Date('Date',readonly=True)
    pur_order = fields.Char('PO #',readonly=True)
    sup_inv = fields.Char('Supplier Invoice #',readonly=True)
    sup_name = fields.Char('Supplier Name',readonly=True)
    amt = fields.Float('Amount',readonly=True)
    amt_due = fields.Float('Amount Due',readonly=True)
    state = fields.Char('Status',readonly=True)
#     received = fields.Boolean('Received',readonly=True)
    _order ="pdate"
    
    def init(self, cr):
        tools.drop_view_if_exists(cr, 'purchase_register_report')
        cr.execute("""create or replace view purchase_register_report as
            (SELECT in_inv.id,in_inv.number as pur_order,in_inv.date_invoice as pdate, 
                in_inv.amount_total as amt,in_inv.state as state,rp.name as sup_name,
                in_inv.supplier_invoice_number as sup_inv,in_inv.residual as amt_due
                FROM account_invoice in_inv
                INNER JOIN res_partner rp ON rp.id = in_inv.partner_id
                where in_inv.type = 'in_invoice'
                )""")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

