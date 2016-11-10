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
import base64
import StringIO
import tempfile
import xlrd
from xlrd import open_workbook
from openerp.exceptions import Warning
from datetime import datetime


class wiz_galaxy_prod_import_xls(models.TransientModel):
    _name = 'wiz.galaxy.prod.import.xls'

    xls_file = fields.Binary('XLS File')
    datas_fname = fields.Char('File Name')

    #Import product data from xls file
    @api.multi
    def import_data_xls(self):
        for rec in self:
            cr, uid, context = self.env.args
            # Objects Creation

            datafile = rec.xls_file
            file_name = str(rec.datas_fname)

            # Checking for Suitable File
            if not datafile or not file_name.lower().endswith(('.xls', '.xlsx',)):
                raise Warning(_("Please Select an .xls or its compatible file to Import Products"))
            # Checking for file type (extension)
            if file_name.lower().endswith(('.xls', '.xlsx',)):
                xls_data = base64.decodestring(datafile)
                temp_path = tempfile.gettempdir()
                fp = open(temp_path + '/xsl_file.xls', 'wb+')
                fp.write(xls_data)
                fp.close()
                wb = open_workbook(temp_path + '/xsl_file.xls')
                for sheet in wb.sheets():
                    header_list = []
                    for rownum in range(sheet.nrows):
                        # headers
                        if rownum == 0:
                            # converting unicode chars. into string
                            header_list = [x.strip().encode('UTF8') for x in sheet.row_values(rownum)]
                        vals = {}
                        product_ids = False
                        if header_list and rownum > 0:
                            record_data_l = [x for x in \
                                            sheet.row_values(rownum)]
                            final_dictionary = dict(zip(header_list, record_data_l))
                            if record_data_l and final_dictionary:
                                for header_l in header_list:
                                    if header_l:
                                        rec_value = final_dictionary.get(header_l, False) or False
                                        same_ref_product = final_dictionary.get('Item Reference', False) or False
                                        product_ids = self.env['product.product'].search([('default_code', '=', same_ref_product)])
#                                         if header_l == 'EAN':
#                                             vals.update({'ean13': rec_value})
                                        if not product_ids:
                                            vals.update({'newly_imp_prod': True})
                                            if header_l == 'Item Reference':
                                                vals.update({'default_code': rec_value or ''})
                                            elif header_l == 'Item Name':
                                                vals.update({'name': rec_value or ''})
                                            elif header_l == 'Brand':
                                                brand = self.env['brand.brand'].search([('name', '=', rec_value)])
                                                if not brand:
                                                    brand = self.env['brand.brand'].create({'name': rec_value})
                                                vals.update({'brand': brand.id or ''})
                                            elif header_l == 'Flavor':
                                                flavor = self.env['flavor.flavor'].search([('name', '=', rec_value)])
                                                if not flavor:
                                                    flavor = self.env['flavor.flavor'].create({'name': rec_value})
                                                vals.update({'flavor': flavor.ids[0] or ''})
                                            elif header_l == 'Price':
                                                vals.update({'list_price': rec_value or ''})
                            if vals:
                                self.env['product.product'].create(vals)
        po_create_wiz_id = self.env['ir.model.data'].get_object_reference('galaxy_purchase', 'wiz_galaxy_create_po_form')[1]
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wiz.galaxy.create.po',
            'views': [(po_create_wiz_id, 'form')],
            'view_id': po_create_wiz_id,
            'target': 'new',
        }


class wiz_galaxy_create_po(models.TransientModel):
    _name = 'wiz.galaxy.create.po'

    supplier_id = fields.Many2one('res.partner', 'Supplier')

    #create po based on newly imported product
    @api.multi
    def create_po(self):
        po_dict = {}
        product_ids = self.env['product.product'].search([('newly_imp_prod', '=', True)])
        po_dict.update({'partner_id': self.supplier_id.id, 'pricelist_id':self.supplier_id.property_product_pricelist_purchase.id,
                        'location_id': self.supplier_id.property_stock_customer.id})
        order_line_list = []
        for product_rec in product_ids:
            name = product_rec.with_context({'partner_id': self.supplier_id.id}).name_get()[0][1]
            if product_rec.description_purchase:
                name += '\n' + product_rec.description_purchase
            purchase_line = {'product_id': product_rec.id,
                             'name': name, 'price_unit': product_rec.standard_price,
                             'date_planned': datetime.now(),
                             'product_qty': 1.0}
            order_line_list.append((0, 0, purchase_line))
            product_rec.write({'newly_imp_prod': False})
        po_dict.update({'order_line': order_line_list})
        self.env['purchase.order'].create(po_dict)
        return True
