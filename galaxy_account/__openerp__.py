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
{
    'name' : "Galaxy Account",
    'version' : "1.0",
    'author' : "Serpent Consulting Services Pvt. Ltd.",
    'category': 'Account',
    'website' : "http://www.serpentcs.com",
    'description': """
                manage account related information
    """,
    'depends': ['sg_account_odoo','galaxy_product', 'account_cancel','galaxy_stock'],
    'demo': [],
    'data': [
            'views/invoice_form.xml',
            'views/report_view.xml',    
            'views/res_partner_view.xml',
            'views/account_invoice_sequence.xml',
            'report/galaxy_product_tax_invoice_report_view.xml',
            'report/galaxy_sale_local_tax_report.xml',
            'report/galaxy_bank_invoice_report.xml',
            'report/sales_register_report_pdf_view.xml',
            'report/purchase_reg_report_pdf_view.xml',
            'wizard/update_currency_rates.xml',
            'wizard/sales_register_pdf_wiz_view.xml',
            'wizard/purchase_register_pdf_wiz_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
