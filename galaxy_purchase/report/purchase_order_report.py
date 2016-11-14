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
from openerp.tools import ustr


class report_print_purchase_order(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_print_purchase_order, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'amount_to_text': self._amount_to_text,
            'get_qty':self._get_qty,
            'origin': self._get_origin,
            'get_cost':self._get_cost,
            'get_price_subtotal':self._get_price_subtotal,
        })
        
    def _get_price_subtotal(self,price):
        return "{:0,.2f}".format(price)

    def _get_cost(self,landed_cost,currency):
        lines=[]
        for cost in landed_cost:
            vals={
                  'name':cost.name,
                  'amount':currency.name +currency.symbol+ustr("{:0,.2f}".format(cost.amount))
                  }
            lines.append(vals)
        return lines
    
    def _amount_to_text(self, amount,currency):
        # Currency complete name is not available in res.currency model
        # Exceptions done here (EUR, USD, BRL) cover 75% of cases
        # For other currencies, display the currency code
        return amount_to_text(amount,currency=currency.name)

    def _get_qty(self,qty):
        return "{:0,}".format(int(qty))
    
    def _get_origin(self, line):
        origin =''
        if line and line.origin_ids:
            for origin_name in line.origin_ids:
                if origin:
                    origin = origin + ',' + origin_name.name.name
                else:
                    origin = origin_name.name.name
        return origin

class report_print_purchase_order_extended(models.AbstractModel):
    _name = 'report.galaxy_purchase.report_galaxy_purchase_order_report'
    _inherit = 'report.abstract_report'
    _template = 'galaxy_purchase.report_galaxy_purchase_order_report'
    _wrapped_report_class = report_print_purchase_order