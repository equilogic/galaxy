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
import xlwt
import base64
import tempfile
from xlrd import open_workbook
from StringIO import StringIO
from datetime import datetime
from openerp.tools import misc, DEFAULT_SERVER_DATE_FORMAT, ustr
from openerp.exceptions import Warning
from openerp import fields, models, api, _
from openerp.tools.sql import drop_view_if_exists


class product_qty_on_hand(models.TransientModel):
    _name = "product.qty.on.hand"

    date_from = fields.Date(string='From', default=datetime.now().date().strftime("%Y-%m-01"))
    date_to = fields.Date(string='To', default=datetime.now().date())

    @api.multi
    def print_report(self):
        cr, uid, context = self.env.args
        stock_obj = self.env['stock.move']
        sale_line_obj = self.env['sale.order.line']
        purchase_line_obj = self.env['purchase.order.line']
        proudct_list = []
        product_qty = {}
#        for wiz in self:
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
        header2_left = xlwt.easyxf('font: bold 0, height 200; align: horiz left ;borders :top hair, bottom hair,left hair, right hair, bottom_color black,top_color black')
        rep_name = ''
        
        st_dt = datetime.strptime(self.date_from,
                                   DEFAULT_SERVER_DATE_FORMAT)
        start_dt = datetime.strftime(st_dt, "%d-%m-%Y")
        en_dt = datetime.strptime(self.date_to,
                                   DEFAULT_SERVER_DATE_FORMAT)
        end_dt = datetime.strftime(en_dt, "%d-%m-%Y")
        
        worksheet = wbk.add_sheet('Sales Register Report')
        rep_name = 'Item Register.xls'
        product_ids = self.env['product.product'].search([])
        
        worksheet.row(0).height = 600
        worksheet.write_merge(0, 0, 0, 6, 'Item Register Report ' + ' ( ' + start_dt + ' to ' + end_dt+' ) ', main_header)
        col = 0
        row = 3
        worksheet.row(3).height = 400
        worksheet.col(col).width = 10000
        worksheet.write(row, col, 'Product Reference', header2)
        col += 1
        worksheet.col(col).width = 10000
        worksheet.write(row, col, 'Product Name', header2)
        col += 1
        worksheet.col(col).width = 5000
        worksheet.write(row, col, 'Opening Stock', header2)
        col += 1
        worksheet.col(col).width = 5000
        worksheet.write(row, col, 'Purchase Qty', header2)            
        col += 1              
        worksheet.col(col).width = 5000
        worksheet.write(row, col, 'Sold Qty', header2)
        col += 1
        worksheet.col(col).width = 5000
        worksheet.write(row, col, 'Qty(C+D - E)', header2)
        
        col += 1
        worksheet.col(col).width = 5000
        worksheet.write(row, col, 'Oty In stock', header2)
                
        if product_ids:
            for product in  product_ids:
                stock_data = stock_obj.search([('inventory_id', '!=', False),('product_id','=',product.id),
                                               ('date','>=',self.date_from),('date','<=', self.date_to)]) 
                if stock_data:
                    if product_qty.has_key(product.id):
                        product_qty[product.id].update({'opening_stock': product_qty[product.id].get('opening_stock', False)\
                                                         + stock_data.product_uom_qty})
                    else:   
                        product_qty[product.id] = {'opening_stock': stock_data.product_uom_qty}
                sale_line_data = sale_line_obj.search([('product_id','=',product.id),
                                                       ('order_id.date_order', '>=', self.date_from),
                                                       ('order_id.date_order', '<=', self.date_to)])
                if sale_line_data:
                    for line in sale_line_data:
                        if product_qty.has_key(product.id):
                            product_qty[product.id].update({'sold_qty':  product_qty[product.id].get('sold_qty', 0)\
                                                             + line.product_uom_qty}) 
                        else:
                             product_qty[product.id] ={'sold_qty': line.product_uom_qty}
                pur_line_data = purchase_line_obj.search([('product_id','=',product.id),
                                                       ('order_id.date_order', '>=', self.date_from),
                                                       ('order_id.date_order', '<=', self.date_to)])
                if pur_line_data:
                    for line1 in pur_line_data:
                        if product_qty.has_key(product.id):
                            product_qty[product.id].update({'pur_qty': product_qty[product.id].get('pur_qty', 0) + \
                                                            line1.product_qty}) 
                        else:
                            product_qty[product.id] = {'pur_qty': line1.product_qty} 
                if product_qty.has_key(product.id): 
                    product_qty[product.id].update({'name': product.name,'ref': product.default_code, 'qty_avi': product.qty_available})
                else:
                    product_qty[product.id] = {'name': product.name,'ref': product.default_code,'qty_avi': product.qty_available}
            if product_qty: 
                proudct_list.append(product_qty)                                                 
    
        if proudct_list:
            row = 4
            for pro_dict in proudct_list:
                for key, data in pro_dict.items():
                    worksheet.write(row, 0, data.get('name'), header2_left)
                    worksheet.write(row, 1, data.get('ref'), header2_left)
                    worksheet.write(row, 2, int(data.get('opening_stock', False)) or 0, header2_left)
                    worksheet.write(row, 3, int(data.get('pur_qty', False)) or 0, header2_left)
                    worksheet.write(row, 4, int(data.get('sold_qty', False)) or 0, header2_left)
                    worksheet.write(row, 5, (int(data.get('opening_stock', False)) + int(data.get('pur_qty', False)) - int(data.get('sold_qty', False))) or 0, header2_left)
                    worksheet.write(row, 6, int(data.get('qty_avi', False)) or 0, header2_left)
                    row+=1
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
            'res_model': 'wiz.product.qty.on.hand.detail',
            'target': 'new',
            'context': ctx
        }


class wiz_product_qty_on_hand_detail(models.TransientModel):
    _name = "wiz.product.qty.on.hand.detail"

    @api.model
    def default_get(self, fields):
        super(wiz_product_qty_on_hand_detail, self).default_get(fields)
        cr, uid, context = self.env.args
        res = dict(context)
        vals = {'name': 'Sales report.xls'}
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
            'res_model': 'product.qty.on.hand',
            'target': 'new',
        }
