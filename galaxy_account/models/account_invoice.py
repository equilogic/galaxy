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
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
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

    @api.model
    def move_line_get(self, invoice_id):
        res = super(account_invoice_line, self).move_line_get(invoice_id)
        inv = self.env['account.invoice'].browse(invoice_id)
        if inv.landed_cost_price and inv.landed_cost_price > 0.0:
            acc_id = False
            for line in inv.invoice_line:
                acc_id = line.account_id and line.account_id.id or False
            res.append({'uos_id': False, 'account_id': acc_id, 'price_unit': inv.landed_cost_price,
                        'name': 'Landed Cost', 'product_id': False, 'taxes': False,
                        'invl_id': False, 'account_analytic_id': False,
                        'type': 'dest', 'price': inv.landed_cost_price,
                        'quantity': 1.0})
        return res


class account_invoice(models.Model):
    _inherit = "account.invoice"
    
    vehicle_name = fields.Char('Vehicle Name')
    container_name = fields.Char('Container Name')
    container_place_area_code = fields.Char('Container Place Area Code')
    invoice_from_sale = fields.Boolean('Invoice From Sale')
    invoice_from_purchase = fields.Boolean('Invoice From Purchase')
    ship_via_id = fields.Many2one('ship.via', 'Ship Via')
    cases_id = fields.Many2one('cases.loc', 'Cases')
    from_id = fields.Many2one('from.loc', 'From')
    port_name_id = fields.Many2one('port.name', 'Port')
    insurence_covered_id = fields.Many2one('insurence.covered', 'Insurance Covered')
    vessale_name_id = fields.Many2one('vessale.name', 'Vessale')
    bank = fields.Char('Bank')
    currency_rate = fields.Float(string='Currency rate', digits=(16,4))
    
    part_inv_id = fields.Many2one('res.partner', 'Invoice Address', readonly=True, required=True,
                                  states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                  help="Invoice address for current sales order.")
    cust_add = fields.Text('Customer Address', readonly=True, states={'draft': [('readonly', False)]})
    part_inv_add = fields.Text('Invoice Address', readonly=True, states={'draft': [('readonly', False)]})
    part_ship_add = fields.Text('Delivery Address', readonly=True, states={'draft': [('readonly', False)]})
    

    part_ship_id = fields.Many2one('res.partner', 'Delivery Address', readonly=True, required=True,
                                   states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                   help="Delivery address for current sales order.")
    attn_inv = fields.Many2one('res.partner', 'ATTN')

    landed_cost = fields.One2many('landed.cost.invoice','acc_inv_id',string='Landed Cost')
    landed_cost_price = fields.Float(compute='_compute_amount',store=True,string='Landed Amount')
    customer_po = fields.Char(string="Customer PO")
    delivery_status =fields.Char(string="Delivery Status")
    export = fields.Boolean('Export')
    
    @api.onchange('currency_id')
    def onchange_currency_id(self):
        for rec in self:
            curr = rec.currency_id
            if curr:
                rec.currency_rate = curr and \
                            curr.rate_silent or 0.0
    
    @api.v7
    def _check_check_currency_rate(self, cr, uid, ids, context=None):
        curr_day = datetime.now().strftime('%A')
        curr_dt = datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)
        flag = False
        if curr_day == 'Tuesday':
            for invoice in self.browse(cr, uid, ids, context=context):
                if invoice.currency_id and invoice.currency_id.rate_ids:
                    for rate_line in invoice.currency_id.rate_ids:
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
        (_check_check_currency_rate, 'Please Update Current Currency rate !', ['currency_id'])
    ]
    
    @api.multi
    def onchange_partner_id(self, type, partner_id, date_invoice=False,
            payment_term=False, partner_bank_id=False, company_id=False):
        inv_add_list=[]
        ship_add_list=[]
        cust_add_list=[]
        inv_address=''
        ship_address=''
        cust_address=''
        res = super(account_invoice, self).onchange_partner_id(type=type, partner_id=partner_id,
                                    date_invoice=date_invoice, payment_term=payment_term,
                                    partner_bank_id=partner_bank_id, company_id=company_id)

        part = self.env['res.partner'].browse(partner_id)
        res_inv = part.address_get(adr_pref=['delivery', 'invoice', 'contact']).get('invoice')
        res_ship = part.address_get(adr_pref=['delivery', 'invoice', 'contact']).get('delivery')
        
        
        if part.street:
            cust_add_list.append(part.street +'\n')
        if part.street2:
            cust_add_list.append(part.street2 +'\n')
        if part.city:
            cust_add_list.append(part.city +'\n')
        if part.state_id:
            cust_add_list.append(part.state_id.code +' ')
        if part.zip:
            cust_add_list.append(part.zip +'\n')
        if part.country_id:
            cust_add_list.append(part.country_id.name +' ')

        for cust_add in cust_add_list:
            cust_address += cust_add
        part_inv = self.env['res.partner'].browse(res_inv)
        if part_inv.street:
            inv_add_list.append(part_inv.street +'\n')
        if part_inv.street2:
            inv_add_list.append(part_inv.street2 +'\n')
        if part_inv.city:
            inv_add_list.append(part_inv.city +'\n')
        if part_inv.state_id:
            inv_add_list.append(part_inv.state_id.code +' ')
        if part_inv.zip:
            inv_add_list.append(part_inv.zip +'\n')
        if part_inv.country_id:
            inv_add_list.append(part_inv.country_id.name +' ')
        
        
        for inv_add in inv_add_list:
            inv_address += inv_add
            
        ship_inv = self.env['res.partner'].browse(res_ship)
       
        if ship_inv.street:
            ship_add_list.append(ship_inv.street +'\n')
        if ship_inv.street2:
            ship_add_list.append(ship_inv.street2 +'\n')
        if ship_inv.city:
            ship_add_list.append(ship_inv.city +'\n')
        if ship_inv.state_id:
            ship_add_list.append(ship_inv.state_id.code +' ')
        if ship_inv.zip:
            ship_add_list.append(ship_inv.zip +'\n')
        if ship_inv.country_id:
            ship_add_list.append(ship_inv.country_id.name +' ')
        
        
        for ship_add in ship_add_list:
            ship_address += ship_add

        res['value'].update({'part_inv_id':res_inv,
                             'part_ship_id':res_ship,
                             'cust_add':cust_address,
                             'part_inv_add':inv_address,
                             'part_ship_add':ship_address
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
    def prepare_order_line(self):
        cr, uid, context = self.env.args
        so_obj = self.env['sale.order']
        so_line_obj = self.env['sale.order.line']
        po_obj = self.env['purchase.order']
        po_line_obj = self.env['purchase.order.line']
        acc_vou = self.env['account.voucher']

        loc_id = self.env['stock.location'].search([('location_id','!=',False),('location_id.name','ilike','WH'),
                    ('company_id.id','=',self.company_id.id),('usage','=','internal')])
    
        
        
        if self.type == "out_invoice" and not self.invoice_from_sale:
            order_vals = {
                          'partner_id': self.partner_id.id,
                          'partner_invoice_id':self.part_inv_id.id,
                          'partner_shipping_id':self.part_ship_id.id,
                          'date_order': self.date_invoice,
                          'pricelist_id': self.partner_id.property_product_pricelist.id,
                          'active': True,
                          'account_id': self._ids,
                          'attn_sal':self.attn_inv.id,
                          'landed_cost_sal':[(6,0,self.landed_cost.ids)],
                          'landed_cost_price':self.landed_cost_price,
                          'currency_rate': self.currency_rate,
                          'customer_po': self.customer_po,
                          'direct_invoice': True,
                          'invoice_ids': self.ids,
                          }
            res = so_obj.create(order_vals)
            for line in self.invoice_line:
                vals = {
                        'product_id' : line.product_id.id,
                        'name' : line.name,
                        'product_uom_qty' : line.quantity,
                        'product_uom' :line.uos_id.id or 1,
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
                    pick_id.invoice_id = self._ids
                    pick_id.do_transfer()
        if self.type == "in_invoice" and not self.invoice_from_purchase:
            product_ids = []
            invoice_method='picking'
            flag = False
            if self.invoice_line:
                for line in self.invoice_line:
                    if line.product_id.id:
                        flag = True
            if flag == False:
                invoice_method='manual'
            order_vals = {
                          'partner_id': self.partner_id.id,
                          'partner_inv_id':self.part_inv_id.id,
                          'partner_ship_id':self.part_ship_id.id,
                          'invoice_method': invoice_method,
                          'partner_ref':self.reference,
                          'date_order': self.date_invoice,
                          'pricelist_id': self.partner_id.property_product_pricelist.id,
                          'invoiced':True,
                          'active': True,
                          'currency_id':self.currency_id.id,
                          'account_id': self._ids,
                          'location_id' : loc_id.id,#self.partner_id.property_stock_supplier.id,
                          'attn_pur':self.attn_inv.id,
                          'landed_cost_pur':[(6,0,self.landed_cost.ids)],
                          'total_cost_price':self.landed_cost_price,
                          'invoice_ids':[(4, self.ids)],
                          'currency_rate': self.currency_rate,
                          'partner_ref': self.supplier_invoice_number,
                          'direct_invoice': True
                          }
            po_res = po_obj.create(order_vals)
            for line in self.invoice_line:
                vals = {
                        'product_id' : line.product_id.id,
                        'name' : line.name,
                        'date_planned':self.date_invoice,
                        'product_qty' : line.quantity,
                        'product_uom' :line.uos_id.id or 1,
                        'price_unit':line.price_unit,
                        'taxes_id': [(6, 0, [x.id for x in line.invoice_line_tax_id])],
                        'discount':line.discount,
                        'price_subtotal':line.price_subtotal,
                        'origin_ids': [(6, 0, line.origin_ids.ids)],
                        'no_origin':line.no_origin,
                        'order_id':po_res.id,
                        }
                po_res1 = po_line_obj.create(vals)
            po_res.signal_workflow('purchase_confirm')
            
            if po_res.picking_ids:
                for pick_id in po_res.picking_ids:
                    pick_id.active = True
                    pick_id.invoice_id = self._ids
                    pick_id.do_transfer()
    @api.multi
    def invoice_validate(self):
        prefix = ''
        cr,uid,context = self.env.args
        if self.partner_id and self.number:
            country = self.partner_id.country_id.name
            currency = self.currency_id.name
            if self.type=='out_invoice':
                if self.export == False: 
                    self.number = self.env['ir.sequence'].get('invoice_local')
                else:
                    if not self.partner_id.cust_code:
                        if self.type=="out_invoice":
                            raise except_orm(_('Error!'), _('Please Enter Customer code'))
                    cust_code = str(self.partner_id.cust_code) + '/'
                    prefix = cust_code[:3].upper()
                    cr.execute("select id from ir_sequence where name = %s",('Customer Invoice Export',))
                    res=cr.fetchone()
                    if res:                    
                        cr.execute("update ir_sequence set prefix = %s where id=%s",(cust_code,res[0]))
                        seq_id = self.env['ir.sequence'].next_by_id(res[0])
                        self.number = seq_id
            if self.type=='in_invoice':
                self.number = self.env['ir.sequence'].get('sup_inv')
        self.prepare_order_line()
        return self.write({'state': 'open'})

    @api.multi
    def action_cancel(self):
        moves = self.env['account.move']
        quant_obj = self.env["stock.quant"]
        uom_obj = self.env['product.uom']
        sale_rec=''
        purchase_rec=''
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
            for pick in picking_rec:
                for move_rec in pick.move_lines:
                    return_dict = {'product_id': move_rec.product_id.id,
                                   'move_id': move_rec.id,
                                   'quantity': move_rec.product_uom_qty,
                                   }
                    return_line.append((0, 0, return_dict))
                    move_rec.write({'state': 'cancel'})
            picking_return_rec = self.env['stock.return.picking'].create({'product_return_moves': return_line, 'invoice_state': 'none'})
            for pick in picking_rec:
                new_picking, old_picking = picking_return_rec.with_context({'active_id': pick.id})._create_returns()
                pick.write({'state': 'cancel'})
                pick_obj = self.env['stock.picking'].browse(new_picking)
                pick_obj.do_transfer()
            if self.type=="out_invoice":
                sale_rec = self.env['sale.order'].search([('account_id', '=', self.ids[0])])
            if self.type=="in_invoice":
                purchase_rec = self.env['purchase.order'].search([('account_id', '=', self.ids[0])])
            if sale_rec:
                sale_rec.action_invoice_cancel()
            if purchase_rec:
                purchase_rec.write({'state':'except_invoice'})
        return True

class res_partner(models.Model):
    _inherit = 'res.partner'
    
    cust_code = fields.Char('Code')
    
#     _sql_constraints = [
#         ('cust_code_unique', 'unique(cust_code)', 'Please Enter Unique Customer Code.'),
#     ]

    @api.v7
    def _check_cust_code_unique(self, cr, uid, ids, context=None):
        for partner in self.browse(cr, uid, ids, context=context):
            if partner.customer == True and partner.cust_code:
                partners = self.search(cr, uid, [('cust_code', '=', partner.cust_code),
                                                 ('customer','=', True)])
                if partners and len(partners) > 1:
                    return False
        return True

#    @api.v7
#    def _check_supp_code_unique(self, cr, uid, ids, context=None):
#        for partner in self.browse(cr, uid, ids, context=context):
#            if partner.supplier == True and partner.cust_code:
#                partners = self.search(cr, uid, [('cust_code', '=', partner.cust_code),
#                                                 ('supplier','=', True)])
#                if partners and len(partners) > 1:
#                    return False
#        return True

    _constraints = [
        (_check_cust_code_unique, 'Please Enter Unique Customer Code.', ['cust_code']),
#        (_check_supp_code_unique, 'Please Enter Unique Supplier Code.', ['cust_code']),
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
    
class landed_cost_invoice(models.Model):
    _name='landed.cost.invoice'
    _rec_name = 'landed_id'
    
    acc_inv_id = fields.Many2one('account.invoice','Invoice')
    landed_id = fields.Many2one('landed.cost','Name')
    amount = fields.Float('Amount')
    acc_sal_id = fields.Many2one('sale.order','Sale Order')
    acc_pur_id = fields.Many2one('purchase.order','Sale Order')
    
    @api.onchange('landed_id')
    def onchange_landed_id(self):
        for rec in self:
            rec.amount=rec.landed_id.amount

    
class landed_cost(models.Model):
    _name='landed.cost'
    
    name = fields.Char('Name')
    amount = fields.Float('Amount')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
