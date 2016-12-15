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
from datetime import datetime, date, timedelta
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp.exceptions import except_orm, Warning
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

# mapping invoice type to journal type
TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale_refund',
    'in_refund': 'purchase_refund',
}

class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    @api.depends('product_id')
    def _compute_profoma_qty(self):
        for cost in self:
            if cost.product_id and cost.product_id.non_invenotry_item == False:
                line_ids = self.search([('product_id', '=', cost.product_id.id), ('invoice_id.state', '=', 'draft')])
                qty=0.0
                for line_id in line_ids:
                    if line_id.id != cost.id and line_id.invoice_id.id != cost.invoice_id.id :
                        qty += line_id.quantity
                cost.profoma_qty = int(qty)

    prod_desc = fields.Text(related = 'product_id.description', string = 'Full Description')
    origin_ids = fields.Many2many('origin.origin', string = 'Origin')
    no_origin = fields.Boolean('NO Origin')
    qty_on_hand = fields.Float(related = 'product_id.qty_available', string = 'Quantity On Hand', default = 0.0)
    profoma_qty = fields.Integer(compute = '_compute_profoma_qty', string = 'Profoma QTY',store = True)
    discount = fields.Float(string='Discount (%)',
                            digits=(16, 2),
                            # digits= dp.get_precision('Discount'),
                            default=0.0)

    @api.multi
    def product_id_change(self, product, uom_id, qty = 0, name = '', type = 'out_invoice',
            partner_id = False, fposition_id = False, price_unit = False, currency_id = False,
            company_id = None):

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

    @api.model
    def _default_journal(self):
        inv_type = self._context.get('type', 'out_invoice')
        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type', 'in', filter(None, map(TYPE2JOURNAL.get, inv_types))),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit = 1)

    @api.model
    def _default_currency(self):
        journal = self._default_journal()
        return journal.currency or journal.company_id.currency_id

    vehicle_name = fields.Char('Vehicle Name')
    container_id = fields.Many2one('container.container', 'Container Name')
    container_place_area_code = fields.Char('Container Place Area Code')
    invoice_from_sale = fields.Boolean('Invoice From Sale')
    invoice_from_purchase = fields.Boolean('Invoice From Purchase')
    ship_via_id = fields.Many2one('ship.via', 'Ship Via')
    cases_id = fields.Many2one('cases.loc', 'Cases')
    from_id = fields.Many2one('from.loc', 'Origin Port')
    port_name_id = fields.Many2one('port.name', 'Destination Port')
    insurence_covered_id = fields.Many2one('insurence.covered', 'Insurance Covered')
    vessale_name_id = fields.Many2one('vessale.name', 'Vessale')
    bank = fields.Char('Bank')
    currency_rate = fields.Float(string = 'Currency rate', digits = (16, 4))

    part_inv_id = fields.Many2one('res.partner', 'Invoice Address', readonly = True, required = True,
                                  states = {'draft': [('readonly', False)], 'sent': [('readonly', False)], 'open': [('readonly', False)]},
                                  help = "Invoice address for current sales order.")
    cust_add = fields.Text('Customer Address', readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]})
    part_inv_add = fields.Text('Invoice Address', readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]})
    part_ship_add = fields.Text('Delivery Address', readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]})


    part_ship_id = fields.Many2one('res.partner', 'Delivery Address', readonly = True, required = True,
                                   states = {'draft': [('readonly', False)], },
                                   help = "Delivery address for current sales order.")
    attn_inv = fields.Many2one('res.partner', 'ATTN')

    landed_cost = fields.One2many('landed.cost.invoice', 'acc_inv_id', string = 'Landed Cost')
    landed_cost_price = fields.Float(compute = '_compute_amount', store = True, string = 'Landed Amount')
    customer_po = fields.Char(string = "Customer PO")
    delivery_status = fields.Char(string = "Delivery Status")
    export = fields.Boolean('Export', readonly = True, states = {'draft': [('readonly', False)]})
    direct_shipemt = fields.Boolean('Direct Shipment', readonly = True, states = {'draft': [('readonly', False)]})

    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], 'Discount Type', readonly = True,
                                     states = {'draft': [('readonly', False)], 'open': [('readonly', False)]})
    discount_rate = fields.Float('Discount Rate',
                                 digits_compute = dp.get_precision('Account'),
                                 readonly = True,
                                 states = {'draft': [('readonly', False)], 'open': [('readonly', False)]})
    amount_discount = fields.Float(string = 'Discount',
                                   digits = dp.get_precision('Account'),
                                   readonly = True, compute = '_compute_amount',store=True)
    sequence_update =  fields.Boolean('Sequence updated')

    ####
    # This Fields Overrite to Edit its value after validate invoice.(TO Change Attrs and domains)
    ####
    partner_id = fields.Many2one('res.partner', string = 'Partner', change_default = True,
        required = True, readonly = True, states = {'draft': [('readonly', False)]},
        track_visibility = 'always')
    date_invoice = fields.Date(string = 'Invoice Date',
        readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]}, index = True,
        help = "Keep empty to use the current date", copy = False, default = date.today().strftime('%Y-%m-%d'))
    journal_id = fields.Many2one('account.journal', string = 'Journal',
        required = True, readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]},
        default = _default_journal,
        domain = "[('type', 'in', {'out_invoice': ['sale'], 'out_refund': ['sale_refund'], 'in_refund': ['purchase_refund'], 'in_invoice': ['purchase']}.get(type, [])), ('company_id', '=', company_id)]")
    account_id = fields.Many2one('account.account', string = 'Account',
        required = True, readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]},
        help = "The partner account used for this invoice.")
    fiscal_position = fields.Many2one('account.fiscal.position', string = 'Fiscal Position',
        readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]})
    company_id = fields.Many2one('res.company', string = 'Company', change_default = True,
        required = True, readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]},
        default = lambda self: self.env['res.company']._company_default_get('account.invoice'))
    payment_term = fields.Many2one('account.payment.term', string = 'Payment Terms',
        readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]},
        help = "If you use payment terms, the due date will be computed automatically at the generation "
             "of accounting entries. If you keep the payment term and the due date empty, it means direct payment. "
             "The payment term may compute several due dates, for example 50% now, 50% in one month.")
    user_id = fields.Many2one('res.users', string = 'Salesperson', track_visibility = 'onchange',
        readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]},
        default = lambda self: self.env.user)
    partner_bank_id = fields.Many2one('res.partner.bank', string = 'Bank Account',
        help = 'Bank Account Number to which the invoice will be paid. A Company bank account if this is a Customer Invoice or Supplier Refund, otherwise a Partner bank account number.',
        readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]})
    period_id = fields.Many2one('account.period', string = 'Force Period',
        domain = [('state', '!=', 'done')], copy = False,
        help = "Keep empty to use the period of the validation(invoice) date.",
        readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]})
    date_due = fields.Date(string = 'Due Date',
        readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]}, index = True, copy = False,
        help = "If you use payment terms, the due date will be computed automatically at the generation "
             "of accounting entries. The payment term may compute several due dates, for example 50% "
             "now and 50% in one month, but if you want to force a due date, make sure that the payment "
             "term is not set on the invoice. If you keep the payment term and the due date empty, it "
             "means direct payment.")
    origin = fields.Char(string = 'Source Document',
        help = "Reference of the document that produced this invoice.",
        readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]})
    name = fields.Char(string = 'Reference/Description', index = True,
        readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string = 'Currency',
        required = True, readonly = True, states = {'draft': [('readonly', False)]},
        default = _default_currency, track_visibility = 'always')
    supplier_invoice_number = fields.Char(string = 'Supplier Invoice Number',
        help = "The reference of this invoice as provided by the supplier.",
        readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]})
    invoice_line = fields.One2many('account.invoice.line', 'invoice_id', string = 'Invoice Lines',
        readonly = True, states = {'draft': [('readonly', False)], 'open': [('readonly', False)]}, copy = True)

    state = fields.Selection([
            ('draft', 'Proforma'),
            ('proforma', 'Pro-forma'),
            ('proforma2', 'Pro-forma'),
            ('open', 'Open'),
            ('paid', 'Paid'),
            ('cancel', 'Cancelled'),
        ], string = 'Status', index = True, readonly = True, default = 'draft',
        track_visibility = 'onchange', copy = False,
        help = " * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Pro-forma' when invoice is in Pro-forma status,invoice does not have an invoice number.\n"
             " * The 'Open' status is used when user create invoice,a invoice number is generated.Its in open status till user does not pay invoice.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")

    @api.onchange('part_ship_id')
    def onchange_part_ship_add(self):
        ship_add_list = []
        ship_address = ''
        for rec in self:
            res_ship = rec.partner_id.address_get(adr_pref = ['delivery', 'invoice', 'contact']).get('delivery')
            ship_inv = self.env['res.partner'].browse(res_ship)
            if ship_inv.street:
                ship_add_list.append(ship_inv.street + '\n')
            if ship_inv.street2:
                ship_add_list.append(ship_inv.street2 + '\n')
            if ship_inv.city:
                ship_add_list.append(ship_inv.city + '\n')
            if ship_inv.state_id:
                ship_add_list.append(ship_inv.state_id.code + ' ')
            if ship_inv.zip:
                ship_add_list.append(ship_inv.zip + '\n')
            if ship_inv.country_id:
                ship_add_list.append(ship_inv.country_id.name + ' ')

            for ship_add in ship_add_list:
                ship_address += ship_add
            rec.part_ship_add = ship_address

    @api.onchange('part_inv_add')
    def onchange_part_inv_add(self):
        inv_add_list = []
        inv_address = ''
        for rec in self:
            res_inv = rec.partner_id.address_get(adr_pref = ['delivery', 'invoice', 'contact']).get('invoice')
            part_inv = self.env['res.partner'].browse(res_inv)
            if part_inv.street:
                inv_add_list.append(part_inv.street + '\n')
            if part_inv.street2:
                inv_add_list.append(part_inv.street2 + '\n')
            if part_inv.city:
                inv_add_list.append(part_inv.city + '\n')
            if part_inv.state_id:
                inv_add_list.append(part_inv.state_id.code + ' ')
            if part_inv.zip:
                inv_add_list.append(part_inv.zip + '\n')
            if part_inv.country_id:
                inv_add_list.append(part_inv.country_id.name + ' ')
            for inv_add in inv_add_list:
                inv_address += inv_add
            rec.part_inv_add = inv_address

    @api.onchange('currency_id')
    def onchange_currency_id(self):
        for rec in self:
            curr = rec.currency_id
            if curr:
                rec.currency_rate = curr and \
                            curr.rate_silent or 0.0
    @api.one
    @api.onchange('currency_rate')
    def onchane_currency_rate(self):
        """
            This onchange method update latest currency rate manually
        """
        for rec in self:
            if rec.currency_rate:
                if rec.currency_id.rate_ids and rec.currency_id.rate_ids[0]:
                    rec.currency_id.rate_ids[0].write({'rate': rec.currency_rate})
                    
    @api.onchange('export')
    def onchange_export(self):
        """
            Onchange Export set 0% ZR in all invoice line
        """
        account_tax_pool = self.env['account.tax']
        account_line_pool = self.env['account.invoice.line']
        curr = self.env['res.currency'].search([('name', '=', 'USD')])
        curr_sgd = self.env['res.currency'].search([('name', '=', 'SGD')])
        for inv_rec in self:
            if inv_rec.export:
                inv_rec.currency_id = curr and curr.id
            else:
                inv_rec.currency_id = curr_sgd and curr_sgd.id
            if inv_rec.type == 'out_invoice' and inv_rec.export:
                zero_per_tax = account_tax_pool.search([('description', '=', '0% ZR')])
                if inv_rec.invoice_line:
                    for i_line in inv_rec.invoice_line:
                        if zero_per_tax:
                            i_line.write({'invoice_line_tax_id': [(6, 0, zero_per_tax.ids)], })
            if inv_rec.type == 'out_invoice' and not inv_rec.export:
                sr_per_tax = account_tax_pool.search([('description', '=', '7% SR')])
                if inv_rec.invoice_line:
                    for i_line in inv_rec.invoice_line:
                        if sr_per_tax:
                            i_line.write({'invoice_line_tax_id': [(6, 0, sr_per_tax.ids)], })

            if inv_rec.type == 'in_invoice' and inv_rec.export:
                zero_zp_tax = account_tax_pool.search([('description', '=', '0% ZP')])
                if inv_rec.invoice_line:
                    for i_line in inv_rec.invoice_line:
                        if zero_zp_tax:
                            i_line.write({'invoice_line_tax_id': [(6, 0, zero_zp_tax.ids)], })
            if inv_rec.type == 'in_invoice' and not inv_rec.export:
                tx_tax = account_tax_pool.search([('description', '=', '7% TX7')])
                if inv_rec.invoice_line:
                    for i_line in inv_rec.invoice_line:
                        if tx_tax:
                            i_line.write({'invoice_line_tax_id': [(6, 0, tx_tax.ids)], })
            self.env['account.invoice'].button_reset_taxes()
            
    @api.v7
    def _check_check_currency_rate(self, cr, uid, ids, context = None):
        curr_day = datetime.now().strftime('%A')
        curr_dt = datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT)
        flag = False
        if curr_day == 'Tuesday':
            for invoice in self.browse(cr, uid, ids, context = context):
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
    def onchange_partner_id(self, type, partner_id, date_invoice = False,
            payment_term = False, partner_bank_id = False, company_id = False):
        inv_add_list = []
        ship_add_list = []
        cust_add_list = []
        inv_address = ''
        ship_address = ''
        cust_address = ''
        res = super(account_invoice, self).onchange_partner_id(type = type, partner_id = partner_id,
                                    date_invoice = date_invoice, payment_term = payment_term,
                                    partner_bank_id = partner_bank_id, company_id = company_id)

        part = self.env['res.partner'].browse(partner_id)
        res_inv = part.address_get(adr_pref = ['delivery', 'invoice', 'contact']).get('invoice')
        res_ship = part.address_get(adr_pref = ['delivery', 'invoice', 'contact']).get('delivery')


        if part.street:
            cust_add_list.append(part.street + '\n')
        if part.street2:
            cust_add_list.append(part.street2 + '\n')
        if part.city:
            cust_add_list.append(part.city + '\n')
        if part.state_id:
            cust_add_list.append(part.state_id.code + ' ')
        if part.zip:
            cust_add_list.append(part.zip + '\n')
        if part.country_id:
            cust_add_list.append(part.country_id.name + ' ')

        for cust_add in cust_add_list:
            cust_address += cust_add
        part_inv = self.env['res.partner'].browse(res_inv)
        if part_inv.street:
            inv_add_list.append(part_inv.street + '\n')
        if part_inv.street2:
            inv_add_list.append(part_inv.street2 + '\n')
        if part_inv.city:
            inv_add_list.append(part_inv.city + '\n')
        if part_inv.state_id:
            inv_add_list.append(part_inv.state_id.code + ' ')
        if part_inv.zip:
            inv_add_list.append(part_inv.zip + '\n')
        if part_inv.country_id:
            inv_add_list.append(part_inv.country_id.name + ' ')


        for inv_add in inv_add_list:
            inv_address += inv_add

        ship_inv = self.env['res.partner'].browse(res_ship)

        if ship_inv.street:
            ship_add_list.append(ship_inv.street + '\n')
        if ship_inv.street2:
            ship_add_list.append(ship_inv.street2 + '\n')
        if ship_inv.city:
            ship_add_list.append(ship_inv.city + '\n')
        if ship_inv.state_id:
            ship_add_list.append(ship_inv.state_id.code + ' ')
        if ship_inv.zip:
            ship_add_list.append(ship_inv.zip + '\n')
        if ship_inv.country_id:
            ship_add_list.append(ship_inv.country_id.name + ' ')


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
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount', 'discount_type','discount_rate')
    def _compute_amount(self):
        val = 0.0
        discount = 0.0
        total = 0.0
        self.amount_untaxed = self.currency_id.round(sum(line.price_subtotal for line in self.invoice_line))
        if self.discount_type == 'percent':
            if self.discount_rate != 0:
                discount = (self.amount_untaxed*self.discount_rate) / 100.0
        else:
            discount = self.discount_rate
        if total == 0:
            total = 1
        self.amount_discount = discount * total
        self.amount_tax = self.currency_id.round(sum(line.amount for line in self.tax_line))
        self.amount_total = self.amount_untaxed + self.amount_tax - self.amount_discount

    @api.multi
    def prepare_order_line(self):
        """
        This method create sale order and purchase order
        ------------------------------------------------------
        @param self : object pointer
        """
        cr, uid, context = self.env.args
        so_obj = self.env['sale.order']
        so_line_obj = self.env['sale.order.line']
        po_obj = self.env['purchase.order']
        po_line_obj = self.env['purchase.order.line']
        acc_vou = self.env['account.voucher']

        loc_id = self.env['stock.location'].search([('location_id', '!=', False), ('location_id.name', 'ilike', 'WH'),
                    ('company_id.id', '=', self.company_id.id), ('usage', '=', 'internal')])
        prdouct_dict = {}
        if self.type == "out_invoice" and not self.invoice_from_sale:
            print "\n discount type========",self.discount_type
            order_vals = {
                          'partner_id': self.partner_id.id,
                          'partner_invoice_id':self.part_inv_id.id,
                          'partner_shipping_id':self.part_ship_id.id,
                          'date_order': self.date_invoice,
                          'pricelist_id': self.partner_id.property_product_pricelist.id,
                          'active': True,
                          'inv_id': self.id or False,
                          'attn_sal':self.attn_inv.id,
                          'landed_cost_sal':[(6, 0, self.landed_cost.ids)],
                          'landed_cost_price':self.landed_cost_price,
                          'currency_rate': self.currency_rate,
                          'customer_po': self.customer_po,
                          'direct_invoice': True,
                          'invoice_ids':[(4, self.ids)],
                          'amount_discount':self.amount_discount,
                          'discount_type':self.discount_type,
                          'discount_rate':self.discount_rate,
                          }
            res = so_obj.create(order_vals)
            for line in self.invoice_line:
                vals = {
                        'product_id' : line.product_id.id,
                        'name' : line.name,
                        'product_uom_qty' : line.quantity,
                        'product_uom' :line.uos_id.id or 1,
                        'inv_line_id': line.id or False,
                        'price_unit':line.price_unit,
                        'tax_id': [(6, 0, line.invoice_line_tax_id.ids)],
                        'discount':line.discount,
                        'price_subtotal':line.price_subtotal,
                        'origin_ids': [(6, 0, line.origin_ids.ids)],
                        'order_id':res.id,
                        }
                if self.direct_shipemt or line.product_id.non_invenotry_item:
                    rout_ids = self.env['stock.location.route'].search([('name', '=', 'Drop Shipping')])
                    if rout_ids:
                        vals.update({'route_id' : rout_ids and rout_ids[0].id})
                res1 = so_line_obj.create(vals)
