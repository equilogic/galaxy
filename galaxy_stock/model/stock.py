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
