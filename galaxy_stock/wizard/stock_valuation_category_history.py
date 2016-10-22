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
from datetime import datetime
from openerp import tools
from openerp import api, fields, models, _

class wizard_audit_product_history(models.TransientModel):

    _name = 'wizard.audit.product.history'

    _description = 'Wizard that opens stock audit by product category table'

    date = fields.Datetime('Date', required=True, default=datetime.now())

    @api.multi
    def open_table(self):
        cr, uid, context = self.env.args
        data = self.read()[0]
        ctx = context.copy()
        ctx['history_date'] = data['date']
        ctx['search_default_group_by_category'] = True
        return {
            'domain': "[('date', '<=', '" + data['date'] + "')]",
            'name': _('Stock Audit By Product Category'),
            'view_type': 'form',
            'view_mode': 'tree,graph',
            'res_model': 'stock.audit.category.history',
            'type': 'ir.actions.act_window',
            'context': ctx,
        }


class stock_audit_category_history(models.Model):
    _name = 'stock.audit.category.history'
    _auto = False
    _order = 'date asc'

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):
        res = super(stock_audit_category_history, self).read_group(cr, uid, domain, fields, groupby, offset=offset, limit=limit, context=context, orderby=orderby, lazy=lazy)
        if context is None:
            context = {}
        date = context.get('history_date', datetime.now())
        if 'inventory_value' in fields:
            group_lines = {}
            for line in res:
                domain = line.get('__domain', domain)
                group_lines.setdefault(str(domain), self.search(cr, uid, domain, context=context))
            line_ids = set()
            for ids in group_lines.values():
                for product_id in ids:
                    line_ids.add(product_id)
            line_ids = list(line_ids)
            lines_rec = {}
            if line_ids:
                cr.execute('SELECT id, product_id, price_unit_on_quant, company_id, quantity FROM stock_history WHERE id in %s', (tuple(line_ids),))
                lines_rec = cr.dictfetchall()
            lines_dict = dict((line['id'], line) for line in lines_rec)
            product_ids = list(set(line_rec['product_id'] for line_rec in lines_rec))
            products_rec = self.pool['product.product'].read(cr, uid, product_ids, ['cost_method', 'product_tmpl_id'], context=context)
            products_dict = dict((product['id'], product) for product in products_rec)
            cost_method_product_tmpl_ids = list(set(product['product_tmpl_id'][0] for product in products_rec if product['cost_method'] != 'real'))
            histories = []
            if cost_method_product_tmpl_ids:
                cr.execute('SELECT DISTINCT ON (product_template_id, company_id) product_template_id, company_id, cost FROM product_price_history WHERE product_template_id in %s AND datetime <= %s ORDER BY product_template_id, company_id, datetime DESC', (tuple(cost_method_product_tmpl_ids), date))
                histories = cr.dictfetchall()
            histories_dict = {}
            for history in histories:
                histories_dict[(history['product_template_id'], history['company_id'])] = history['cost']
            for line in res:
                inv_value = 0.0
                lines = group_lines.get(str(line.get('__domain', domain)))
                for line_id in lines:
                    line_rec = lines_dict[line_id]
                    product = products_dict[line_rec['product_id']]
                    if product['cost_method'] == 'real':
                        price = line_rec['price_unit_on_quant']
                    else:
                        price = histories_dict.get((product['product_tmpl_id'][0], line_rec['company_id']), 0.0)
                    inv_value += price * line_rec['quantity']
                line['inventory_value'] = inv_value
        return res

    @api.multi
    def _get_inventory_value(self):
        cr, uid, context = self.env.args
        date = context.get('history_date')
        for line in self:
            if line.product_id.cost_method == 'real':
                line.inventory_value = line.quantity * line.price_unit_on_quant
            else:
                line.inventory_value = line.quantity * self.env["product.template"].get_history_price(line.product_id.product_tmpl_id.id, line.company_id.id, date=date)
        return True


    move_id = fields.Many2one('stock.move', 'Stock Move', required=True)
    location_id = fields.Many2one('stock.location', 'Location', required=True)
    company_id = fields.Many2one('res.company', 'Company')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_categ_id = fields.Many2one('product.category', 'Product Category', required=True)
    quantity = fields.Float('Product Quantity')
    date = fields.Datetime('Operation Date')
    price_unit_on_quant = fields.Float('Value', group_operator='avg')
    inventory_value =  fields.Float(compute='_get_inventory_value', string="Inventory Value", readonly=True)
    source = fields.Char('Source')


    def init(self, cr):
        tools.drop_view_if_exists(cr, 'stock_audit_category_history')
        cr.execute("""
            CREATE OR REPLACE VIEW stock_audit_category_history AS (
              SELECT MIN(id) as id,
                move_id,
                location_id,
                company_id,
                product_id,
                product_categ_id,
                SUM(quantity) as quantity,
                date,
                COALESCE(SUM(price_unit_on_quant * quantity) / NULLIF(SUM(quantity), 0), 0) as price_unit_on_quant,
                source
                FROM
                ((SELECT
                    stock_move.id AS id,
                    stock_move.id AS move_id,
                    dest_location.id AS location_id,
                    dest_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.categ_id AS product_categ_id,
                    quant.qty AS quantity,
                    stock_move.date AS date,
                    quant.cost as price_unit_on_quant,
                    stock_move.origin AS source
                FROM
                    stock_move
                JOIN
                    stock_quant_move_rel on stock_quant_move_rel.move_id = stock_move.id
                JOIN
                    stock_quant as quant on stock_quant_move_rel.quant_id = quant.id
                JOIN
                   stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                JOIN
                    product_product ON product_product.id = stock_move.product_id
                JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                WHERE quant.qty>0 AND stock_move.state = 'done' AND dest_location.usage in ('internal', 'transit')
                  AND (
                    not (source_location.company_id is null and dest_location.company_id is null) or
                    source_location.company_id != dest_location.company_id or
                    source_location.usage not in ('internal', 'transit'))
                ) UNION ALL
                (SELECT
                    (-1) * stock_move.id AS id,
                    stock_move.id AS move_id,
                    source_location.id AS location_id,
                    source_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.categ_id AS product_categ_id,
                    - quant.qty AS quantity,
                    stock_move.date AS date,
                    quant.cost as price_unit_on_quant,
                    stock_move.origin AS source
                FROM
                    stock_move
                JOIN
                    stock_quant_move_rel on stock_quant_move_rel.move_id = stock_move.id
                JOIN
                    stock_quant as quant on stock_quant_move_rel.quant_id = quant.id
                JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                JOIN
                    stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                JOIN
                    product_product ON product_product.id = stock_move.product_id
                JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                WHERE quant.qty>0 AND stock_move.state = 'done' AND source_location.usage in ('internal', 'transit')
                 AND (
                    not (dest_location.company_id is null and source_location.company_id is null) or
                    dest_location.company_id != source_location.company_id or
                    dest_location.usage not in ('internal', 'transit'))
                ))
                AS foo
                GROUP BY move_id, location_id, company_id, product_id, product_categ_id, date, source
            )""")
