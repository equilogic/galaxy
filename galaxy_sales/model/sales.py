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
from openerp.exceptions import except_orm, ValidationError
import openerp.addons.decimal_precision as dp

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'

    origin_ids = fields.Many2many('origin.origin', string='Origin')
    no_origin = fields.Boolean('No Origin')
    
    @api.model
    def _prepare_order_line_invoice_line(self,line, account_id=False):
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(line, account_id)
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
    currency_rate = fields.Float(string='Currency rate', digits=(16,4))
    active = fields.Boolean('Active', default=True, help="If the active field is set to False, it will allow you to hide the sale order without removing it.")
    attn_sal = fields.Many2one('res.partner', 'ATTN')
    account_id = fields.Many2one('account.invoice', 'Invoice')
    landed_cost_sal = fields.One2many('landed.cost.invoice','acc_sal_id',string='Landed Cost')
    customer_po = fields.Char('Customer PO')
    direct_invoice = fields.Boolean('Direct Invoice')


from openerp.osv import osv,fields
class sale_order(osv.osv):

    _inherit = 'sale.order'


    def _amount_all_wrapper(self, cr, uid, ids, field_name, arg, context=None):
        """ Wrapper because of direct method passing as parameter for function fields """
        return self._amount_all(cr, uid, ids, field_name, arg, context=context)

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'landed_cost_price':0.0,
            }
            val = val1 =val2= 0.0
            cur = order.pricelist_id.currency_id
            for cost in order.landed_cost_sal:
                val2 += cost.amount 
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context=context)
            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            res[order.id]['landed_cost_price'] = cur_obj.round(cr, uid, cur, val2)
            res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']\
                                            +res[order.id]['landed_cost_price'] 
        return res
    
    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()



    _columns = {
                
            'amount_untaxed': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'),
                             string='Untaxed Amount',
                            store={'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                                   'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10)},
                            multi='sums', help="The amount without tax.", track_visibility='always'),
            'amount_tax': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'),
                         string='Taxes',
                         store={'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                                'sale.order.line': (_get_order,
                             ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),},
                         multi='sums', help="The tax amount."),
            'amount_total': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Account'), 
                            string='Total',
                            store={
                            'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                            'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
                            },
                            multi='sums', help="The total amount."),
            'landed_cost_price': fields.function(_amount_all_wrapper, digits_compute=dp.get_precision('Purchase Price'), string='Landed amount',
                            store=True, multi="sums", help="The total Landed Cost Price"),
                
                }

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
        
        price_list_rec = self.env['product.pricelist'].browse(pricelist_id)
        if price_list_rec.currency_id:
            curr = price_list_rec.currency_id
            if res and res.get('value', False):
                res['value'].update({'currency_rate': price_list_rec.currency_id.rate_silent or 0.0})
            else:
                res.update({'value': {'currency_rate': price_list_rec.currency_id.rate_silent or 0.0}})
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
    
   
    @api.model
    def _prepare_invoice(self,order, lines):
        res = super(sale_order, self)._prepare_invoice(order, lines)
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
