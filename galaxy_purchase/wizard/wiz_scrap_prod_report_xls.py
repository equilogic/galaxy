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

class scrap_product_wiz_report(models.TransientModel):
    _name="scrap.product"

    
    @api.multi
    def print_scrap_prod_report(self):

        cr,uid,context = self.env.args
        all_product = {}
        location_ids = self.env['stock.location'].search([('scrap_location','=',True)])
        
        for loc_id in location_ids:
            stock_move_ids = self.env['stock.move'].search([('location_dest_id','=',loc_id.id)])
            for stock_id in stock_move_ids:
                if stock_id.product_id.id in all_product:
                    all_product[stock_id.product_id.id].update({'qty': all_product[stock_id.product_id.id].get('qty') + stock_id.product_uom_qty})
                else:
                    all_product[stock_id.product_id.id] = {'prodct_name': stock_id.product_id.name,
                                                                'qty': stock_id.product_uom_qty}
            fl = StringIO()
            ctx=dict(context)
            
            row=1
                
            workbook = xlwt.Workbook()
            worksheet = workbook.add_sheet('New Sheet')

            pattern = xlwt.Pattern()
            font = xlwt.Font()
            font.bold = True
            main_header = xlwt.easyxf('font: bold 1, height 360, color coral; align: horiz center,vert center;')
            header1 = xlwt.easyxf('font: bold 1, height 230, color green; align: horiz center,vert center ,wrap 1;borders :top hair, bottom hair,left hair, right hair, bottom_color aqua,top_color black;')
            header2 = xlwt.easyxf('align: horiz center,vert center ;borders :top hair, bottom hair,left hair, right hair,')
            
            worksheet.row(1).height=500
            worksheet.col(0).width=12000
            worksheet.col(1).width=5000

            worksheet.row(0).height = 600
            worksheet.write_merge(0, 0, 0, 1, 'SCRAP PRODUCT REPORT', main_header)

            worksheet.write(row, 0, "Product Name",header1)
            worksheet.write(row, 1, "Product Qty",header1)
        
            if all_product:
                row=2
                for key,value in all_product.items():
                    worksheet.write(row, 0, value.get('prodct_name'),header2)
                    worksheet.write(row, 1, value.get('qty'),header2)
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
                'res_model': 'scrap.product.wiz.file',
                'target': 'new',
                'context': ctx
                }


class scrap_prod_wiz_file(models.TransientModel):
    _name="scrap.product.wiz.file"

    file=fields.Binary('File')
    fname=fields.Char('File Name')

    @api.model
    def default_get(self,  fields):
        cr,uid,context=self.env.args

        if context is None:
            context = {}
        res = super(scrap_prod_wiz_file, self).default_get(fields)
        res.update({'fname': 'scrap_product_report_file.xls'})

        if context.get('file'):
            res.update({'file': context['file']})
        return res

    file = fields.Binary('File')
    name = fields.Char(string='File Name', size=64)

    def back(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return {
            'name': 'Scrap Product Report',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'scrap.product',
            'target': 'new',
        }