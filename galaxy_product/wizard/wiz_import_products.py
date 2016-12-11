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
        prod_obj = self.env['product.template']
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
                                products_ids = []
                                for header_l in header_list:
                                    rec_value = final_product_dict.get(header_l, False) or False
                                    print "rec_value==========",rec_value
                                    if header_l == 'Item Name':
#                                        if rec_value:
#                                            products_ids = prod_obj.search([('name', '=', ustr(rec_value))])
                                        product_vals.update({'name': ustr(rec_value) or ''})
                                    if header_l == 'Full Description':
                                        product_vals.update({'description': ustr(rec_value) or ''})
                                    if header_l == 'Internal Reference':
                                        if rec_value:
                                            products_ids = prod_obj.search([('default_code', '=', ustr(rec_value))])
                                        product_vals.update({'default_code': rec_value or ''})
                                    elif header_l == 'Sale Price':
                                        product_vals.update({'list_price': rec_value or 0.0})
                                    elif header_l == 'Cost Price':
                                        product_vals.update({'standard_price': rec_value or 0.0})
                                    elif header_l == 'Origin':
                                        product_vals.update({'origin_data': rec_value or ''})
                                    elif header_l == 'Brand':
                                        brand_id = self.env['brand.brand'].search([('name','=', ustr(rec_value))])
                                        if not brand_id:
                                            self._cr.execute("insert into brand_brand \
                                            (name) \
                                            values (%s)  RETURNING id \
                                            ", ( ustr(rec_value), ))
                                            brand_rec = self._cr.fetchone()
                                            brd_id = brand_rec and brand_rec[0]
                                            product_vals.update({'brand': brd_id or False})
                                        else:
                                            product_vals.update({'brand': brand_id.id or False})
                                    elif header_l == 'Category':
                                        catg_id = self.env['product.category'].search([('name','=', ustr(rec_value))])
                                        if not catg_id:
                                            self._cr.execute("insert into product_category \
                                                (name,parent_id) \
                                                values (%s, 1)  RETURNING id \
                                                ", ( ustr(rec_value), ))
                                            cat_id = self._cr.fetchone()   
                                            product_vals.update({'categ_id': cat_id and cat_id[0] or False})   
                                        else:                                                     
                                            product_vals.update({'categ_id': catg_id.id or False})                                        
                                product_vals.update({'type': 'product'})                                                                                                                
                                if product_vals and products_ids:
                                    if products_ids:
                                        products_ids.write(product_vals)
                                if product_vals and not products_ids:
                                    prod_obj.create(product_vals)
            else:
                raise Warning(_("Please select (.xls or .xlsx) extension"
                                " file to import Products."))
        return True