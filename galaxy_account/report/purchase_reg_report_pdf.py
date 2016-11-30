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
            })
   
        

class allergan_hourly_profile(osv.AbstractModel):
    _name = 'report.galaxy_account.galaxy_purchase_order_template_pdf'
    _inherit = 'report.abstract_report'
    _template = 'galaxy_account.galaxy_purchase_order_template_pdf'
    _wrapped_report_class = purchaser_reg_pdf_report