#                 prdouct_dict[line.product_id.id] = {'line_id': res1.id}
                prdouct_dict[line.product_id.id] = {'line_id': line.id}
            res.signal_workflow('order_confirm')
            if res.picking_ids:
                for pick_id in res.picking_ids:
                    pick_id.active = True
                    pick_id.inv_id = self.id or False
                    pick_id.do_transfer()
                    for m_line in pick_id.move_lines:
                        inv_line_id = prdouct_dict.get(m_line.product_id.id).get('line_id', False)
                        self._cr.execute('update stock_move set inv_line_id=%s where id=%s', (inv_line_id, m_line.id,))
        if self.type == "in_invoice" and not self.invoice_from_purchase:
            product_ids = []
            invoice_method = 'manual'
            flag = False
#            if self.invoice_line:
#                for line in self.invoice_line:
#                    if line.product_id.id:
#                        flag = True
#            if flag == False:
#                invoice_method = 'manual'
            order_vals = {
                          'partner_id': self.partner_id.id,
                          'partner_inv_id':self.part_inv_id.id,
                          'partner_ship_id':self.part_ship_id.id,
                          'invoice_method': invoice_method,
                          'partner_ref':self.reference,
                          'date_order': self.date_invoice,
                          'pricelist_id': self.partner_id.property_product_pricelist.id,
                          'invoiced':True,
                          'currency_id':self.currency_id.id,
                          'inv_id': self.id or False,
                          'location_id' : loc_id.id,  # self.partner_id.property_stock_supplier.id,
                          'attn_pur':self.attn_inv.id,
                          'landed_cost_pur':[(6, 0, self.landed_cost.ids)],
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
                        'inv_line_id': line.id or False,
                        'date_planned':self.date_invoice,
                        'product_qty' : line.quantity,
                        'product_uom' :line.uos_id.id or False,
                        'price_unit':line.price_unit,
                        'taxes_id': [(6, 0, [x.id for x in line.invoice_line_tax_id])],
                        'price_subtotal':line.price_subtotal,
                        'origin_ids': [(6, 0, line.origin_ids.ids)],
                        'no_origin':line.no_origin,
                        'order_id':po_res.id,
                        }
                po_res1 = po_line_obj.create(vals)
                prdouct_dict[line.product_id.id] = {'line_id': line.id}
            po_res.signal_workflow('purchase_confirm')
            if not self.direct_shipemt:
                if po_res.picking_ids:
                    for pick_id in po_res.picking_ids:
                        pick_id.active = True
                        pick_id.inv_id = self.id or False
                        pick_id.do_transfer()
                        for m_line in pick_id.move_lines:
                            inv_line_id = prdouct_dict.get(m_line.product_id.id).get('line_id', False)
                            self._cr.execute('update stock_move set inv_line_id=%s where id=%s', (inv_line_id, m_line.id,))
        return True

    @api.multi
    def invoice_validate(self):
        """
        This method used for create sales order when invoice
        validated.
        """
