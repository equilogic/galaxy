# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Serpent Consulting Services Pvt. Ltd.
#    Copyright (C) 2015 OpenERP SA (<http://www.serpentcs.com>)
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
from openerp.exceptions import Warning
from openerp import netsvc, workflow
from datetime import datetime

class wiz_sales_register_report(models.TransientModel):
    
    _name = 'wiz.sales.register.report'
    
    st_dt = fields.Date('Start Date')
    en_dt = fields.Date('End Date')
    
    @api.multi
    def print_report(self):
        cr, uid, context = self.env.args
        for trans in self:
            if trans:
                data = self.read()[0]
                if context.get('active_ids',False):
                    invoice = context.get('active_ids',False)
                data = {
                    'ids': [],
                    'form': data,
                    'model': 'account.invoice',
                    'context': context,  
                }
            return self.env['report'].get_action(self,
                'galaxy_account.report_galaxy_sales_register_pdf', data = data)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: