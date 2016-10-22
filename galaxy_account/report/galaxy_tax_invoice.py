# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import time
from openerp.report import report_sxw
from openerp import models,api,_,fields
from openerp.tools.amount_to_text_en import amount_to_text


class report_print_tax_invoice(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_print_tax_invoice, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'amount_to_text': self._amount_to_text,
            'get_qty':self._get_qty,
            'origin': self._get_origin
        })

    def _amount_to_text(self, amount):
        # Currency complete name is not available in res.currency model
        # Exceptions done here (EUR, USD, BRL) cover 75% of cases
        # For other currencies, display the currency code
        return amount_to_text(amount)

    def _get_qty(self,qty):
        return int(qty)
    
    def _get_origin(self, line):
        origin =''
        if line and line.origin_ids:
            for origin_name in line.origin_ids:
                if origin:
                    origin = origin + ',' + '['+str(origin_name.qty)+']'+origin_name.name.name
                else:
                    origin = '['+str(origin_name.qty)+']'+origin_name.name.name
        return origin

class report_print_tax_invoice_extended(models.AbstractModel):
    _name = 'report.galaxy_account.report_galaxy_product_tax_invoice'
    _inherit = 'report.abstract_report'
    _template = 'galaxy_account.report_galaxy_product_tax_invoice'
    _wrapped_report_class = report_print_tax_invoice