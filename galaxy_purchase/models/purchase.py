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
    
    account_id = fields.Many2one('account.invoice', 'Invoice')
    amount_untaxed = fields.Float(compute="_amount_all", store=True,
                                  string='Untaxed Amount',
                                  help="The amount without tax")
    amount_tax = fields.Float(compute="_amount_all", store=True,
                              string='Taxes',
                              help="The tax amount")
    amount_total = fields.Float(compute="_amount_all",
                                store=True, string='Total')
    
    total_cost_price = fields.Float(compute="_amount_all",string='Landed Amount', help="The total Landed Cost Price")
    
    currency_rate = fields.Float(string='Currency rate')

    partner_inv_id = fields.Many2one('res.partner','Invoice Address',readonly=True,required=True,
                                  states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                  help="Invoice address for current sales order.")
    partner_ship_id = fields.Many2one('res.partner','Delivery Address',readonly=True,required=True,
                                   states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                   help="Delivery address for current sales order.")

    attn_pur = fields.Many2one('res.partner','ATTN')
    
    sup_inv_num = fields.Char('Supplier Invoice Number')

    landed_cost_pur = fields.One2many('landed.cost.invoice','acc_pur_id',string='Landed Cost')
    @api.multi
    def onchange_partner_id(self,partner_id):
        res = super(purchase_order,self).onchange_partner_id(partner_id)
        part = self.env['res.partner'].browse(partner_id)
        res_invoice= part.address_get(adr_pref=['delivery', 'invoice', 'contact']).get('invoice')
        res_shipping= part.address_get(adr_pref=['delivery', 'invoice', 'contact']).get('delivery')
        res['value'].update({'partner_inv_id':res_invoice,
                             'partner_ship_id':res_shipping})
        return res

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].get('purchase_order_new') or '/'
        res = super(purchase_order, self).create(vals)
        
        return res
    
    @api.multi
    @api.depends('order_line','landed_cost_pur')
    def _amount_all(self):
        line_obj = self.env['purchase.order.line']
        for order in self:
            val = val1 =val2= 0.0
            val3 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                line_price = line_obj._calc_line_base_price(line)
                line_qty = line_obj._calc_line_quantity(line)

                if line.taxes_id:
                    for tax_t in line.taxes_id:
                        for tax in tax_t.compute_all(line.price_unit, line.product_qty).get('taxes', {}):
                            val += tax.get('amount', 0.0)
            for landed_cost in order.landed_cost_pur:
                val3+=landed_cost.amount
            order.amount_tax = cur.round(val)
            order.amount_untaxed = cur.round(val1)
            order.total_cost_price = cur.round(val3)
            order.amount_total = cur.round(val) + cur.round(val1)+cur.round(val3)
        return True
    
    @api.v7
    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):
        res = super(purchase_order,self)._prepare_inv_line(cr, uid, account_id, order_line, context=context)
        res.update({'origin_ids':order_line.origin_ids.ids,'no_origin':order_line.no_origin})
        return res
    @api.v7
    def _prepare_invoice(self, cr, uid, order, line_ids, context=None):
        """Prepare the dict of values to create the new invoice for a
           purchase order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: purchase.order record to invoice
           :param list(int) line_ids: list of invoice line IDs that must be
                                      attached to the invoice
           :return: dict of value to create() the invoice
        """
        
        res = super(purchase_order,self)._prepare_invoice(cr, uid, order, line_ids, context=context)
        res.update({
                    'invoice_from_purchase':True,
                    'part_inv_id': order.partner_inv_id.id,
                    'part_ship_id':order.partner_ship_id.id,
                    'attn_inv':order.attn_pur.id,
                    'landed_cost':[(6,0,order.landed_cost_pur.ids)],
                    'landed_cost_price':order.total_cost_price,
                    
                    })
        return res





# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
