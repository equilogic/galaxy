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

from openerp import fields, models, api, _
from openerp.exceptions import Warning
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

class purchaser_register_pdf_report(models.TransientModel):
    _name = "purchaser.register.pdf.report"

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')


    @api.constrains('start_date', 'end_date')
    def _check_date(self):
        for order in self:
            if order.start_date and order.end_date:
                join_dt = datetime.strptime(order.start_date, DEFAULT_SERVER_DATE_FORMAT)
                end_date = datetime.strptime(order.end_date, DEFAULT_SERVER_DATE_FORMAT)

                if end_date < join_dt:
                    raise ValidationError('End date must be greater than start Date !!!!!')
                
    @api.multi
    def print_report(self):
        cr, uid, context = self.env.args
        data = self.read()[0]
        company_id = self.env['res.company'].search([])
        domain = [('type','=','in_invoice'), ('state', '!=','cancel')]
        if data.get('start_date', False):
            domain.append(('date_invoice','>=',data.get('start_date', False)))
        if data.get('end_date', False):
            domain.append(('date_invoice','<=',data.get('end_date', False)))
        invoice_data = self.env['account.invoice'].search(domain, order='name')
        datas = {
            'ids': [],
            'form': data,
            'model': 'account.invoice',
            'context': context,
            'invoice_data': invoice_data.ids,
            'company_id': company_id.ids,
        }
        return self.env['report'].get_action(self,
                 'galaxy_account.galaxy_purchase_order_template_pdf', data = datas)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: