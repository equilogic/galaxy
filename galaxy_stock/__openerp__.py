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
    "name": "Galaxy Stock",
    "version": "1.0",
    "depends": ['stock'],
    "author" :"Serpent Consulting Services Pvt. Ltd.",
    "website" : "http://www.serpentcs.com",
    'category':'stock',
    "description":"""
        This application enables you to manage stock.
    """,
    "data": [
            'view/stock_view.xml',
            'wizard/stock_analysis_wizard_view.xml',
            'wizard/stock_valuation_category_history.xml',
            "view/stock_picking_move_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

