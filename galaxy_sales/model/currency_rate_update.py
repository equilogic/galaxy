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


from openerp import models, fields, api
from datetime import datetime
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
from openerp.exceptions import ValidationError
from openerp.osv import osv
from openerp.tools.translate import _

class res_company(models.Model):
    _inherit = 'res.company'

    currency_id = fields.Many2one('res.currency', string="Currency")
    api_key = fields.Char(string = 'Api Key', help = 'API Key require for updating current currency rate.')

    @api.multi
    def refresh_currency(self):
        """Refresh the currencies rates per day"""
        rate_obj = self.env['res.currency.rate']
        # Search for the base currency
        main_currency = self.env['res.currency'].search(
            [('base', '=', True)],
            limit = 1)
        # Check whether the currency is found or not.
        if not main_currency:
            raise ValidationError('There must be atleast 1 currency defined as Base Currency!')
        # Search for all the currencies to convert
        curr_to_fetch = self.env['res.currency'].search([])
        # Check whether a token is created for the company or not.
        if not self.api_key:
            raise Warning("Please input the Xignite Token first for getting Updated Currency Rate.")
        # Fetch the rates for all currencies
        r = self.env['res.currency'].get_updated_currency(curr_to_fetch, main_currency.name, self.api_key)
        # Create rate versions in the system for all currencies
        for key, val in r.items():
            if val['rate']:
                rate_obj = self.env['res.currency.rate'].create({
                                    'name': datetime.now(),
                                    'rate': val['rate'],
                                    'currency_id': key
                                    })

    @api.model
    def _run_currency_update(self):
        self.refresh_currency()

class res_currency_update(models.Model):

    _inherit = "res.currency"

    @api.constrains('base')
    def _check_unique_base_currency(self):
        """
        A constraint added to have only 1 base currency in the system
        -------------------------------------------------------------
        @param self : object pointer
        """
        for curr in self:
            if curr.base:
                base_curr = self.search([('base', '=', True)])
                if base_curr.ids:
                    # This will give two records including the current currency record.
                    for bc in base_curr:
                        if bc.id != self.id:
                            raise ValidationError("""You must have only 1 base currency in the system.\nCurrently "%s" is already set as base currency!""" % (bc.name))

    @api.v7
    def _current_rate_silent(self, cr, uid, ids, name, arg, context = None):
        return self._get_current_rate(cr, uid, ids, raise_on_no_rate = False, context = context)

    @api.v7
    def _get_current_rate(self, cr, uid, ids, raise_on_no_rate = True, context = None):
        if context is None:
            context = {}
        res = {}
        date = context.get('date') or datetime.now()
        for id in ids:
            cr.execute('SELECT rate FROM res_currency_rate '
                       'WHERE currency_id = %s '
                         'AND name <= %s '
                       'ORDER BY name desc LIMIT 1',
                       (id, date))
            if cr.rowcount:
                res[id] = cr.fetchone()[0]
            elif not raise_on_no_rate:
                res[id] = 0
            else:
                currency = self.browse(cr, uid, id, context = context)
                raise osv.except_osv(_('Error!'), _("No currency rate associated for currency '%s' for the given period" % (currency.name)))
        return res

    @api.multi
    def get_updated_currency(self, currency_array, main_currency, api_key):
        url = ('http://globalcurrencies.xignite.com/xGlobalCurrencies.csv/GetRealTimeRate?Symbol=%s')

        cur_dict = {}
        for curr in currency_array:
            # Generate a URL for conversion
            t = url % str(main_currency) + str(curr.name) + '&_token=' + str(api_key)
            try:
                # Call the URL Request and Receive Response
                objfile = urllib.urlopen(t)
                # Get the rate result as CSV
                buf = base64.encodestring(objfile.read())
                csv_data = base64.decodestring(buf)
                f = StringIO.StringIO(csv_data)
                reader = list(csv.reader(f, delimiter = ','))
                headers = reader[0]
                data = reader[1]
                # Create a dictionary for rate conversion
                cur_dict[curr.id] = {
                        'rate': data[11],
                        'currency_id': curr.id
                        }
            except Exception as exc:
                error = '\nERROR : %s' % (exc)
        return cur_dict