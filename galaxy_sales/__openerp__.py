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
    "name": "Galaxy Sales",
    "version": "1.0",
    "depends": ['sale','galaxy_product','galaxy_account'],
    "author" :"Serpent Consulting Services Pvt. Ltd.",
    "website" : "http://www.serpentcs.com",
    "category":"sale",
    "description":"""
        This application enables you to manage sales for Products.
    """,
    "data": [
             "report/sales_dmy_custom_report_view.xml",
             "wizard/wiz_galaxy_add_prod_in_so.xml",
             "views/sales_order_view.xml",
             "views/currency_rate_update_view.xml",
             "views/template.xml",
             "views/res_partner_view.xml",
             "views/sale_order_sequence.xml",
             "wizard/wiz_sale_order_register_view.xml",
             "wizard/wiz_sale_register_view.xml",
             "wizard/wiz_sales_register_view.xml",
             "wizard/wiz_product_wise_sale_report_1_view.xml",
             "wizard/wiz_product_wise_sale_report_2_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

