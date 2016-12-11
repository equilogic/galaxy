from openerp.osv import osv
from openerp import api
from openerp.report import report_sxw
import time
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT,ustr


GLOBAL_STATE_DICT = {'draft' : 'Draft',
                       'proforma': 'Pro-forma',
                       'proforma2': 'Pro-forma',
                       'open': 'Open',
                       'paid': 'Paid',
                       'cancel': 'Cancelled'}

class purchaser_reg_pdf_report(report_sxw.rml_parse):
   
    def __init__(self,cr,uid,name,context=None):
        super(purchaser_reg_pdf_report,self).__init__(cr,uid,name,context=context)
        self.localcontext.update({
            'time': time,
            'get_details': self._get_details,
            'get_company': self._get_company,
            })
   
    def _get_details(self, data):
        inv_dict = {}
        data_list = []
        inv_obj = self.pool.get('account.invoice')
        inv_data = inv_obj.browse(self.cr, self.uid, data.get('invoice_data', False))
        if inv_data:
            for data in inv_data:
                new_dt=datetime.strptime(data.date_invoice, DEFAULT_SERVER_DATE_FORMAT)
                formated_dt=datetime.strftime(new_dt, "%d-%m-%Y")                    
                data_list.append({'date': formated_dt,
                                 'po': data.number,
                                 'supplier_inv': data.supplier_invoice_number,
                                 'supplier': data.partner_id.name,
                                 'amount': data.amount_total,
                                 'amt_due': data.amount_total,
                                 'state': GLOBAL_STATE_DICT.get(data.state, '') or '',
                                 'delivery_status': data.delivery_status,
                                 })
        newlist = sorted(data_list, key=lambda k: k['po']) 
        return newlist

    def _get_company(self, data):
        user = self.pool.get('res.users').browse(self.cr, self.uid, self.uid)
        return user and user.company_id or False
    
class allergan_hourly_profile(osv.AbstractModel):
    _name = 'report.galaxy_account.galaxy_purchase_order_template_pdf'
    _inherit = 'report.abstract_report'
    _template = 'galaxy_account.galaxy_purchase_order_template_pdf'
    _wrapped_report_class = purchaser_reg_pdf_report
