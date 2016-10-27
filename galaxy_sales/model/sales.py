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
from openerp.osv import osv
from openerp.tools.translate import _
from openerp.exceptions import except_orm, ValidationError

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    origin_ids = fields.Many2many('origin.origin', string='Origin')
    no_origin = fields.Boolean('No Origin')
    
    @api.v7
    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line, account_id, context=context)
        res.update({'origin_ids': [(6, 0, line.origin_ids.ids)], 'no_origin': line.no_origin})
        return res

    @api.multi
    def product_id_change(self, pricelist, product, qty=0,
                            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                            lang=False, update_tax=True, date_order=False, packaging=False,
                            fiscal_position=False, flag=False, context=None):

        res = super(sale_order_line, self).product_id_change(pricelist, product, qty=qty,
                            uom=uom, qty_uos=qty_uos, uos=uos, name='', partner_id=partner_id,
                            lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging,
                            fiscal_position=fiscal_position, flag=flag, context=context)
        prod_obj = self.env['product.product'].browse(product)
        if res and res.has_key('value'):
            res['value'].update({'name':prod_obj.name})
        if res and res.has_key('domain'):
            pro_env = self.env['product.product'].browse(product)
            prod_tmpl_id = pro_env and pro_env.product_tmpl_id \
                            and pro_env.product_tmpl_id.id or False
            if prod_tmpl_id:
                res['domain'].update({'origin_ids':[('product_id', 'in', [prod_tmpl_id])]})
        return res
    
class sale_order(models.Model):
    _inherit = "sale.order"


    pricelist_id = fields.Many2one('product.pricelist', 'Currency', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Pricelist for current sales order.")
    currency_rate = fields.Float(related="pricelist_id.currency_id.rate_silent", string='Currency rate')
    active = fields.Boolean('Active', default=True, help="If the active field is set to False, it will allow you to hide the sale order without removing it.")
    attn_sal = fields.Many2one('res.partner', 'ATTN')
    landed_cost_sal = fields.Many2many('landed.cost', string="Landed Cost")
    landed_cost_price = fields.Float(compute='_amount_all', string='Landed Amount', help="landed cost price", store=True)
    
    amount_untaxed = fields.Float(compute="_amount_all", store=True,
                                  string='Untaxed Amount',
                                  help="The amount without tax")
    amount_tax = fields.Float(compute="_amount_all", store=True,
                              string='Taxes',
                              help="The tax amount")
    amount_total = fields.Float(compute="_amount_all",
                                store=True, string='Total')
    
    @api.multi
    @api.depends('order_line', 'landed_cost_sal')
    def _amount_all(self):
        cur_obj = self.env['res.currency']
        for order in self:
            val = val1 = val2 = 0.0
            cur = self.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(line)
            for cost in order.landed_cost_sal:
                val2 += cost.amount 
            order.amount_tax = cur.round(val)
            order.amount_untaxed = cur.round(val1)
            order.landed_cost_price = cur.round(val2)
            order.amount_total = cur.round(val) + cur.round(val1) + cur.round(val2)

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].get('sale_order_new') or '/'
        res = super(sale_order, self).create(vals)
        
        return res
    
    @api.multi
    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self, pricelist_id, order_lines):
        res = super(sale_order, self).onchange_pricelist_id(pricelist_id, order_lines)
        cur_lst = []
        
        price_list_obj = self.env['product.pricelist'].browse(pricelist_id)
        if self.partner_id and not self.partner_id.currency:
            raise except_orm(_('Error!'), _('PLease select Currency for Customer'))
        if self.pricelist_id and self.partner_id and self.partner_id.currency:
            for cur in self.partner_id.currency:
                cur_lst.append(cur.id)

            if self.pricelist_id.currency_id.id not in cur_lst:
                raise except_orm(_('Error!'), _('Customer Currency and Selected Currency are not Match'))
        return res

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self, part):
        res = super(sale_order, self).onchange_partner_id(part)

        if part:
            partner_data = self.env['res.partner'].browse(part)
            if partner_data and partner_data.country_id:
                price_list_ids = self.env['product.pricelist'].search([('currency_id', '=', partner_data.country_id and partner_data.country_id.currency_id.id)])
                if price_list_ids:
                    res['value']['pricelist_id'] = price_list_ids.ids
            else:
                res['value']['pricelist_id'] = partner_data.property_product_pricelist.id
        return res
    
   
    @api.v7
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        res = super(sale_order, self)._prepare_invoice(cr, uid, order, lines)
        res.update({'invoice_from_sale':True,
                    'part_inv_id':order.partner_invoice_id.id,
                    'part_ship_id':order.partner_shipping_id.id,
                    'attn_inv':order.attn_sal.id,
                    'landed_cost':[(6, 0, order.landed_cost_sal.ids)],
                    'landed_cost_price':order.landed_cost_price,
                    })
        return res


class sale_advance_payment_inv(osv.osv_memory):
    _inherit = 'sale.advance.payment.inv'
    
    @api.multi
    def _prepare_advance_invoice_vals(self):
        res = super(sale_advance_payment_inv, self)._prepare_advance_invoice_vals()
        sale = self.env['sale.order'].browse(self._context.get('active_id'))
        for val in res:
            val[1].update({'invoice_from_sale':True,
                           'part_inv_id':sale.partner_invoice_id.id,
                           'part_ship_id':sale.partner_shipping_id.id,
                           'attn_inv':sale.attn_sal.id,
                           'landed_cost':[(6, 0, sale.landed_cost_sal.ids)],
                           'landed_cost_price':sale.landed_cost_price,
                           })
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
