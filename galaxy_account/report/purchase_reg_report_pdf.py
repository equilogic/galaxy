from openerp.osv import osv
from openerp import api
from openerp.report import report_sxw
import time
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT,ustr



class purchaser_reg_pdf_report(report_sxw.rml_parse):
   
    def __init__(self,cr,uid,name,context=None):
        super(purchaser_reg_pdf_report,self).__init__(cr,uid,name,context=context)
        self.localcontext.update({
            'time': time,
            'get_details': self._get_details
            })
   
    def _get_details(self, data):
        inv_dict = {}
        data_list = []
        inv_obj = self.pool.get('account.invoice')
        inv_data = inv_obj.browse(self.cr, self.uid, data.get('invoice_data', False))
        if inv_data:
            for data in inv_data:
                inv_dict.update({'date': data.date_invoice,
                                 'po': data.number,
                                 'supplier_inv': data.supplier_invoice_number,
                                 'supplier': data.partner_id.name,
                                 'amount': data.amount_total,
                                 'amt_due': data.residual,
                                 'state': data.state,
                                 'delivery_status': data.delivery_status,
                                 })
                data_list.append(inv_dict)
        print "inv_dict=========",data_list
                    
        return data_list
    
class allergan_hourly_profile(osv.AbstractModel):
    _name = 'report.galaxy_account.galaxy_purchase_order_template_pdf'
    _inherit = 'report.abstract_report'
    _template = 'galaxy_account.galaxy_purchase_order_template_pdf'
    _wrapped_report_class = purchaser_reg_pdf_report
