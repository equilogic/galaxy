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
import openerp.addons.decimal_precision as dp
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import except_orm


class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    origin_ids = fields.Many2many('origin.origin', string='Origin')
    no_origin = fields.Boolean('No Origin')

    @api.multi
    def onchange_product_id(self, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft', context=None):

        res = super(purchase_order_line, self).onchange_product_id(pricelist_id, product_id, qty=qty, uom_id=uom_id,
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
                res['domain'].update({'origin_ids':[('product_id', 'in', [prod_tmpl_id])]})
        return res



class purchase_order(models.Model):
    
    _inherit = 'purchase.order'

    account_id = fields.Many2one('account.invoice', 'Invoice')
    currency_rate = fields.Float(string='Currency rate', digits=(16,4))

    partner_inv_id = fields.Many2one('res.partner', 'Invoice Address', readonly=True, required=True,
                                  states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                  help="Invoice address for current sales order.")
    partner_ship_id = fields.Many2one('res.partner', 'Delivery Address', readonly=True, required=True,
                                   states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                   help="Delivery address for current sales order.")

    attn_pur = fields.Many2one('res.partner', 'ATTN')
    
    sup_inv_num = fields.Char('Supplier Invoice Number')
    direct_invoice = fields.Boolean('Direct Invoice')

    landed_cost_pur = fields.One2many('landed.cost.invoice', 'acc_pur_id', string='Landed Cost')

    @api.onchange('currency_id')
    def onchange_currency_id(self):
        for rec in self:
            curr = rec.currency_id
            if curr:
                rec.currency_rate = curr and \
                            curr.rate_silent or 0.0

    @api.v7
    def _check_pur_currency_rate(self, cr, uid, ids, context=None):
        curr_day = datetime.now().strftime('%A')
        curr_dt = datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)
        flag = False
        if curr_day == 'Tuesday':
            for purchase in self.browse(cr, uid, ids, context=context):
                if purchase.currency_id and purchase.currency_id.rate_ids:
                    for rate_line in purchase.currency_id.rate_ids:
                        if rate_line.name:
                            rate_dt = datetime.strptime(rate_line.name, DEFAULT_SERVER_DATETIME_FORMAT)
                            if curr_dt == rate_dt.date().strftime(DEFAULT_SERVER_DATE_FORMAT):
                                flag = True
            if not flag:
                return False
            else:
                return True
        return True

    _constraints = [
        (_check_pur_currency_rate, 'Please Update Current Currency rate !', ['currency_id'])
    ]
    

from openerp.osv import osv,fields

class purchase_order(osv.osv):

    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].get('purchase_order_new') or '/'
        res = super(purchase_order, self).create(vals)
        
        return res

    @api.multi
    def onchange_partner_id(self,partner_id):
        res = super(purchase_order, self).onchange_partner_id(partner_id)
        part = self.env['res.partner'].browse(partner_id)
        res_invoice = part.address_get(adr_pref=['delivery', 'invoice', 'contact']).get('invoice')
        res_shipping = part.address_get(adr_pref=['delivery', 'invoice', 'contact']).get('delivery')
        res['value'].update({'partner_inv_id':res_invoice,
                             'partner_ship_id':res_shipping})
        return res

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        cur_obj=self.pool.get('res.currency')
        line_obj = self.pool['purchase.order.line']
        for order in self.browse(cr, uid, ids, context=context):
            
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'total_cost_price':0.0,
            }
            val = val1 =val2= 0.0
            cur = order.pricelist_id.currency_id
            for landed_cost in order.landed_cost_pur:
                val2+=landed_cost.amount
            for line in order.order_line:
                val1 += line.price_subtotal
                line_price = line_obj._calc_line_base_price(cr, uid, line,
                                                            context=context)
                line_qty = line_obj._calc_line_quantity(cr, uid, line,
                                                        context=context)
                for c in self.pool['account.tax'].compute_all(
                        cr, uid, line.taxes_id, line_price, line_qty,
                        line.product_id, order.partner_id)['taxes']:
                    val += c.get('amount', 0.0)
            res[order.id]['amount_tax']=cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed']=cur_obj.round(cr, uid, cur, val1)
            res[order.id]['total_cost_price']=cur_obj.round(cr, uid, cur, val2)
            res[order.id]['amount_total']=res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] \
                                          +res[order.id]['total_cost_price']
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()



    _columns = {
                
            'amount_untaxed': fields.function(_amount_all, digits_compute=dp.get_precision('Purchase Price'), string='Untaxed Amount',
                              store={'purchase.order.line': (_get_order, None, 10),}, multi="sums", help="The amount without tax", track_visibility='always'),
            'amount_tax': fields.function(_amount_all, digits_compute=dp.get_precision('Purchase Price'), string='Taxes',
                        store={'purchase.order.line': (_get_order, None, 10),}, multi="sums", help="The tax amount"),
            'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Purchase Price'), string='Total',
                            store={'purchase.order.line': (_get_order, None, 10),}, multi="sums", help="The total amount"),
            'total_cost_price': fields.function(_amount_all, digits_compute=dp.get_precision('Purchase Price'), string='Landed amount',
                            store=True, multi="sums", help="The total Landed Cost Price"),
                
                }
    @api.model
    def _prepare_inv_line(self, account_id, order_line):
        cr, uid, context = self.env.args
        res = super(purchase_order, self)._prepare_inv_line(account_id, order_line)
        res.update({'origin_ids':order_line.origin_ids.ids, 'no_origin':order_line.no_origin})
        return res
    
    @api.model
    def _prepare_invoice(self, order, line_ids):
        """Prepare the dict of values to create the new invoice for a
           purchase order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: purchase.order record to invoice
           :param list(int) line_ids: list of invoice line IDs that must be
                                      attached to the invoice
           :return: dict of value to create() the invoice
        """
        
        res = super(purchase_order, self)._prepare_invoice(order, line_ids)
        res.update({
                    'invoice_from_purchase':True,
                    'part_inv_id': order.partner_inv_id.id,
                    'part_ship_id':order.partner_ship_id.id,
                    'attn_inv':order.attn_pur.id,
                    'landed_cost':[(6, 0, order.landed_cost_pur.ids)],
                    'landed_cost_price':order.total_cost_price,
                    
                    })
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
