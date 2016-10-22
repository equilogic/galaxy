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

class wiz_galaxy_add_prod_in_so(models.TransientModel):
    _name = 'wiz.galaxy.add.prod.in.so'

    product_ids = fields.Many2many('product.product','product_wiz_sale_rel', 'wiz_pro_id', 'product_id', 'Products')

    #Add products in the sale order
    @api.multi
    def products_add_in_so(self):
        cr, uid, context = self.env.args
        order_line_list = []
        sale_rec = self.env['sale.order'].browse(context.get('active_ids'))
        if sale_rec:
            for product_rec in self.product_ids:
                name = product_rec.with_context({'partner_id': sale_rec.partner_id.id}).name_get()[0][1]
                if product_rec.description_sale:
                    name += '\n' + product_rec.description_sale
                so_line = {'product_id': product_rec.id,
                           'name': name, 'price_unit': product_rec.list_price,
                           'product_qty': 1.0}
                order_line_list.append((0, 0, so_line))
            sale_rec.write({'order_line': order_line_list})
        return True
