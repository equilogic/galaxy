# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Serpent Consulting Services Pvt. Ltd.
#    Copyright (C) 2015 OpenERP SA (<http://www.serpentcs.com>)
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

import base64
import tempfile
import xlrd
from xlrd import open_workbook

from openerp import models, fields, api, _
from openerp.exceptions import Warning
from openerp.tools import misc, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT,ustr
from datetime import datetime


class wiz_account_invoice_import(models.TransientModel):
    _name = 'wiz.account.invoice.import'

    xls_file = fields.Binary('XLS File')
    datas_fname = fields.Char('File Name')

    @api.multi
    def convert_date(self, dt, wb):
        txs_date = False
        if isinstance(dt, (str, unicode)):
            txs_date = datetime.strptime(dt, '%m/%d/%Y')
        elif isinstance(dt, (str, float)):
             dt = datetime(* (xlrd.xldate_as_tuple(dt, wb.datemode))).strftime('%d/%m/%Y')
             txs_date = datetime.strptime(dt, '%d/%m/%Y')
        return txs_date

    @api.multi
    def import_invoices(self):
        """
        This Method will Create Invoices. 
        """
        cr, uid, context = self.env.args
        partner_obj = self.env['res.partner']
        curr_obj = self.env['res.currency']
        product_obj = self.env['product.product']
        inv_obj = self.env['account.invoice']
        inv_line_obj = self.env['account.invoice.line']
        for rec in self:
            datafile = rec.xls_file
            file_name = str(rec.datas_fname)
            # Checking for Suitable File
            if not datafile or not file_name.lower().endswith(('.xls', '.xlsx',)):
                raise Warning(_("Please Select an .xls or its compatible file to Import"))
            xls_data = base64.decodestring(datafile)
            temp_path = tempfile.gettempdir()
            # writing a file to temp. location
            fp = open(temp_path + '/xsl_file.xls', 'wb+')
            fp.write(xls_data)
            fp.close()
            # opening a file form temp. location
            wb = open_workbook(temp_path + '/xsl_file.xls')
            header_list = []
            data_list = []
            for sheet in wb.sheets():
                for rownum in range(sheet.nrows):
                    # Preparing headers
                    if rownum == 0:
                        header_list = [x.strip().encode('UTF8') for x in sheet.row_values(rownum)]
                        fixed_list = ['Partner', 'Invoice Address', 'Delivery Address', 'Account',
                                      'Currency', 'Invoice Date', 'Supplier Invoice Number', 'Ship Via',
                                      'Invoice Lines / Product', 'Invoice Lines / Description', 'Invoice Lines / Quantity',
                                      'Invoice Lines / Unit Price', 'Invoice Lines / Discount (%)',
                                      'Invoice Lines / Taxes', 'Additional Information', 'Currency rate',
                                      'Delivery Status', 'Export']
                        for column in fixed_list:
                            if column not in header_list:
                                raise Warning(_("Column Named = '%s' Not Found in Uploaded File." \
                                                "\n Please Upload The File Having At least Columns like :- %s" \
                                                 % (column, fixed_list)))
                        headers_dict = {
                                    'partner'               : header_list.index('Partner'),
                                    'inv_add'               : header_list.index('Invoice Address'),
                                    'delivery_add'          : header_list.index('Delivery Address'),
                                    'account'               : header_list.index('Account'),
                                    'currency'              : header_list.index('Currency'),
                                    'inv_date'              : header_list.index('Invoice Date'),
                                    'ship_via'              : header_list.index('Ship Via'),
                                    'supp_inv_no'           : header_list.index('Supplier Invoice Number'),
                                    'inv_line_product'      : header_list.index('Invoice Lines / Product'),
                                    'inv_line_description'  : header_list.index('Invoice Lines / Description'),
                                    'inv_line_quantity'     : header_list.index('Invoice Lines / Quantity'),
                                    'inv_line_unit_price'   : header_list.index('Invoice Lines / Unit Price'),
                                    'inv_line_discount'     : header_list.index('Invoice Lines / Discount (%)'),
                                    'inv_line_tax'          : header_list.index('Invoice Lines / Taxes'),
                                    'additional_info'       : header_list.index('Additional Information'),
                                    'currency_rate'         : header_list.index('Currency rate'),
                                    'deli_status'           : header_list.index('Delivery Status'),
                                    'export'                : header_list.index('Export')
                                }
                    # rows data
                    if rownum >= 1:
                        data_list.append(sheet.row_values(rownum))
            if data_list and headers_dict:
                inv_id = False
                inv_ids_lst = []
                for row in data_list:
                    partner = row[headers_dict['partner']]
                    inv_add = row[headers_dict['inv_add']]
                    delivery_add = row[headers_dict['delivery_add']]
                    account = row[headers_dict['account']]
                    currency = row[headers_dict['currency']]
                    inv_date = row[headers_dict['inv_date']]
                    ship_via = row[headers_dict['ship_via']]
                    supp_inv_no = row[headers_dict['supp_inv_no']]
                    inv_line_product = row[headers_dict['inv_line_product']]
                    inv_line_description = row[headers_dict['inv_line_description']]
                    inv_line_quantity = row[headers_dict['inv_line_quantity']]
                    inv_line_unit_price = row[headers_dict['inv_line_unit_price']]
                    inv_line_discount = row[headers_dict['inv_line_discount']]
                    inv_line_tax = row[headers_dict['inv_line_tax']]
                    additional_info = row[headers_dict['additional_info']]
                    currency_rate = row[headers_dict['currency_rate']]
                    deli_status = row[headers_dict['deli_status']]
                    export = row[headers_dict['export']]
                    part_rec = inv_add_rec = delivery_add_rec = currency_rec = prod_rec = False
                    if partner:
                        part_rec = partner_obj.search([('name', '=', partner)], limit=1)
                    if inv_add:
                        inv_add_rec = partner_obj.search([('name', '=', inv_add)], limit=1)
                    if delivery_add:
                        delivery_add_rec = partner_obj.search([('name', '=', inv_add)], limit=1)
                    if currency:
                        currency_rec = curr_obj.search([('name', '=', currency)], limit=1)
                    if inv_line_product:
                        prod_rec = product_obj.search([('default_code', '=', inv_line_product)], limit=1)
                    tax_lst = []
                    if inv_line_tax:
                        inv_line_tax_split = inv_line_tax.split(',')
                        for tax in inv_line_tax_split:
                            tax_id = self.env['account.tax'].search([('type_tax_use','=','purchase'),
                                         ('description', '=', tax)], limit=1)
                            if tax_id:
                                tax_lst.append(tax_id.id)
                    if partner:
                        account = part_rec and part_rec.property_account_payable and \
                                        part_rec.property_account_payable.id or False
                        inv_id = inv_obj.create({'partner_id': part_rec and part_rec.id or False,
                                    'part_inv_id': inv_add_rec and inv_add_rec.id or False,
                                    'part_ship_id': delivery_add_rec and delivery_add_rec.id or False,
                                    'currency_id': currency_rec.id or False,
                                    'currency_rate': currency_rate or 0.000,
                                    'account_id': account,
    #                                 'discount_rate': inv_line_discount or 0.0,
                                    'date_invoice': inv_date and self.convert_date(inv_date, wb) or datetime.now().date(),
                                    'supplier_invoice_number': supp_inv_no or '',
                                    'comment': additional_info or '',
                                    'type': 'in_invoice'
                                    })
                        inv_ids_lst.append(inv_id)
                    inv_line_id = inv_line_obj.create({
                                     'product_id': prod_rec and prod_rec.id or False,
                                     'name': inv_line_description or '',
                                     'prod_desc': inv_line_description or '',
                                     'quantity': inv_line_quantity or 0.0,
                                     'price_unit': inv_line_unit_price or 0.0,
                                     'invoice_id': inv_id and inv_id.id or False,
                                     'invoice_line_tax_id': [(6,0,tax_lst)],
                                     'uos_id': prod_rec and prod_rec.uom_id and \
                                                    prod_rec.uom_id.id or False
                                     })
                for inv in inv_ids_lst:
                    inv.signal_workflow('invoice_open')
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: