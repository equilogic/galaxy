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

from openerp import api, fields, models, _

class wiz_galaxy_add_prod_in_invoice(models.TransientModel):
    _name = 'wiz.galaxy.add.prod.in.invoice'

    product_ids = fields.Many2many('product.product','product_wiz_account_rel', 'wiz_inv_id', 'product_id', 'Products')

    #Add products in the invoice
    @api.multi
    def products_add_in_so(self):
        cr, uid, context = self.env.args
        order_line_list = []
        so_line ={}
        tax_ids =[]
        account_tax_pool = self.env['account.tax']
        invoice_rec = self.env['account.invoice'].browse(context.get('active_ids'))
        if invoice_rec:
            tx_per_tax = account_tax_pool.search([('description', '=', '7% TX7')])
            sr_per_tax = account_tax_pool.search([('description', '=', '7% SR')])
            zero_per_tax = account_tax_pool.search([('description', '=', '0% ZR')])
            zero_zp_tax = account_tax_pool.search([('description', '=', '0% ZP')])
            if invoice_rec.export == True and invoice_rec.type  == 'out_invoice':
                tax_ids = zero_per_tax.ids
            elif invoice_rec.type  == 'out_invoice':
                tax_ids = sr_per_tax.ids
            if invoice_rec.export == True and invoice_rec.type == 'in_invoice':
                tax_ids = zero_zp_tax.ids   
            elif invoice_rec.type == 'in_invoice':
                tax_ids= tx_per_tax.ids 
            for product_rec in self.product_ids:
                name = product_rec.with_context({'partner_id': invoice_rec.partner_id.id}).name_get()[0][1]
                if product_rec.description_sale:
                    name += '\n' + product_rec.description_sale
                so_line = {'product_id': product_rec.id,
                           'name': name, 'price_unit': product_rec.list_price,
                           'quantity': 1.0,
                           'invoice_line_tax_id': [(6, 0, tax_ids)]
                           }
                order_line_list.append((0, 0, so_line))
                print "order_line_list===========",order_line_list
            invoice_rec.write({'invoice_line': order_line_list})
        return True
