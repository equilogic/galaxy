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
    
    @api.multi
    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self,pricelist_id, order_lines):
        res = super(sale_order,self).onchange_pricelist_id(pricelist_id, order_lines)
        cur_lst = []
        if self.partner_id and not self.partner_id.currency:
            raise except_orm(_('Error!'), _('PLease select Currency for Customer'))
        if self.pricelist_id and self.partner_id and self.partner_id.currency:
            for cur in self.partner_id.currency:
                cur_lst.append(cur.id)

            if self.pricelist_id.currency_id.id not in cur_lst:
                raise except_orm(_('Error!'), _('Customer Currency and Selected Currency are not Match'))
        return res

    @api.v7
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        res = super(sale_order, self)._prepare_invoice(cr, uid, order, lines)
        res.update({'invoice_from_sale':True})
        return res


class sale_advance_payment_inv(osv.osv_memory):
    _inherit = 'sale.advance.payment.inv'
    
    @api.v7
    def _prepare_advance_invoice_vals(self, cr, uid, ids, context=None):
        res = super(sale_advance_payment_inv, self)._prepare_advance_invoice_vals(cr, uid, ids, context=context)
        sale_obj = self.pool.get('sale.order')
        for val in res:
            val[1].update({'invoice_from_sale':True})

        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