#         prefix = ''
        cr, uid, context = self.env.args
#         if self.partner_id and self.number:
#             country = self.partner_id.country_id.name
#             currency = self.currency_id.name
#             if self.type=='out_invoice':
#                 if self.export == False:
#                     self.number = self.env['ir.sequence'].get('invoice_local')
#                 else:
#                     if not self.partner_id.cust_code:
#                         if self.type=="out_invoice":
#                             raise except_orm(_('Error!'), _('Please Enter Customer code'))
#                     cust_code = str(self.partner_id.cust_code) + '/'
#                     prefix = cust_code[:3].upper()
#                     cr.execute("select id from ir_sequence where name = %s",('Customer Invoice Export',))
#                     res=cr.fetchone()
#                     if res:
#                         cr.execute("update ir_sequence set prefix = %s where id=%s",(cust_code,res[0]))
#                         seq_id = self.env['ir.sequence'].next_by_id(res[0])
#                         self.number = seq_id
#             if self.type=='in_invoice':
#                 self.number = self.env['ir.sequence'].get('sup_inv')
        for inv in self:
            inv.prepare_order_line()
        return self.write({'state': 'open'})

    @api.multi
    def unlink(self):
        for invoice in self:
            if invoice.state not in ('draft', 'cancel'):
                raise Warning(_('You cannot delete an invoice which is not draft or cancelled. You should refund it instead.'))
            elif invoice.internal_number and invoice.state != 'draft':
                raise Warning(_('You cannot delete an invoice after it has been validated (and received a number).  You can set it back to "Draft" state and modify its content, then re-confirm it.'))
        return True

    @api.model
    def create(self, vals):
        """
        This method create invoice number and update zero rated tax
        ------------------------------------------------------
        @param self : object pointer
        @param vals : A dictionary containing keys and values
        """
        account_tax_pool = self.env['account.tax']
        zero_per_tax = account_tax_pool.search([('description', '=', '0% ZR')])

        zero_zp_tax = account_tax_pool.search([('description', '=', '0% ZP')])
        if vals.get('export') == True and self._context.get('type', False) == 'out_invoice':
            for line in vals.get('invoice_line'):
                if line and line[2]:
                    if zero_per_tax:
                        line[2]['invoice_line_tax_id'][0] = [6, False, zero_per_tax.ids]
        if vals.get('export') and self._context.get('type', False) == 'in_invoice':
            for line in vals.get('invoice_line'):
                if line and line[2]:
                    if zero_zp_tax:
                        line[2]['invoice_line_tax_id'][0] = [6, False, zero_zp_tax.ids]
        inv = super(account_invoice, self).create(vals)
        inv.button_reset_taxes()
        if inv.partner_id:
            if inv.type == 'out_invoice':
                if inv.export == False:
                    seq = self.env['ir.sequence'].get('invoice_local')
                    inv.number = seq
                    inv.internal_number = seq
                else:
                    if not inv.partner_id.cust_code:
                        if inv.type == "out_invoice":
                            raise except_orm(_('Error!'), _('Please Enter Customer code'))
                    cust_code = str(inv.partner_id.cust_code) + '/'
                    prefix = cust_code[:3].upper()
                    self._cr.execute("select id from ir_sequence where name = %s", ('Customer Invoice Export',))
                    res = self._cr.fetchone()
                    if res:
                        self._cr.execute("update ir_sequence set prefix = %s where id=%s", (cust_code, res[0]))
                        seq_id = self.env['ir.sequence'].next_by_id(res[0])
                        inv.number = seq_id
                        inv.internal_number = seq_id
        if inv.type == 'in_invoice':
            seq_inv = self.env['ir.sequence'].get('sup_inv')
            inv.number = seq_inv
            inv.internal_number = seq_inv
        return inv

    def update_sequnce(self):
        latest_number=''
        for inv in self:
            if inv.type=='out_invoice' and inv.sequence_update == False:
                if inv.number:
                    invoice_id = self.search([('internal_number', '=', inv.number)])
                    if inv.id == invoice_id.id:
                        self._cr.execute("select id from ir_sequence where name = %s", ('Account Invoice Local',))
                        loc_res = self._cr.fetchone()      
                        if loc_res:          
                            self._cr.execute("update ir_sequence set number_next = %s where id=%s", (inv.number, loc_res[0])) 
                    if inv.export == False:
                        self._cr.execute("select id from ir_sequence where name = %s", ('Customer Invoice Export',))
                        res1 = self._cr.fetchone()    
                        seq_id1 = self.env['ir.sequence'].next_by_id(res1[0])                    
                        inv.number = seq_id1
                        inv.internal_number = seq_id1
                        latest_number = seq_id1
                    else:                               
                        if not inv.partner_id.cust_code:
                            if inv.type == "out_invoice":
                                raise except_orm(_('Error!'), _('Please Enter Customer code'))
                        cust_code = str(inv.partner_id.cust_code) + '/'
                        prefix = cust_code[:3].upper()
                        self._cr.execute("select id from ir_sequence where name = %s", ('Customer Invoice Export',))
                        res = self._cr.fetchone()
                        if res:
                            self._cr.execute("update ir_sequence set prefix = %s where id=%s", (cust_code, res[0]))
                            seq_id = self.env['ir.sequence'].next_by_id(res[0])
                            latest_number = seq_id   
        return latest_number
    
    @api.multi
    def write(self, vals):
        picking_obj = self.env['stock.picking']
        sale_obj = self.env['sale.order']
        sale_l_obj = self.env['sale.order.line']
        purchase_obj = self.env['purchase.order']
        purchase_l_obj = self.env['purchase.order.line']
        invoice_l_obj = self.env['account.invoice.line']
        pick_line_obj = self.env['stock.move']
        stock_quant_obj = self.env['stock.quant']
        if vals.get('export', False) == True:
            for inv in self:
                if inv.sequence_update == False and inv.type == 'out_invoice':
                    num = self.update_sequnce()
                    vals.update({'number': num, 'internal_number': num, 'sequence_update': True})
        res = super(account_invoice, self).write(vals)
        for inv in self:
            if inv.state not in ('draft', 'cancel'):
                sale_ord_id = sale_obj.search([('inv_id', '=', inv.id)])
                purch_ord_id = purchase_obj.search([('inv_id', '=', inv.id)])
                pick_ord_id = picking_obj.search([('inv_id', '=', inv.id)])
                sale_ord_vals = {}
                purchase_ord_vals = {}
                picking_ord_vals = {}
                if vals.get('date_invoice', False):
                    sale_ord_vals.update({'date_order': vals['date_invoice']})
                    purchase_ord_vals.update({'date_order': vals['date_invoice']})
                    picking_ord_vals.update({'min_date': vals['date_invoice']})
                if vals.get('partner_id', False):
                    sale_ord_vals.update({'partner_id': vals['partner_id']})
                    purchase_ord_vals.update({'partner_id': vals['partner_id']})
                    picking_ord_vals.update({'partner_id': vals['partner_id']})
                if vals.get('part_inv_id', False):
                    sale_ord_vals.update({'partner_invoice_id': vals['part_inv_id']})
                    purchase_ord_vals.update({'partner_invoice_id': vals['part_inv_id']})
                if vals.get('part_ship_id', False):
                    sale_ord_vals.update({'partner_shipping_id': vals['part_ship_id']})
                    purchase_ord_vals.update({'partner_shipping_id': vals['part_ship_id']})
                if vals.get('attn_inv', False):
                    sale_ord_vals.update({'attn_sal': vals['attn_inv']})
                    purchase_ord_vals.update({'attn_pur': vals['attn_inv']})
                if vals.get('landed_cost', False):
                    sale_ord_vals.update({'landed_cost_sal': [(6, 0, inv.landed_cost.ids)]})
                    purchase_ord_vals.update({'landed_cost_pur': [(6, 0, inv.landed_cost.ids)]})
                if vals.get('currency_rate', False):
                    sale_ord_vals.update({'currency_rate': vals['currency_rate']})
                    purchase_ord_vals.update({'currency_rate': vals['currency_rate']})
                if vals.get('customer_po', False):
                    sale_ord_vals.update({'customer_po': vals['customer_po']})

                if vals.get('invoice_line', False):
                    sale_order_l_lst = []
                    for inv_line in vals['invoice_line']:
                        if inv_line[1] and inv_line[2]:
                            s_lines_vals = {}
                            p_lines_vals = {}
                            pick_lines_vals = {}
                            if inv_line[2].get('price_unit', False):
                                s_lines_vals.update({'price_unit': inv_line[2]['price_unit'] or 0.0})
                                p_lines_vals.update({'price_unit': inv_line[2]['price_unit'] or 0.0})
                                pick_lines_vals.update({'price_unit': inv_line[2]['price_unit'] or 0.0})
                            if inv_line[2].get('product_id', False):
                                s_lines_vals.update({'product_id': inv_line[2]['product_id'] or False})
                                p_lines_vals.update({'product_id': inv_line[2]['product_id'] or False})
                                pick_lines_vals.update({'price_unit': inv_line[2]['product_id'] or 0.0})
                            if inv_line[2].get('quantity', False):
                                s_lines_vals.update({'product_uom_qty': inv_line[2]['quantity'] or 0.0})
                                p_lines_vals.update({'product_qty': inv_line[2]['quantity'] or 0.0})
                                pick_lines_vals.update({'product_uom_qty': inv_line[2]['quantity'] or 0.0})
                            if inv_line[2].get('name', False):
                                s_lines_vals.update({'name': inv_line[2]['name'] or ''})
                                p_lines_vals.update({'name': inv_line[2]['name'] or ''})
                                pick_lines_vals.update({'price_unit': inv_line[2]['name'] or 0.0})
                            if inv_line[2].get('invoice_line_tax_id', False):
                                if inv_line[2]['invoice_line_tax_id'][0] and inv_line[2]['invoice_line_tax_id'][0][2]:
                                    s_lines_vals.update({'tax_id': [(6, 0, inv_line[2]['invoice_line_tax_id'][0][2])]})
                                    p_lines_vals.update({'taxes_id': [(6, 0, inv_line[2]['invoice_line_tax_id'][0][2])]})
                                    p_lines_vals.update({'price_unit': inv_line[2]['price_unit'] or 0.0})
                            if s_lines_vals and sale_ord_id:
                                sale_line_id = sale_l_obj.search([('inv_line_id', '=', inv_line[1])])
                                if sale_line_id:
                                    sale_line_id.write(s_lines_vals)
                            if p_lines_vals and purch_ord_id:
                                p_lines_vals.update({'date_planned': inv.date_invoice or False})
                                purch_line_id = purchase_l_obj.search([('inv_line_id', '=', inv_line[1])])
                                if purch_line_id:
                                    purch_line_id.write(p_lines_vals)
                            if inv.type == 'out_invoice':
                                if pick_lines_vals and pick_ord_id:
                                    inv_line_rec = invoice_l_obj.browse(inv_line[1])
                                    pick_line_ids = pick_line_obj.search([('inv_line_id', '=', inv_line[1])])
                                    if pick_line_ids:
                                        for pick_line_id in pick_line_ids:
                                                pick_line_id.write(pick_lines_vals)
                                                self._cr.execute('select quant_id from stock_quant_move_rel  where move_id=%s', (pick_line_id.id,))
                                                quant_id = self._cr.fetchone()
                                                quat_data = stock_quant_obj.browse(quant_id)
                                                new_qnt = stock_quant_obj.create({'product_id': inv_line_rec.product_id.id,
                                                                        'qty': quat_data.qty - pick_lines_vals.get('product_uom_qty', 0.0),
                                                                        'in_date': inv_line_rec.invoice_id and inv_line_rec.invoice_id.date_invoice,
                                                                        'location_id': pick_line_id.location_id.id})
                                                quat_data.write({'qty': pick_lines_vals.get('product_uom_qty')})
                            else:
                                inv_line_rec = invoice_l_obj.browse(inv_line[1])
                                pick_det_line_id = pick_line_obj.search([('inv_line_id', '=', inv_line[1])])
