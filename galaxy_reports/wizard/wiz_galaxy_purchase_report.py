import xlwt
import base64
import tempfile
from xlrd import open_workbook
from StringIO import StringIO
from datetime import datetime
from openerp.tools import misc, DEFAULT_SERVER_DATE_FORMAT, ustr
from openerp.exceptions import Warning
from openerp import fields, models, api, _


class wiz_galaxy_purchase_report(models.TransientModel):
    _name = "wiz.galaxy.purchase.report"

    date_from = fields.Date(string='From', default=datetime.now().date().strftime("%Y-%m-01"))
    date_to = fields.Date(string='To', default=datetime.now().date())
    report_name = fields.Selection([('purch_reg_rep', 'Purchase Register Report'),
                                    ('purch_order_reg_rep', 'Purchase Order Register Report'),
                                    ('prod_wise_purch_rep_summary', 'Product-wise Purchase Report in Summary'),
                                    ('prod_wise_purch_rep_detail', 'Product-wise Purchase Report in Detail')],
                                   default="purch_reg_rep", string="Report")
    partner_ids = fields.Many2many('res.partner','res_partner_purchase_report_rel', 'wiz_id', 'partner_id', 'Suppliers')

    @api.onchange('report_name')
    def onchange_report_name(self):
        if self.report_name and self.report_name != 'prod_wise_purch_rep_summary':
            self.partner_ids = [(6, 0, [])]

    @api.multi
    def print_report(self):
        cr, uid, context = self.env.args
        purchase_obj = self.env['purchase.order']
        purch_ord_line_obj = self.env['purchase.order.line']
        partner_obj = self.env['res.partner']
        for wiz in self:
            fl = StringIO()
            wbk = xlwt.Workbook(encoding='utf-8')
            font = xlwt.Font()
            font.bold = True
            header_left = xlwt.easyxf('align: horiz left')
            bold_header_left = xlwt.easyxf("font: bold 1, height 200,"
                               " color black; align: horiz left")
            header8 = xlwt.easyxf('align: horiz left')
            header_left = xlwt.easyxf('align: horiz left')
            main_header = xlwt.easyxf('font: bold 1, height 360; align: horiz center,vert center')
            header2 = xlwt.easyxf('font: bold 1, height 230; align: horiz center,vert center ;borders :top hair, bottom hair,left hair, right hair, bottom_color black,top_color black')
            header2_left = xlwt.easyxf('font: bold 1, height 230; align: horiz left ;borders :top hair, bottom hair,left hair, right hair, bottom_color black,top_color black')
            rep_name = ''
            
            st_dt = datetime.strptime(wiz.date_from,
                                       DEFAULT_SERVER_DATE_FORMAT)
            start_dt = datetime.strftime(st_dt, "%Y/%m/%d")
            en_dt = datetime.strptime(wiz.date_to,
                                       DEFAULT_SERVER_DATE_FORMAT)
            end_dt = datetime.strftime(en_dt, "%Y/%m/%d")
            
            if wiz.report_name == 'purch_reg_rep':
                worksheet = wbk.add_sheet('Purchase Register Report')
                rep_name = 'Purchase Register Report.xls'
                purch_ords = purchase_obj.search(
                         [('state', '!=', 'draft'),
                          ('date_order', '>=', start_dt),
                          ('date_order', '<=', end_dt)])
                invoices = []
                if purch_ords:
                    for purch in purch_ords:
                        if purch.invoice_ids:
                            invoices = [inv for inv in purch.invoice_ids if inv.state != 'draft']
                    worksheet.row(0).height = 600
                    worksheet.write_merge(0, 0, 0, 8, 'Purchase Register Report ' + ' ( ' + start_dt + ' to ' + end_dt+' ) ', main_header)
                    col = 0
                    row = 1
                    worksheet.col(col).width = 3000
                    worksheet.write(row, col, 'Sr. No.', header2)
                    col += 1
                    worksheet.col(col).width = 5000
                    worksheet.write(row, col, 'Date', header2)
                    col += 1
                    worksheet.col(col).width = 6000
                    worksheet.write(row, col, 'Purchase Invoice No.', header2)
                    col += 1
                    worksheet.col(col).width = 5000
                    worksheet.write(row, col, 'Supplier PO No.', header2)
                    col += 1
                    worksheet.col(col).width = 5000
                    worksheet.write(row, col, 'Customer Name', header2)
                    col += 1
                    worksheet.col(col).width = 7000
                    worksheet.write(row, col, 'Amount in Actual Currency', header2)
                    col += 1
                    worksheet.col(col).width = 5000
                    worksheet.write(row, col, 'Tax amt', header2)
                    col += 1
                    worksheet.col(col).width = 5000
                    worksheet.write(row, col, 'Amt in SGD', header2)
                    col += 1
                    worksheet.col(col).width = 7000
                    worksheet.write(row, col, 'Tax Amt in SGD', header2)
                    
                    col = 0
                    row += 1
                    seq_no = 1
                    for invoice in invoices:
                        worksheet.write(row, col, seq_no or '', header8)
                        col += 1
                        worksheet.write(row, col, invoice.date_invoice or '', header8)
                        col += 1
                        worksheet.write(row, col, invoice.origin or '', header8)
                        col += 1
                        worksheet.write(row, col, invoice.origin, header8)
                        col += 1
                        worksheet.write(row, col, invoice.partner_id and invoice.partner_id.name or '', header8)
                        col += 1
                        worksheet.write(row, col, invoice.amount_total or '', header8)
                        col += 1
                        worksheet.write(row, col, invoice.amount_tax or '', header8)
                        col += 1
                        worksheet.write(row, col, '', header8)
                        col += 1
                        worksheet.write(row, col, '', header8)
                        col = 0
                        row += 1
                        seq_no += 1
            elif wiz.report_name == 'purch_order_reg_rep':
                worksheet = wbk.add_sheet('Purchase Order Register Report')
                rep_name = 'Purchase Order Register Report.xls'
                purch_ords = purchase_obj.search(
                         [('state', '!=', 'draft'),
                          ('date_order', '>=', start_dt),
                          ('date_order', '<=', end_dt)])
                if purch_ords:
                    worksheet.row(0).height = 600
                    worksheet.write_merge(0, 0, 0, 6, 'Purchase Order Register Report ' + ' ( ' + start_dt + ' to ' + end_dt+' ) ', main_header)
                    col = 0
                    row = 1
                    worksheet.col(col).width = 3000
                    worksheet.write(row, col, 'Sr. No.', header2)
                    col += 1
                    worksheet.col(col).width = 5000
                    worksheet.write(row, col, 'Date', header2)
                    col += 1
                    worksheet.col(col).width = 6000
                    worksheet.write(row, col, 'Purchase Order No.', header2)
                    col += 1
                    worksheet.col(col).width = 5000
                    worksheet.write(row, col, 'Supplier PO No.', header2)
                    col += 1
                    worksheet.col(col).width = 5000
                    worksheet.write(row, col, 'Supplier Name', header2)
                    col += 1
                    worksheet.col(col).width = 8000
                    worksheet.write(row, col, 'Order Amt in Actual Currency', header2)
                    col += 1
                    worksheet.col(col).width = 5000
                    worksheet.write(row, col, 'Tax amt', header2)
                    
                    col = 0
                    row += 1
                    seq_no = 1
                    for purch_ord in purch_ords:
                        worksheet.write(row, col, seq_no or '', header8)
                        col += 1
                        worksheet.write(row, col, purch_ord.date_order or '', header8)
                        col += 1
                        worksheet.write(row, col, purch_ord.name or '', header8)
                        col += 1
                        worksheet.write(row, col, '', header8)
                        col += 1
                        worksheet.write(row, col, purch_ord.partner_id and purch_ord.partner_id.name or '', header8)
                        col += 1
                        worksheet.write(row, col, purch_ord.amount_total or '', header8)
                        col += 1
                        worksheet.write(row, col, purch_ord.amount_tax or '', header8)
                        col = 0
                        row += 1
                        seq_no += 1
                        
                        
            elif wiz.report_name == 'prod_wise_purch_rep_summary':
                worksheet = wbk.add_sheet('Product-wise Purchase Summary')
                rep_name = 'Product-wise Purchase Report in Summary.xls'
                partner_ids = wiz.partner_ids
                worksheet.row(0).height = 600
                worksheet.col(0).width = 7000
                worksheet.col(1).width = 7000
                worksheet.col(2).width = 7000
                worksheet.col(3).width = 5000
                worksheet.col(4).width = 7000
                worksheet.write_merge(0, 0, 0, 4, 'Product-wise Purchase Report in Summary' + '( ' + start_dt + ' to ' + end_dt+' )', main_header)
                if not wiz.partner_ids:
                    partner_ids = partner_obj.search([('supplier','=', True)])
                row = 1
                for partner in partner_ids:
                    purch_ords = purchase_obj.search(
                             [('partner_id', '=', partner.id),('state', '!=', 'draft'),
                              ('date_order', '>=', start_dt),
                              ('date_order', '<=', end_dt)])
                    if purch_ords:
                        col = 0
                        worksheet.col(col).width = 7000
                        worksheet.write(row, col, 'Supplier Name', header2_left)
                        col += 1
                        worksheet.write(row, col, partner.name or '', header_left)
                        
                        col = 0
                        row += 1
                        worksheet.col(col).width = 7000
                        worksheet.write(row, col, 'Product Name', header2_left)
                        col += 1
                        worksheet.col(col).width = 5000
                        worksheet.write(row, col, 'Qty', header2)
                        col += 1
                        worksheet.col(col).width = 7000
                        worksheet.write(row, col, 'Amt in Actual Currency', header2)
                        col += 1
                        worksheet.col(col).width = 5000
                        worksheet.write(row, col, 'Amt in SGD', header2)
                        
                        col = 0
                        row += 1
                        for purch_ord in purch_ords:
                            for purch_l in purch_ord.order_line:
                                worksheet.write(row, col, purch_l.product_id and purch_l.product_id.name or '', header_left)
                                col += 1
                                worksheet.write(row, col, purch_l.product_qty or '', header8)
                                col += 1
                                worksheet.write(row, col, purch_l.price_subtotal or '', header8)
                                col += 1
                                worksheet.write(row, col, '', header8)
                                col = 0
                                row += 1
                        row += 1
            elif wiz.report_name == 'prod_wise_purch_rep_detail':
                worksheet = wbk.add_sheet('Product-wise Purchase Detail')
                rep_name = 'Product-wise Purchase Report in Detail.xls'
                partner_ids = wiz.partner_ids
                worksheet.row(0).height = 600
                worksheet.col(0).width = 7000
                worksheet.col(1).width = 7000
                worksheet.col(2).width = 7000
                worksheet.col(3).width = 5000
                worksheet.col(4).width = 7000
                worksheet.write_merge(0, 0, 0, 5, 'Product-wise Purchase Report in Detail' + '( ' + start_dt + ' to ' + end_dt+' )', main_header)
                if not wiz.partner_ids:
                    partner_ids = partner_obj.search([('supplier','=', True)])
                row = 1
                for partner in partner_ids:
                    purch_ords = purchase_obj.search(
                             [('partner_id', '=', partner.id),('state', '!=', 'draft'),
                              ('date_order', '>=', start_dt),
                              ('date_order', '<=', end_dt)])
                    if purch_ords:
                        col = 0
                        worksheet.col(col).width = 7000
                        worksheet.write(row, col, 'Supplier Name', header2_left)
                        col += 1
                        worksheet.write(row, col, partner.name or '', header_left)
                        col += 1
                        worksheet.write(row, col, 'Customer Code', header2_left)
                        col += 1
                        worksheet.write(row, col, '', header_left)
                        
                        col = 0
                        row += 1
                        worksheet.col(col).width = 7000
                        worksheet.write(row, col, 'Product Name', header2_left)
                        col += 1
                        worksheet.col(col).width = 7000
                        worksheet.write(row, col, 'Date', header2)
                        col += 1
                        worksheet.col(col).width = 5000
                        worksheet.write(row, col, 'Quantity', header2)
                        col += 1
                        worksheet.col(col).width = 7000
                        worksheet.write(row, col, 'Amt in Actual Currency', header2)
                        col += 1
                        worksheet.col(col).width = 5000
                        worksheet.write(row, col, 'Amt in SGD', header2)
                        col += 1
                        worksheet.col(col).width = 5000
                        worksheet.write(row, col, 'Tax Amt in SGD', header2)
                        
                        col = 0
                        row += 1
                        for purch_ord in purch_ords:
                            for purch_l in purch_ord.order_line:
                                worksheet.write(row, col, purch_l.product_id and purch_l.product_id.name or '', header_left)
                                col += 1
                                worksheet.write(row, col, purch_ord.date_order or '', header8)
                                col += 1
                                worksheet.write(row, col, purch_l.product_qty or '', header8)
                                col += 1
                                worksheet.write(row, col, purch_l.price_subtotal or '', header8)
                                col += 1
                                worksheet.write(row, col, '', header8)
                                col += 1
                                worksheet.write(row, col, '', header8)
                                col = 0
                                row += 1
                        row += 1
            wbk.save(fl)
            fl.seek(0)
            buf = base64.encodestring(fl.read())
            vals = {'file': buf, 'report_name': rep_name}
            cr, uid, context = self.env.args
            ctx = dict(context)
            ctx.update(vals)
            self.env.args = cr, uid, misc.frozendict(ctx)
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wiz.galaxy.purchase.report.detail',
            'target': 'new',
            'context': ctx
        }


class wiz_galaxy_purchase_report_detail(models.TransientModel):
    _name = "wiz.galaxy.purchase.report.detail"

    @api.model
    def default_get(self, fields):
        super(wiz_galaxy_purchase_report_detail, self).default_get(fields)
        cr, uid, context = self.env.args
        res = dict(context)
        vals = {'name': 'Purchase report.xls'}
        if context.get('report_name', False):
            vals = {'name': context['report_name']}
        res.update(vals)
        self.env.args = cr, uid, misc.frozendict(res)
        if context.get('file'):
            vals1 = {'file': context['file']}
            cr, uid, context = self.env.args
            res = dict(context)
            res.update(vals1)
            self.env.args = cr, uid, misc.frozendict(res)
        return res

    file = fields.Binary('File')
    name = fields.Char(string='File Name', size=64)

    @api.multi
    def action_back(self):
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wiz.galaxy.purchase.report',
            'target': 'new',
        }
