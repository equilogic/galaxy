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
from openerp import models
import time
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

GLOBAL_STATE_DICT = {'draft' : 'Draft',
		               'proforma': 'Pro-forma',
		               'proforma2': 'Pro-forma',
		               'open': 'Open',
		               'paid': 'Paid',
		               'cancel': 'Cancelled'}

class report_sales_register_pdf(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(report_sales_register_pdf, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'get_invoice_data':self._get_invoice_data,
			'get_company':self.get_company
		})

	def _get_invoice_data(self, data):
		inv_data_lst = []
		if data and data.get('form', False):
			invoices = False

			if data['form'].get('st_dt', False) and data['form'].get('en_dt', False):
				invoices = self.pool.get('account.invoice').search(self.cr, self.uid, [('date_invoice','>=', data['form']['st_dt']),
													('date_invoice','<=', data['form']['en_dt']),
													('type','=', 'out_invoice'),('state', '!=','cancel')], order='origin' )
			if invoices:
				for inv in self.pool.get('account.invoice').browse(self.cr, self.uid, invoices):
					new_dt=datetime.strptime(inv.date_invoice, DEFAULT_SERVER_DATE_FORMAT)
					formated_dt=datetime.strftime(new_dt, "%d-%m-%Y")	
					inv_data_lst.append({
						'date': formated_dt or '',
						'invoice': inv.number or '',
						'customer_po': inv.customer_po or '', 
						'customer': inv.partner_id and inv.partner_id.name or '',
						'amount': inv.amount_total or 0.00,
						'amount_due': inv.amount_total or 0.00,
						'status': GLOBAL_STATE_DICT.get(inv.state, '') or '',
					})
		return inv_data_lst

	def get_company(self, data):
		user = self.pool.get('res.users').browse(self.cr, self.uid, self.uid)
		return user and user.company_id or False


class report_print_sales_register_pdf_extended(models.AbstractModel):
	_name = 'report.galaxy_account.report_galaxy_sales_register_pdf'
	_inherit = 'report.abstract_report'
	_template = 'galaxy_account.report_galaxy_sales_register_pdf'
	_wrapped_report_class = report_sales_register_pdf