#                                 pick_det_line_id = pick_line_obj.search([('purchase_line_id', '=', pur_line_id_new.id)])
#                                 pur_line_id_new = purchase_l_obj.search([('inv_line_id', '=', inv_line[1])])
                                diff = 0
                                if pick_det_line_id:
                                    pick_det_line_id.write(pick_lines_vals)
                                    for pick_det_line_data in pick_det_line_id:
                                        self._cr.execute('select quant_id from stock_quant_move_rel  where move_id=%s', (pick_det_line_data.id,))
                                        quant_id = self._cr.fetchone()
                                        quat_data = stock_quant_obj.browse(quant_id)
                                        if quat_data.qty - pick_lines_vals.get('product_uom_qty', 0) > 0:
                                            diff = -quat_data.qty - pick_lines_vals.get('product_uom_qty', 0)
                                        else:
                                            diff = quat_data.qty - pick_lines_vals.get('product_uom_qty', 0)
                                        stock_quant_obj.create({'product_id': inv_line_rec.product_id.id,
                                                                'qty':-(quat_data.qty - pick_lines_vals.get('product_uom_qty', 0)),
                                                                'in_date': inv_line_rec.invoice_id and inv_line_rec.invoice_id.date_invoice,
                                                                'location_id': pick_det_line_data.location_id.id})
                                        quat_data.write({'qty': pick_lines_vals.get('product_uom_qty')})

                        if inv_line[2] and not inv_line[1]:
                            s_lines_vals = {}
                            p_lines_vals = {}
                            pick_lines_vals = {}
                            if inv_line[2].get('price_unit', False):
                                s_lines_vals.update({'price_unit': inv_line[2]['price_unit'] or 0.0})
                                p_lines_vals.update({'price_unit': inv_line[2]['price_unit'] or 0.0})
                                pick_lines_vals.update({'price_unit': inv_line[2]['price_unit'] or 0.0})
                            if inv_line[2].get('product_id', False):
                                s_lines_vals.update({'product_id': inv_line[2]['product_id'] or False})
                                p_lines_vals.update({'product_id': inv_line[2]['product_id'] or False})
                                pick_lines_vals.update({'product_id': inv_line[2]['product_id'] or False})
                            if inv_line[2].get('quantity', False):
                                s_lines_vals.update({'product_uom_qty': inv_line[2]['quantity'] or 0.0})
                                p_lines_vals.update({'product_qty': inv_line[2]['quantity'] or 0.0})
                                pick_lines_vals.update({'product_uom_qty': inv_line[2]['quantity'] or 0.0})
                            if inv_line[2].get('name', False):
                                s_lines_vals.update({'name': inv_line[2]['name'] or ''})
                                p_lines_vals.update({'name': inv_line[2]['name'] or ''})
                                pick_lines_vals.update({'product_uom_qty': inv_line[2]['quantity'] or 0.0})
                            if inv_line[2].get('invoice_line_tax_id', False):
                                if inv_line[2]['invoice_line_tax_id'][0] and inv_line[2]['invoice_line_tax_id'][0][2]:
                                    s_lines_vals.update({'tax_id': [(6, 0, inv_line[2]['invoice_line_tax_id'][0][2])]})
                                    p_lines_vals.update({'taxes_id': [(6, 0, inv_line[2]['invoice_line_tax_id'][0][2])]})
                            if s_lines_vals and sale_ord_id:
                                inv_l_id = invoice_l_obj.search([('name', '=', s_lines_vals.get('name', '')),
                                                      ('product_id', '=', s_lines_vals.get('product_id', False)),
                                                      ('price_unit', '=', s_lines_vals.get('price_unit', 0.0)),
                                                      ('quantity', '=', s_lines_vals.get('product_uom_qty', 0.0)),
                                                      ('invoice_id', '=', inv.id or False)])
                                if inv_l_id:
                                    s_lines_vals.update({'inv_line_id': inv_l_id.ids[0] or False})
                                
                                if sale_ord_vals.get('order_line', False):
                                    sale_ord_vals['order_line'].append((0, 0, s_lines_vals))
                                else:
                                    sale_ord_vals.update({'order_line': [(0, 0, s_lines_vals)]})
                            if p_lines_vals and purch_ord_id:
                                p_lines_vals.update({'date_planned': inv.date_invoice or False})
                                inv_l_id = invoice_l_obj.search([('name', '=', p_lines_vals.get('name', '')),
                                                      ('product_id', '=', p_lines_vals.get('product_id', False)),
                                                      ('price_unit', '=', p_lines_vals.get('price_unit', 0.0)),
                                                      ('quantity', '=', p_lines_vals.get('product_qty', 0.0)),
                                                      ('invoice_id', '=', inv.id or False)])
                                if inv_l_id:
                                    p_lines_vals.update({'inv_line_id': inv_l_id.ids[0] or False})
