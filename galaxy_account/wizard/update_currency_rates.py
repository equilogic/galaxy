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

from openerp import fields, models, api, _
from datetime import datetime


class update_currency_rates(models.TransientModel):

    _name = "update.currency.rates"

    currency_ids = fields.One2many('change.currency.history', 'currency_rates_id', 'Currency Change')

    @api.multi
    def chage_rates(self):
        for currency_rec in self.currency_ids:
            currency_list = []
            currency_id = self.env['res.currency'].search([('id', '=', currency_rec.currency_id.id)])
            if currency_id:
                rate_vals = {
                             'name': datetime.now(),
                             'rate': currency_rec.new_rate or 0.0,
                             }
                currency_list.append((0, 0, rate_vals))
                currency_id.write({'rate_ids': currency_list})
        return True

    @api.model
    def default_get(self, fields):
        res = super(update_currency_rates, self).default_get(fields)
        currency_list = []
        if self._context.get('default_currency'):
            currency_rec_ids = self.env['res.currency'].search([('update_manually', '=', True)])
            for currency_rec in currency_rec_ids:
                line_vals = {'currency_id': currency_rec.id, 'current_rate': currency_rec.rate_silent}
                currency_list.append((0, 0, line_vals))
                res.update({'currency_ids': currency_list})
        return res

class change_currency_history(models.TransientModel):

    _name = 'change.currency.history'

    currency_rates_id = fields.Many2one('update.currency.rates', 'Change Currency Rates')
    current_rate = fields.Float('Current Rate', digits=(12, 6))
    new_rate = fields.Float('New Rate', digits=(12, 6))
    currency_id = fields.Many2one('res.currency', 'Currency')
    
class res_currency(models.Model):

    _inherit = 'res.currency'

    update_manually = fields.Boolean('Update Manually')

