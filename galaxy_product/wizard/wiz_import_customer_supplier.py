import xlrd
import base64
import tempfile
from xlrd import open_workbook
from openerp.tools import ustr
from openerp.exceptions import Warning
from openerp import fields, models, api, _


class wiz_import_cust_supp(models.TransientModel):
    _name = "wiz.import.cust.supp"

    file = fields.Binary('File')
    name = fields.Char(string='File Name', size=64)
#     import_type = fields.Selection([
#                                 ('import_customers', 'Import Customers.'),
#                                 ('import_suppliers', 'Import Suppliers.')],
#                                default="import_customers", string="Import Type")
    @api.multi
    def import_customers_suppliers(self):
        partner_obj = self.env['res.partner']
        state_obj = self.env['res.country.state']
        country_obj = self.env['res.country']
        title_obj = self.env['res.partner.title']
        user_obj = self.env['res.users']
        for wiz_rec in self:
            datafile = wiz_rec.file
            if not datafile:
                raise Warning(_("Please select (.xls or .xlsx) extension"
                                " file to import."))
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
                            final_data_dict = dict(zip(header_list, record_data_l))
                            if record_data_l and final_data_dict:
                                partner_vals = {}
                                for header_l in final_data_dict:
                                    rec_value = final_data_dict.get(header_l, False) or False
                                    if header_l == 'Name':
                                        partner_vals.update({'name': rec_value or ''})
                                    elif header_l == 'Last Name':
                                        partner_vals.update({'last_name': rec_value or ''})
                                    elif header_l == 'Customer':
                                        cust = False
                                        if rec_value:
                                            cust = True
                                        partner_vals.update({'customer': cust})
                                    elif header_l == 'Supplier':
                                        supp = False
                                        if rec_value:
                                            supp = True
                                        partner_vals.update({'supplier': supp})
                                    if header_l == 'Code':
                                        code = ''
                                        if rec_value:
                                            split_code = str(rec_value).split('.')
                                            if split_code and split_code[1] == '0':
                                                code = split_code and split_code[0]
                                        partner_vals.update({'cust_code': code or ''})
                                    elif header_l == 'Active':
                                        active = False
                                        if rec_value:
                                            active = True
                                        partner_vals.update({'active': active or ''})
                                    elif header_l == 'Street':
                                        partner_vals.update({'street': rec_value or ''})
                                    elif header_l == 'Street2':
                                        partner_vals.update({'street2': rec_value or ''})
                                    elif header_l == 'City':
                                        partner_vals.update({'city': rec_value or ''})
                                    elif header_l == 'State':
                                        states = state_obj.search([('name','=', ustr(rec_value))])
                                        state = False
                                        if states:
                                            state = states.ids[0]
                                        partner_vals.update({'state_id': state})
                                    elif header_l == 'Zip':
                                        zip_code = ''
                                        if rec_value:
                                            split_zip = str(rec_value).split('.')
                                            if split_zip and split_zip[1] == '0':
                                                zip_code = split_zip and split_zip[0]
                                        partner_vals.update({'zip': zip_code})
                                    elif header_l == 'Country':
                                        countrys = country_obj.search([('name','=', ustr(rec_value))])
                                        country = False
                                        if countrys:
                                            country = countrys.ids[0]
                                        partner_vals.update({'country_id': country})
                                    elif header_l == 'Job Position':
                                        partner_vals.update({'function': rec_value or ''})
                                    elif header_l == 'Phone':
                                        partner_vals.update({'phone': rec_value or ''})
                                    elif header_l == 'Mobile':
                                        mobile = ''
                                        if rec_value:
                                            split_mobile = str(rec_value).split('.')
                                            if split_mobile and split_mobile[1] == '0':
                                                mobile = split_mobile and split_mobile[0]
                                        partner_vals.update({'mobile': mobile or ''})
                                    elif header_l == 'Fax':
                                        fax = ''
                                        if rec_value:
                                            split_fax = str(rec_value).split('.')
                                            if split_fax and split_fax[1] == '0':
                                                fax = split_fax and split_fax[0]
                                        partner_vals.update({'fax': fax or ''})
                                    elif header_l == 'Email':
                                        partner_vals.update({'email': rec_value or ''})
                                    elif header_l == 'Title':
                                        titles = title_obj.search([('name','=', ustr(rec_value))])
                                        title = False
                                        if titles:
                                            title = titles.ids[0]
                                        partner_vals.update({'title': title or ''})
                                    elif header_l == 'Customer UEN':
                                        customer_uen = ''
                                        if rec_value:
                                            split_customer_uen = str(rec_value).split('.')
                                            if split_customer_uen and split_customer_uen[1] == '0':
                                                customer_uen = split_customer_uen and split_customer_uen[0]
                                        partner_vals.update({'customer_uen': customer_uen or ''})
                                    elif header_l == 'Customer ID':
                                        partner_vals.update({'customer_id': rec_value})
                                    elif header_l == 'Supplier UEN':
                                        supplier_uen = ''
                                        if rec_value:
                                            split_supplier_uen = str(rec_value).split('.')
                                            if split_supplier_uen and split_supplier_uen[1] == '0':
                                                customer_uen = split_supplier_uen and split_supplier_uen[0]
                                        partner_vals.update({'supplier_uen': supplier_uen or ''})
                                    elif header_l == 'Website':
                                        partner_vals.update({'website': rec_value or ''})
                                    elif header_l == 'Internal Notes':
                                        partner_vals.update({'comment': rec_value or ''})
                                    elif header_l == 'Sales Person':
                                        users = user_obj.search([('name','=', ustr(rec_value))])
                                        user = False
                                        if users:
                                            user = users.ids[0]
                                        partner_vals.update({'user_id': user})
                                    elif header_l == 'Contact Reference':
                                        partner_vals.update({'ref': rec_value or ''})
                                    elif header_l == 'Date':
                                        partner_vals.update({'date': rec_value or ''})
                                if partner_vals:
                                    partner_obj.create(partner_vals)
            else:
                raise Warning(_("Please select (.xls or .xlsx) extension"
                                " file to import."))
        return True