#                                 purchase_ord_vals.update({'order_line': [(0, 0, p_lines_vals)]})
                                if purchase_ord_vals.get('order_line', False):
                                    purchase_ord_vals['order_line'].append((0, 0, p_lines_vals))
                                else:
                                    purchase_ord_vals.update({'order_line': [(0, 0, p_lines_vals)]})
                            if pick_lines_vals and pick_ord_id:
                                pick_lines_vals.update({'state': 'assigned'})
                                inv_l_id = invoice_l_obj.search([('product_id', '=', pick_lines_vals.get('product_id', False)),
                                                      ('price_unit', '=', pick_lines_vals.get('price_unit', 0.0)),
                                                      ('quantity', '=', pick_lines_vals.get('product_uom_qty', 0.0)),
                                                      ('invoice_id', '=', inv.id or False)])
                                if inv_l_id:
                                    pick_lines_vals.update({'inv_line_id': inv_l_id.ids[0] or False,
                                                            'product_uom': inv_l_id.product_id and \
                                                                inv_l_id.product_id.uom_id and \
                                                                inv_l_id.product_id.uom_id.id or False,
                                                            'name': inv_l_id.name or ''})
                                    if inv_l_id.invoice_id and inv_l_id.invoice_id.type == 'out_invoice':
                                        loc_id = self.env['stock.location'].search([('location_id', '!=', False), ('location_id.name', 'ilike', 'WH'),
                                                                                    ('company_id.id', '=', self.company_id.id),
                                                                                    ('usage', '=', 'internal')], limit = 1)
                                        dest_loc_id = self.env['stock.location'].search([('location_id', '!=', False),
                                                             ('location_id.name', 'ilike', 'Partner Locations'),
                                                             ('usage', '=', 'customer')], limit = 1)
                                        pick_lines_vals.update({'location_id': loc_id and loc_id.id or False,
                                                                'location_dest_id': dest_loc_id and dest_loc_id.id or False})
                                    if inv_l_id.invoice_id and inv_l_id.invoice_id.type == 'in_invoice':
                                        loc_id = self.env['stock.location'].search([('location_id', '!=', False), ('location_id.name', 'ilike', 'WH'),
                                                                                    ('company_id.id', '=', self.company_id.id),
                                                                                    ('usage', '=', 'internal')], limit = 1)
                                        dest_loc_id = self.env['stock.location'].search([('location_id', '!=', False),
                                                             ('location_id.name', 'ilike', 'Partner Locations'),
                                                             ('usage', '=', 'supplier')], limit = 1)
                                        pick_lines_vals.update({'location_id': dest_loc_id and dest_loc_id.id or False,
                                                                'location_dest_id': loc_id and loc_id.id or False})
                                if picking_ord_vals.get('move_lines', False):
                                    picking_ord_vals['move_lines'].append((0, 0, pick_lines_vals))
                                else:
                                    picking_ord_vals.update({'move_lines': [(0, 0, pick_lines_vals)]})
                if sale_ord_id and sale_ord_vals:
                    sale_ord_id.write(sale_ord_vals)
                if purch_ord_id and purchase_ord_vals:
                    purch_ord_id.write(purchase_ord_vals)
                if pick_ord_id and picking_ord_vals:
                    pick_ord_id.write(picking_ord_vals)
                    for pick in pick_ord_id:
                        if pick.state == 'assigned':
                            pick.do_transfer()
        return res

    @api.multi
    def action_cancel(self):
        """
        This method cancel created picking and generate return
        order and cancel saled order created from invoice
        ------------------------------------------------------
        @param self : object pointer
        """
        moves = self.env['account.move']
        quant_obj = self.env["stock.quant"]
        uom_obj = self.env['product.uom']
        sale_rec = ''
        purchase_rec = ''
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
        picking_rec = self.env['stock.picking'].search([('inv_id', '=', self.ids[0])])
        if picking_rec:
            return_line = []
            for pick in picking_rec:
                if not self.direct_shipemt:
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
            if self.type == "out_invoice":
                sale_rec = self.env['sale.order'].search([('inv_id', '=', self.ids[0])])
            if self.type == "in_invoice":
                purchase_rec = self.env['purchase.order'].search([('inv_id', '=', self.ids[0])])
            if sale_rec:
                sale_rec.action_invoice_cancel()
                sale_rec.write({'state': 'cancel'})
            if purchase_rec:
                purchase_rec.write({'state':'except_invoice'})
        return True

class account_move(models.Model):
     _inherit = "account.move"

     @api.model
     def create(self, vals):
         if self._context and self._context.get('invoice', False):
             vals['name'] = self._context['invoice'].number or '/'
         res = super(account_move, self).create(vals)
         return res

#     @api.multi
#     def post(self):
#         cr,uid,context = self.env.args
#         if context is None:
#             context = {}
#         invoice = context.get('invoice', False)
#         valid_moves = self.with_context(context=context).validate()
#
#         if not valid_moves:
#             raise osv.except_osv(_('Error!'), _('You cannot validate a non-balanced entry.\nMake sure you have configured payment terms properly.\nThe latest payment term line should be of the "Balance" type.'))
#         obj_sequence = self.pool.get('ir.sequence')
#         for move in self.browse(valid_moves):
#             if move.name =='/':
#                 new_name = False
#                 journal = move.journal_id
#
#                 if invoice and invoice.internal_number:
#                     new_name = invoice.internal_number
#                 else:
#                     if journal.sequence_id:
#                         c = {'fiscalyear_id': move.period_id.fiscalyear_id.id}
#                         new_name = obj_sequence.next_by_id(cr, uid, journal.sequence_id.id, c)
#                     else:
#                         raise osv.except_osv(_('Error!'), _('Please define a sequence on the journal.'))
#
#                 if new_name:
#                     move.name = new_name
#
#         cr.execute('UPDATE account_move '\
#                    'SET state=%s '\
#                    'WHERE id IN %s',
#                    ('posted', tuple(valid_moves),))
#         self.with_context(context=context).invalidate_cache(['state', ], valid_moves)
#         return True


