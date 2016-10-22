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
from openerp import tools

class wiz_item_register_detail(models.TransientModel):
    _name = "wiz.item.register.detail"

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    @api.multi
    def print_report(self):
        domain = []
        if self.start_date and self.end_date:
            domain = [("date", ">=", self.start_date), ("date", "<=", self.end_date)]
        return {
                'type':'ir.actions.act_window',
                'name':'Item Register Report',
                'res_model':'item.register.detail.report',
                'view_type':'form',
                'domain': domain,
                'view_mode':'tree,form',
            }


class item_register_detail_report(models.Model):
    _name='item.register.detail.report'
    _order ="date"
    _auto=False

    date = fields.Date('Date',readonly=True)
    src = fields.Char("Src")
    po_id = fields.Char("Id")
    memo = fields.Char("Memo")
    qty_change = fields.Float('Qty Change',readonly=True)
    start_qty = fields.Float('Starting Qty',readonly=True)
    amount = fields.Float('Amount',readonly=True)
    on_hand = fields.Float('On Hand',readonly=True)
    currency_id = fields.Many2one('res.currency', 'Currency')
    
    
    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'item_register_detail_report')
        cr.execute("""create or replace view item_register_detail_report as
            ( SELECT    po.id,po.date_order as date,po.origin as src,po.name as po_id,prod_temp.name as memo,
pol.product_qty as qty_change,po.amount_total as amount ,
po.currency_id as currency_id 
from purchase_order po
 INNER JOIN purchase_order_line pol ON pol.order_id = po.id
 INNER JOIN product_product prod ON prod.id = pol.product_id
 INNER JOIN product_template prod_temp ON prod_temp.id = prod.product_tmpl_id
            )""")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
