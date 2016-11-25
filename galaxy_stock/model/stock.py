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

from openerp import models, fields, api, _

class stock_picking(models.Model):

    _inherit = "stock.picking"

    @api.multi
    @api.depends('move_lines')
    def _compute_move_qty(self):
        for picking_rec in self:
            if picking_rec.move_lines:
                qty = 0.0
                for mov_rec in picking_rec.move_lines:
                    qty += mov_rec.product_uom_qty
            picking_rec.prod_uom_qty = qty

    prod_uom_qty = fields.Float('Quantity', compute="_compute_move_qty")
    active = fields.Boolean('Active', default=True, help="If the active field is set to False, it will allow you to hide the picking without removing it.")
    


class stock_move(models.Model):
    _inherit = "stock.move"
    
    item_desc = fields.Char('Item Description')
    
    @api.multi
    def onchange_product_id(self, prod_id=False, loc_id=False, loc_dest_id=False, partner_id=False):
        """ On change of product id, if finds UoM, UoS, quantity and UoS quantity.
        @param prod_id: Changed Product id
        @param loc_id: Source location id
        @param loc_dest_id: Destination location id
        @param partner_id: Address id of partner
        @return: Dictionary of values
        """
        res={}
        if prod_id:
            prod=self.env['product.product'].browse(prod_id)
            res = super(stock_move,self).onchange_product_id(prod_id=prod_id, loc_id=loc_id, loc_dest_id=loc_dest_id, partner_id=partner_id)
            res['value'].update({'item_desc':prod.name})
        return res
    
    @api.model  
    def create(self, vals):
        if not vals.get('item_desc'):
            product_id = vals.get('product_id', False)
            if product_id:
                product_data =  self.env['product.product'].browse(product_id)
                vals.update({'item_desc': product_data.name})
        return super(stock_move, self).create(vals)
    
    