class res_partner(models.Model):
    _inherit = 'res.partner'

    cust_code = fields.Char('Code')
    bank_detail = fields.Text(string = 'Bank Description')

    @api.multi
    def name_get(self):
        result = []
        for rec in self:
            name = ''
            if rec.name:
                name += rec.name

            result.append((rec.id, name))
        return result

#     _sql_constraints = [
#         ('cust_code_unique', 'unique(cust_code)', 'Please Enter Unique Customer Code.'),
#     ]

    @api.v7
    def _check_cust_code_unique(self, cr, uid, ids, context = None):
        for partner in self.browse(cr, uid, ids, context = context):
            if partner.customer == True and partner.cust_code:
                partners = self.search(cr, uid, [('cust_code', '=', partner.cust_code),
                                                 ('customer', '=', True)])
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
    _name = 'landed.cost.invoice'
    _rec_name = 'landed_id'

    acc_inv_id = fields.Many2one('account.invoice', 'Invoice')
    landed_id = fields.Many2one('landed.cost', 'Name')
    amount = fields.Float('Amount')
    acc_sal_id = fields.Many2one('sale.order', 'Sale Order')
    acc_pur_id = fields.Many2one('purchase.order', 'Sale Order')

    @api.onchange('landed_id')
    def onchange_landed_id(self):
        for rec in self:
            rec.amount = rec.landed_id.amount


class landed_cost(models.Model):
    _name = 'landed.cost'

    name = fields.Char('Name')
    amount = fields.Float('Amount')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
