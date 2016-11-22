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
        currency_obj = self.env['res.currency']
        pricelist_obj = self.env['product.pricelist']
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
                                contact_ids = []
                                already_exist_partner_flag = False
                                for header_l in final_data_dict:
                                    rec_value = final_data_dict.get(header_l, False) or False
                                    if header_l == 'Name':
                                        already_exist_partner = partner_obj.search([('name','=', ustr(rec_value))])
                                        if already_exist_partner:
                                            already_exist_partner_flag = True
                                        partner_vals.update({'name': rec_value or ''})
                                    elif header_l == 'Last Name' and not already_exist_partner_flag:
                                        partner_vals.update({'last_name': rec_value or ''})
                                    elif header_l == 'Customer' and not already_exist_partner_flag:
                                        cust = False
                                        if rec_value:
                                            cust = True
                                        partner_vals.update({'customer': cust})
                                    elif header_l == 'Supplier' and not already_exist_partner_flag:
                                        supp = False
                                        if rec_value:
                                            supp = True
                                        partner_vals.update({'supplier': supp})
                                    if header_l == 'Code' and not already_exist_partner_flag:
                                        code = ''
                                        if rec_value and type(rec_value) == 'Float':
                                            split_code = str(rec_value).split('.')
                                            if split_code and split_code[1] == '0':
                                                code = split_code and split_code[0]
                                        elif rec_value:
                                            code = rec_value
                                        partner_vals.update({'cust_code': code or ''})
                                    elif header_l == 'Active' and not already_exist_partner_flag:
                                        active = False
                                        if rec_value:
                                            active = True
                                        partner_vals.update({'active': active or ''})
                                    elif header_l == 'Is a Company' and not already_exist_partner_flag:
                                        is_company = False
                                        if rec_value:
                                            is_company = True
                                        partner_vals.update({'is_company': is_company or ''})
                                    elif header_l == 'Currency' and not already_exist_partner_flag:
                                        currency = False
                                        if rec_value:
                                            currency = ustr(rec_value)
                                        partner_vals.update({'currency': currency or False})
                                    elif header_l == 'Street' and not already_exist_partner_flag:
                                        partner_vals.update({'street': rec_value or ''})
                                    elif header_l == 'Street2' and not already_exist_partner_flag:
                                        partner_vals.update({'street2': rec_value or ''})
                                    elif header_l == 'City' and not already_exist_partner_flag:
                                        partner_vals.update({'city': rec_value or ''})
                                    elif header_l == 'State' and not already_exist_partner_flag:
                                        states = state_obj.search([('name','=', ustr(rec_value))])
                                        state = False
                                        if states:
                                            state = states.ids[0]
                                        partner_vals.update({'state_id': state})
                                    elif header_l == 'Zip' and not already_exist_partner_flag:
                                        zip_code = ''
                                        if rec_value and type(rec_value) == 'Float':
                                            split_zip = str(rec_value).split('.')
                                            if split_zip and split_zip[1] == '0':
                                                zip_code = split_zip and split_zip[0]
                                        elif rec_value:
                                            zip_code = rec_value
                                        partner_vals.update({'zip': zip_code})
                                    elif header_l == 'Country' and not already_exist_partner_flag:
                                        countrys = country_obj.search([('name','=', ustr(rec_value))])
                                        country = False
                                        if countrys:
                                            country = countrys.ids[0]
                                        partner_vals.update({'country_id': country})
                                    elif header_l == 'Job Position' and not already_exist_partner_flag:
                                        partner_vals.update({'function': rec_value or ''})
                                    elif header_l == 'Phone' and not already_exist_partner_flag:
                                        partner_vals.update({'phone': rec_value or ''})
                                    elif header_l == 'Mobile' and not already_exist_partner_flag:
                                        mobile = ''
                                        if rec_value and type(rec_value) == 'Float':
                                            split_mobile = str(rec_value).split('.')
                                            if split_mobile and split_mobile[1] == '0':
                                                mobile = split_mobile and split_mobile[0]
                                        elif rec_value:
                                            mobile = rec_value
                                        partner_vals.update({'mobile': mobile or ''})
                                    elif header_l == 'Fax' and not already_exist_partner_flag:
                                        fax = ''
                                        if rec_value and type(rec_value) == 'Float':
                                            split_fax = str(rec_value).split('.')
                                            if split_fax and split_fax[1] == '0':
                                                fax = split_fax and split_fax[0]
                                        elif rec_value:
                                            fax = rec_value
                                        partner_vals.update({'fax': fax or ''})
                                    elif header_l == 'Email' and not already_exist_partner_flag:
                                        partner_vals.update({'email': rec_value or ''})
                                    elif header_l == 'Title' and not already_exist_partner_flag:
                                        titles = title_obj.search([('name','=', ustr(rec_value))])
                                        title = False
                                        if titles:
                                            title = titles.ids[0]
                                        partner_vals.update({'title': title or ''})
                                    elif header_l == 'Customer UEN' and not already_exist_partner_flag:
                                        customer_uen = ''
                                        if rec_value and type(rec_value) == 'Float':
                                            split_customer_uen = str(rec_value).split('.')
                                            if split_customer_uen and split_customer_uen[1] == '0':
                                                customer_uen = split_customer_uen and split_customer_uen[0]
                                        elif rec_value:
                                            customer_uen = rec_value
                                        partner_vals.update({'customer_uen': customer_uen or ''})
                                    elif header_l == 'Customer ID' and not already_exist_partner_flag:
                                        partner_vals.update({'customer_id': rec_value})
                                    elif header_l == 'Supplier UEN' and not already_exist_partner_flag:
                                        supplier_uen = ''
                                        if rec_value and type(rec_value) == 'Float':
                                            split_supplier_uen = str(rec_value).split('.')
                                            if split_supplier_uen and split_supplier_uen[1] == '0':
                                                supplier_uen = split_supplier_uen and split_supplier_uen[0]
                                        elif rec_value:
                                            supplier_uen = rec_value
                                        partner_vals.update({'supplier_uen': supplier_uen or ''})
                                    elif header_l == 'Website' and not already_exist_partner_flag:
                                        partner_vals.update({'website': rec_value or ''})
                                    elif header_l == 'Internal Notes' and not already_exist_partner_flag:
                                        partner_vals.update({'comment': rec_value or ''})
                                    elif header_l == 'Sales Person' and not already_exist_partner_flag:
                                        users = user_obj.search([('name','=', ustr(rec_value))])
                                        user = False
                                        if users:
                                            user = users.ids[0]
                                        partner_vals.update({'user_id': user})
                                    elif header_l == 'Contact Reference' and not already_exist_partner_flag:
                                        partner_vals.update({'ref': rec_value or ''})
#                                     elif header_l == 'Date' and not already_exist_partner_flag:
#                                         partner_vals.update({'date': rec_value or ''})
                                    elif header_l == 'Contacts' and not already_exist_partner_flag:
                                        if rec_value:
                                            for contact in ustr(rec_value).split(','):
                                                contact_ids.append(partner_obj.create({'name': ustr(contact) or ''}))
                                if partner_vals and not already_exist_partner_flag:
                                    if partner_vals.get('currency', False):
                                        currency = currency_obj.search([('name', '=', ustr(partner_vals['currency']))])
                                        if currency:
                                            pricelist_sale_ids = pricelist_obj.search([('currency_id','=', currency.ids[0]), ('type','=', 'sale')])
                                            pricelist_purchase_ids = pricelist_obj.search([('currency_id','=', currency.ids[0]), ('type','=', 'purchase')])
                                            if not pricelist_sale_ids:
                                                pricelist_obj.create({'name': partner_vals['currency'] + ' Sale Pricelist',
                                                                       'active': True,
                                                                       'currency_id': currency.ids[0],
                                                                       'type': 'sale'})
                                            if not pricelist_purchase_ids:
                                                pricelist_obj.create({'name': partner_vals['currency'] + ' Purchase Pricelist',
                                                                       'active': True,
                                                                       'currency_id': currency.ids[0],
                                                                       'type': 'purchase'})
                                            if partner_vals.get('customer', False):
                                                pricelist_sale_ids = pricelist_obj.search([('currency_id','=', currency.ids[0]), ('type','=', 'sale')])
                                                if pricelist_sale_ids:
                                                    partner_vals.update({'property_product_pricelist': pricelist_sale_ids.ids[0]})
                                                else:
                                                    new_pricelist_sale_id = pricelist_obj.create({'name': partner_vals['currency'] + ' Sale Pricelist',
                                                                       'active': True,
                                                                       'currency_id': currency.ids[0],
                                                                       'type': 'sale'})
                                                    partner_vals.update({'property_product_pricelist': new_pricelist_sale_id.id})
                                            if partner_vals.get('supplier', False):
                                                pricelist_purchase_ids = pricelist_obj.search([('currency_id','=', currency.ids[0]), ('type','=', 'purchase')])
                                                if pricelist_purchase_ids:
                                                    partner_vals.update({'property_product_pricelist_purchase': pricelist_purchase_ids.ids[0]})
                                                else:
                                                    new_pricelist_purchase_id = pricelist_obj.create({'name': partner_vals['currency'] + ' Purchase Pricelist',
                                                                       'active': True,
                                                                       'currency_id': currency.ids[0],
                                                                       'type': 'purchase'})
                                                    partner_vals.update({'property_product_pricelist_purchase': new_pricelist_purchase_id.id})
                                    if 'currency' in partner_vals.keys():
                                        partner_vals.pop('currency')
                                    new_partner_id = partner_obj.create(partner_vals)
                                    if contact_ids and new_partner_id:
                                        for contact in contact_ids:
                                            contact.write({'parent_id': new_partner_id.id, 'use_parent_address': True})
            else:
                raise Warning(_("Please select (.xls or .xlsx) extension"
                                " file to import."))
        return True