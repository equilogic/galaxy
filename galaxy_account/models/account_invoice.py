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
from openerp.exceptions import except_orm
from openerp.tools.translate import _


class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'
    
    prod_desc = fields.Text(related='product_id.description', string='Full Description')
    origin_ids = fields.Many2many('origin.origin', string='Origin')
    no_origin = fields.Boolean('NO Origin')
    
    @api.multi
    def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',
            partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
            company_id=None):

        res = super(account_invoice_line, self).product_id_change(product, uom_id, qty, name, type, \
                         partner_id, fposition_id, price_unit, currency_id, company_id)

        if res and res.has_key('domain'):
            pro_env = self.env['product.product'].browse(product)
            prod_tmpl_id = pro_env and pro_env.product_tmpl_id \
                            and pro_env.product_tmpl_id.id or False
            if prod_tmpl_id:
                res['domain'].update({'origin_ids':[('product_id', 'in', [prod_tmpl_id])]})
        return res

class account_invoice(models.Model):
    _inherit = "account.invoice"
    
    vehicle_name = fields.Char('Vehicle Name')
    container_name = fields.Char('Container Name')
    container_place_area_code = fields.Char('Container Place Area Code')
    invoice_from_sale = fields.Boolean('Invoice From Sale')
    ship_via_id = fields.Many2one('ship.via', 'Ship Via')
    cases_id = fields.Many2one('cases.loc', 'Cases')
    from_id = fields.Many2one('from.loc', 'From')
    port_name_id = fields.Many2one('port.name', 'Port')
    insurence_covered_id = fields.Many2one('insurence.covered', 'Insurance Covered')
    vessale_name_id = fields.Many2one('vessale.name', 'Vessale')
    bank = fields.Char('Bank')
    currency_rate = fields.Float(related="currency_id.rate_silent", string='Currency rate')
    
    part_inv_id = fields.Many2one('res.partner', 'Invoice Address', readonly=True, required=True,
                                  states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                  help="Invoice address for current sales order.")
    part_ship_id = fields.Many2one('res.partner', 'Delivery Address', readonly=True, required=True,
                                   states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                   help="Delivery address for current sales order.")
    attn_inv = fields.Many2one('res.partner', 'ATTN')

    landed_cost = fields.Many2many('landed.cost',string='Landed Cost')
    landed_cost_price = fields.Float(compute='_compute_amount',store=True,string='Landed Amount')
    
    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False, company_id=False):
        res = super(account_invoice, self).onchange_partner_id(type=type, partner_id=partner_id,
                                    date_invoice=date_invoice, payment_term=payment_term,
                                    partner_bank_id=partner_bank_id, company_id=company_id)

        part = self.env['res.partner'].browse(partner_id)
        res_inv = part.address_get(adr_pref=['delivery', 'invoice', 'contact']).get('invoice')
        res_ship = part.address_get(adr_pref=['delivery', 'invoice', 'contact']).get('delivery')
        res['value'].update({'part_inv_id':res_inv,
                             'part_ship_id':res_ship,
                             })
        return res
    
    
    @api.one
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount','landed_cost')
    def _compute_amount(self):
        val=0.0
        for cost in self.landed_cost:
            val += cost.amount
        self.landed_cost_price = self.currency_id.round(val)
        self.amount_untaxed = self.currency_id.round(sum(line.price_subtotal for line in self.invoice_line))
        self.amount_tax = self.currency_id.round(sum(line.amount for line in self.tax_line))
        self.amount_total = self.amount_untaxed + self.amount_tax+self.landed_cost_price
        

    @api.multi
    def prepare_sale_order_line(self):
        cr, uid, context = self.env.args
        so_obj = self.env['sale.order']
        so_line_obj = self.env['sale.order.line']
        acc_vou = self.env['account.voucher']
        
        if self.type == "out_invoice" and not self.invoice_from_sale:
            order_vals = {
                          'partner_id': self.partner_id.id,
                          'partner_invoice_id':self.part_inv_id.id,
                          'partner_shipping_id':self.part_ship_id.id,
                          'date_order': self.date_invoice,
                          'pricelist_id': self.partner_id.property_product_pricelist.id,
                          'invoiced':True,
                          'active': True,
                          'account_id': self._ids,
                          'attn_sal':self.attn_inv.id,
                          'landed_cost_sal':[(6,0,self.landed_cost.ids)],
                          'landed_cost_price':self.landed_cost_price,
                          }
            res = so_obj.create(order_vals)
            for line in self.invoice_line:
                vals = {
                        'product_id' : line.product_id.id,
                        'name' : line.name,
                        'product_uom_qty' : line.quantity,
                        'product_uom' :line.uos_id.id,
                        'price_unit':line.price_unit,
                        'tax_id': [(6, 0, line.invoice_line_tax_id.ids)],
                        'discount':line.discount,
                        'price_subtotal':line.price_subtotal,
                        'origin_ids': [(6, 0, line.origin_ids.ids)],
                        'order_id':res.id,
                        }
                res1 = so_line_obj.create(vals)
            res.signal_workflow('order_confirm')
            
            if res.picking_ids:
                for pick_id in res.picking_ids:
                    pick_id.active = True
                    pick_id.account_id = self._ids
                    pick_id.do_transfer()
       
    @api.multi
    def invoice_validate(self):
        prefix = ''
        cr,uid,context = self.env.args
        if self.partner_id and self.type == 'out_invoice':
            
            country = self.partner_id.country_id.name
            if self.number:
                if country and country == 'Singapore': 
                    self.number = self.env['ir.sequence'].get('invoice_local')
                else:
                    if not self.partner_id.cust_code:
                        raise except_orm(_('Error!'), _('Please Enter Customer code'))
                    cust_code = str(self.partner_id.cust_code)
                    prefix = cust_code[:3].upper()

                    seq_type={
                              'name': cust_code,
                              'code':'invoice_export_'+cust_code,
                              }
                    seq = {
                        'name': cust_code,
                        'code':'invoice_export_'+cust_code,
                        'prefix': prefix+'/',
                        'suffix':'/%(y)s',
                        'number_next':8151,
                        'number_increment': 1
                        }
                    cr.execute("select * from ir_sequence_type where code = %s",('invoice_export_'+cust_code,))
                    res=cr.fetchall()
                    if res == []:
                        sq_type=self.env['ir.sequence.type'].create(seq_type)
                        sq = self.env['ir.sequence'].create(seq)
                    self.number = self.env['ir.sequence'].get('invoice_export_'+cust_code)
        self.prepare_sale_order_line()
        return self.write({'state': 'open'})

    @api.multi
    def action_cancel(self):
        moves = self.env['account.move']
        quant_obj = self.env["stock.quant"]
        uom_obj = self.env['product.uom']
        for inv in self:
            if inv.move_id:
                moves += inv.move_id
            if inv.payment_ids:
                for move_line in inv.payment_ids:
                    if move_line.reconcile_partial_id.line_partial_ids:
                        raise except_orm(_('Error!'), _('You cannot cancel an invoice which is partially paid. You need to unreconcile related payment entries first.'))

        # First, set the invoices as cancelled and detach the move ids
        self.write({'state': 'cancel', 'move_id': False})
        self._log_event(-1.0, 'Cancel Invoice')
        picking_rec = self.env['stock.picking'].search([('account_id', '=', self.ids[0])])
        if picking_rec:
            return_line = []
            for move_rec in picking_rec.move_lines:
                return_dict = {'product_id': move_rec.product_id.id,
                               'move_id': move_rec.id,
                               'quantity': move_rec.product_uom_qty,
                               }
                return_line.append((0, 0, return_dict))
                move_rec.write({'state': 'cancel'})
            picking_return_rec = self.env['stock.return.picking'].create({'product_return_moves': return_line, 'invoice_state': 'none'})
            new_picking, old_picking = picking_return_rec.with_context({'active_id': picking_rec.id})._create_returns()
            picking_rec.write({'state': 'cancel'})
            pick_obj = self.env['stock.picking'].browse(new_picking)
            pick_obj.do_transfer()
            sale_rec = self.env['sale.order'].search([('account_id', '=', self.ids[0])])
            if sale_rec:
                sale_rec.action_invoice_cancel()
       
        return True

class res_partner(models.Model):
    _inherit = 'res.partner'
    
    cust_code = fields.Char('Customer Code')
    
    _sql_constraints = [
        ('cust_code_unique', 'unique(cust_code)', 'Please Enter Unique Customer Code'),
    ]

class ship_via(models.Model):
    _name = 'ship.via'
    
    name = fields.Char('Name')
    

class cases_loc(models.Model):
    _name = 'cases.loc'
    
    name = fields.Char('Name')
    
    
    
class from_loc(models.Model):
    _name = 'from.loc'
    
    name = fields.Char('Name')
    
    
class port_name(models.Model):
    _name = 'port.name'
    
    name = fields.Char('Name')
    

class insurence_covered(models.Model):
    _name = 'insurence.covered'
    
    name = fields.Char('Name')
    
    
class vessale_name(models.Model):
    _name = 'vessale.name'
    
    name = fields.Char('Name')
    


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
