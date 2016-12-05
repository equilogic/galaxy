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



from openerp import models, fields, api
import base64
import xlwt
from xlwt import Workbook
from StringIO import StringIO
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

class stock_wiz_report(models.TransientModel):
    _name="stock.wiz"

    product_id = fields.Many2many('product.product',string='Product')


    @api.multi
    def export_stock_report(self):
        
        cr,uid,context = self.env.args
        pur_obj = self.env['purchase.order']
        pur_line_obj = self.env['purchase.order.line']
        cur_obj = self.env['res.currency']
        
        from_currency=self.env['res.users'].browse(uid).company_id.currency_id
        to_currency1 = cur_obj.browse(3)
        to_currency2 = cur_obj.browse(1)
        to_currency3 = cur_obj.browse(38)
        
        fl = StringIO()
        cr,uid,context=self.env.args
        ctx=dict(context)
        
        row=2
        row1=0
        row2=0
        max_raw=0
        min_raw=3
        
        col=0
        
        name=''
        qty=0
        cost=0.0
        stock_price=0.0
            
        data_list=[]
        data_list_eur=[]
        data_list_sgd=[]
       
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('New Sheet')
        
        CORAL_TABLE = xlwt.easyxf(
                 'align: horiz center,vert center ;'
                 'borders :top hair, bottom hair,left hair, right hair, bottom_color black,top_color black;'
                'pattern:pattern solid ,fore_colour coral;'
                 )
        
        CORAL_TABLE_HEADER = xlwt.easyxf(
                'font: bold 1, height 230;'
                 'align: horiz center,vert center ;'
                 'borders :top hair, bottom hair,left hair, right hair, bottom_color black,top_color black;'
                'pattern:pattern solid ,fore_colour coral;'
                 )
        
        SKY_BLUE_TABLE_HEADER = xlwt.easyxf(
                'font: bold 1, height 230;'
                 'align: horiz center,vert center ;'
                 'borders :top hair, bottom hair,left hair, right hair, bottom_color black,top_color black;'
                'pattern:pattern solid ,fore_colour sky_blue;'
                 )
        SKY_BLUE_TABLE = xlwt.easyxf(
                 'align: horiz center,vert center ;'
                 'borders :top hair, bottom hair,left hair, right hair, bottom_color black,top_color black;'
                'pattern:pattern solid ,fore_colour sky_blue;'
                 )
        
        GREEN_TABLE = xlwt.easyxf(
                 'align: horiz center,vert center ;'
                 'borders :top hair, bottom hair,left hair, right hair, bottom_color black,top_color black;'
                'pattern:pattern solid ,fore_colour bright_green;'
                 )
        
        GREEN_TABLE_HEADER = xlwt.easyxf(
                'font: bold 1, height 230;'
                 'align: horiz center,vert center ;'
                 'borders :top hair, bottom hair,left hair, right hair, bottom_color black,top_color black;'
                'pattern:pattern solid ,fore_colour bright_green;'
                 )
      
        font = xlwt.Font()
        font.bold = True
        data_style = xlwt.easyxf('font: height 200; borders: top hair, bottom hair,left hair, right hair, bottom_color black,top_color black ,right_color black,left_color black;align: wrap off;align: wrap on , horiz left;')
        
        header1 = xlwt.easyxf('align: horiz center,vert center ;borders :top hair, bottom hair,left hair, right hair, bottom_color black,top_color black')
        header2 = xlwt.easyxf('font: bold 1, height 230; align: horiz center,vert center ,wrap 1;borders :top hair, bottom hair,left hair, right hair, bottom_color black,top_color black')
        
        
        
        
        
        worksheet.row(1).height=400
        worksheet.row(row).height=400
        worksheet.row(row+1).height=400
        worksheet.col(0).width = 5000
        worksheet.col(1).width = 2000
        worksheet.col(2).width = 4500
        worksheet.col(3).width = 4000
        worksheet.col(4).width = 5000
        worksheet.col(5).width = 2000
        worksheet.col(6).width = 4000
        worksheet.col(7).width = 4000
        worksheet.col(8).width = 5000
        worksheet.col(9).width = 2000
        worksheet.col(10).width = 4000
        worksheet.col(11).width = 4000
        worksheet.col(12).width = 5000
        worksheet.col(13).width = 2000
        worksheet.col(14).width = 4000
        worksheet.col(15).width = 4000
        
        worksheet.write(row, col, "Product Name",header2)
        col+=1
        worksheet.write(row, col, "Total Qty",header2)
        col+=1
        worksheet.write(row, col, "Avg Cost",header2)
        col+=1
        worksheet.write(row, col, "Stock Value(SGD)",header2)
        col+=1
        row=1
        worksheet.write_merge(row,row,col,col+3, "USD",SKY_BLUE_TABLE_HEADER)
        row=2
        worksheet.write(row,col,"Supplier ",SKY_BLUE_TABLE_HEADER)
        col+=1
        worksheet.write(row,col,"Qty",SKY_BLUE_TABLE_HEADER)
        col+=1
        worksheet.write(row,col,"Purchase Price",SKY_BLUE_TABLE_HEADER)
        col+=1
        worksheet.write(row,col,"Exchange Rate",SKY_BLUE_TABLE_HEADER)
        col+=1
        
        
        row=1
        worksheet.write_merge(row,row,col,col+3, "EURO",CORAL_TABLE_HEADER)
        row=2
        worksheet.write(row,col,"Supplier ",CORAL_TABLE_HEADER)
        col+=1
        worksheet.write(row,col,"Qty",CORAL_TABLE_HEADER)
        col+=1
        worksheet.write(row,col,"Purchase Price",CORAL_TABLE_HEADER)
        col+=1
        worksheet.write(row,col,"Exchange Rate",CORAL_TABLE_HEADER)
        col+=1
        
        row=1
        worksheet.write_merge(row,row,col,col+3, "SGD",GREEN_TABLE_HEADER)
        row=2
        worksheet.write(row,col,"Supplier ",GREEN_TABLE_HEADER)
        col+=1
        worksheet.write(row,col,"Qty",GREEN_TABLE_HEADER)
        col+=1
        worksheet.write(row,col,"Purchase Price",GREEN_TABLE_HEADER)
        col+=1
        worksheet.write(row,col,"Exchange Rate",GREEN_TABLE_HEADER)
        col+=1
        row=3
        product_ids = self.env['product.product'].search([])
        for product in product_ids:
            name=product.name
            qty=product.qty_available
            cost=product.standard_price
            stock_price=qty*cost
            
            
            col=0
            worksheet.write(row, col, name,header1)
            col+=1
            worksheet.write(row, col, qty,header1)
            col+=1
            worksheet.write(row, col, cost,header1)
            col+=1
            worksheet.write(row, col, stock_price,header1)
            col+=1
            row+=1
            ex_rate_1 = cur_obj._get_conversion_rate(from_currency,to_currency1)
            ex_rate_2 = cur_obj._get_conversion_rate(from_currency,to_currency2)
            ex_rate_3 = cur_obj._get_conversion_rate(from_currency,to_currency3)
            cr.execute("select id from purchase_order where currency_id = %s and state='approved'",(3,))
            sup_usd_list=cr.fetchall()

            f_row=row
            s_row=row
            t_row=row

            if sup_usd_list and sup_usd_list!=[]:
                cr.execute("select id,order_id from purchase_order_line where product_id = %s and order_id in %s ",(product.id,tuple(sup_usd_list)))
                data_list = cr.fetchall()
                
                for order_line,order in data_list:
                    col=4
                    ord_line = pur_line_obj.browse(order_line)
                    ord = pur_obj.browse(order)

                    worksheet.write(f_row, col, ord.partner_id.name,SKY_BLUE_TABLE)
                    col+=1
                    worksheet.write(f_row, col, ord_line.product_qty,SKY_BLUE_TABLE)
                    col+=1
                    worksheet.write(f_row, col, ord_line.price_unit,SKY_BLUE_TABLE)
                    col+=1
                    worksheet.write(f_row, col, ex_rate_1,SKY_BLUE_TABLE)
                    col+=1
                    f_row+=1
                    row+=1
                    


            cr.execute("select id from purchase_order where currency_id = %s and state='approved'",(1,))
            sup_eur_list=cr.fetchall()
            if sup_eur_list and sup_eur_list != []:
                cr.execute("select id,order_id from purchase_order_line where product_id = %s and order_id in %s ",(product.id,tuple(sup_eur_list)))
                data_list_eur = cr.fetchall()
                for order_line,order in data_list_eur:
                    col=8
                    ord_line = pur_line_obj.browse(order_line)
                    ord = pur_obj.browse(order)
                    
                    worksheet.write(s_row, col, ord.partner_id.name,CORAL_TABLE)
                    col+=1
                    worksheet.write(s_row, col, ord_line.product_qty,CORAL_TABLE)
                    col+=1
                    worksheet.write(s_row, col, ord_line.price_unit,CORAL_TABLE)
                    col+=1
                    worksheet.write(s_row, col, ex_rate_2,CORAL_TABLE)
                    col+=1
                    s_row+=1
                    row+=1


            cr.execute("select id from purchase_order where currency_id = %s and state='approved'",(38,))
            sup_sgd_list=cr.fetchall()
            if sup_sgd_list and sup_sgd_list != []:
                cr.execute("select id,order_id from purchase_order_line where product_id = %s and order_id in %s ",(product.id,tuple(sup_sgd_list)))
                data_list_sgd = cr.fetchall()

                for order_line,order in data_list_sgd:
                    col=12
                    ord_line = pur_line_obj.browse(order_line)
                    ord = pur_obj.browse(order)
                    
                    worksheet.write(t_row, col, ord.partner_id.name,GREEN_TABLE)
                    col+=1
                    worksheet.write(t_row, col, ord_line.product_qty,GREEN_TABLE)
                    col+=1
                    worksheet.write(t_row, col, ord_line.price_unit,GREEN_TABLE)
                    col+=1
                    worksheet.write(t_row, col, ex_rate_3,GREEN_TABLE)
                    col+=1
                    t_row+=1
                    row+=1
            row+=1
        workbook.save(fl)
        
        fl.seek(0)
        buf = base64.encodestring(fl.read())
        ctx.update({'file':buf})
        return {
                'name': 'Attatchment',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.wiz.file',
                'target': 'new',
                'context': ctx
                }
        

class stock_wiz_file(models.TransientModel):
    _name="stock.wiz.file"

    file=fields.Binary('File')
    fname=fields.Char('File Name')


    @api.model
    def default_get(self,  fields_list):
        cr,uid,context=self.env.args

        if context is None:
            context = {}
        res = super(stock_wiz_file, self).default_get(fields_list)
        res.update({'fname': 'stock_analysis_file.xls'})

        if context.get('file'):
            res.update({'file': context['file']})
        return res

    def back(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return {
            'name': 'Stock Analysis Report',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.wiz',
            'target': 'new',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: