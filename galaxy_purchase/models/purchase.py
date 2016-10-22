# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Serpent Consulting Services Pvt. Ltd.
#    (<http://www.serpentcs.com>)
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

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp import SUPERUSER_ID

class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    origin_ids = fields.Many2many('origin.origin',string='Origin')
    no_origin = fields.Boolean('No Origin')

    landed_cost = fields.Selection([('shipping', 'Shipping Cost'),
                                    ('courier', 'Courier Cost'),
                                    ('charge', 'Charges')], default="shipping", string="Landed Cost")
    price = fields.Float('Price')


    @api.multi
    def onchange_product_id(self,pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft', context=None):

        res = super(purchase_order_line,self).onchange_product_id(pricelist_id, product_id, qty=qty, uom_id=uom_id,
            partner_id=partner_id, date_order=date_order, fiscal_position_id=fiscal_position_id, date_planned=date_planned,
            name=name, price_unit=price_unit, state='draft', context=context)
        
        prod_obj = self.env['product.product'].browse(product_id)
        if res and res.has_key('value'):
            res['value'].update({'name':prod_obj.name})
            
        if res and res.has_key('domain'):
            pro_env = self.env['product.product'].browse(product_id)
            prod_tmpl_id = pro_env and pro_env.product_tmpl_id \
                            and pro_env.product_tmpl_id.id or False
            if prod_tmpl_id:
                res['domain'].update({'origin_ids':[('product_id','in',[prod_tmpl_id])]})
        return res



class purchase_order(models.Model):
    
    _inherit = 'purchase.order'
    
    amount_untaxed = fields.Float(compute="_amount_all", store=True,
                                  string='Untaxed Amount',
                                  help="The amount without tax")
    amount_tax = fields.Float(compute="_amount_all", store=True,
                              string='Taxes',
                              help="The tax amount")
    amount_total = fields.Float(compute="_amount_all",
                                store=True, string='Total')
    
    total_cost_price = fields.Float(compute="_amount_all", store=True,
                              string='Cost Price', help="The total Cost Price")
    
    currency_rate = fields.Float(related="currency_id.rate_silent", string='Currency rate')

    @api.multi
    @api.depends('order_line')
    def _amount_all(self):
        line_obj = self.env['purchase.order.line']
        for order in self:
            val = val1 = 0.0
            val2 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val2 += line.price
                line_price = line_obj._calc_line_base_price(line)
                line_qty = line_obj._calc_line_quantity(line)

                if line.taxes_id:
                    for tax_t in line.taxes_id:
                        for tax in tax_t.compute_all(line.price_unit, line.product_qty).get('taxes', {}):
                            val += tax.get('amount', 0.0)
            order.amount_tax = val
            order.amount_untaxed = val1
            order.total_cost_price = val2
            order.amount_total = val + val1 + val2
        return True
    
    @api.v7
    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
        res = super(purchase_order,self)._prepare_inv_line(cr, uid, account_id, order_line, context=context)
        res.update({'origin_ids':order_line.origin_ids.id,'no_origin':order_line.no_origin})
        return res







# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
