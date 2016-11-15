import xlrd
import base64
import tempfile
from xlrd import open_workbook
from openerp.tools import ustr
from openerp.exceptions import Warning
from openerp import fields, models, api, _


class wiz_import_products(models.TransientModel):
    _name = "wiz.import.products"

    file = fields.Binary('File')
    name = fields.Char(string='File Name', size=64)
    
    @api.multi
    def import_products(self):
        prod_obj = self.env['product.product']
        for wiz_rec in self:
            datafile = wiz_rec.file
            if not datafile:
                raise Warning(_("Please select (.xls or .xlsx) extension"
                                " file to import Products."))
            file_name = wiz_rec.name and str(wiz_rec.name) or ''
            if file_name.lower().endswith('.xls') or file_name.lower().endswith('.xlsx'):
                xls_data = base64.decodestring(datafile)
                temp_path = tempfile.gettempdir()
                fp = open(temp_path + '/xls_file.xls', 'wb+')
                fp.write(xls_data)
                fp.close()
                wb = open_workbook(temp_path + '/xls_file.xls')
                for sheet in wb.sheets():
                    header_list = []
                    for rownum in range(sheet.nrows):
                        if rownum == 0:
                            # Converting unicode chars. into string and list all the header
                            header_list = [x.strip().encode('UTF8') \
                                    for x in sheet.row_values(rownum)]
                        if header_list and rownum > 0:
                            record_data_l = [x for x in \
                                            sheet.row_values(rownum)]
                            final_product_dict = dict(zip(header_list, record_data_l))
                            if record_data_l and final_product_dict:
                                product_vals = {}
                                products = []
                                for header_l in header_list:
                                    rec_value = final_product_dict.get(header_l, False) or False
                                    if header_l == 'Item Name':
                                        product_vals.update({'name': rec_value or ''})
                                    elif header_l == 'Internal Reference':
                                        if rec_value:
                                            products = prod_obj.search([('default_code', '=', ustr(rec_value))])
                                        product_vals.update({'default_code': rec_value or ''})
                                    elif header_l == 'Sale Price':
                                        product_vals.update({'list_price': rec_value or 0.0})
                                    elif header_l == 'Cost Price':
                                        product_vals.update({'standard_price': rec_value or 0.0})
                                if product_vals and products:
                                    products.write(product_vals)
                                if product_vals and not products:
                                    prod_obj.create(product_vals)
            else:
                raise Warning(_("Please select (.xls or .xlsx) extension"
                                " file to import Products."))
        return True