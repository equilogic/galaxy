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

from openerp import models, fields, api,SUPERUSER_ID
import re
from openerp.osv import expression


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    brand = fields.Many2one('brand.brand', string="Brand")
    flavor = fields.Many2one('flavor.flavor', string="Flavor")
    gender = fields.Selection([('male', "Male"), ('female', "Female")], default='male')
    origin_ids = fields.One2many('origin.origin', 'product_id', string="Origin")
    non_invenotry_item =  fields.Boolean('Non Inventory Item')
    manufacture_by =  fields.Text('Manufacture By')
    origin_data = fields.Char('Origin')
    qty_on_hand = fields.Integer(compute = '_get_on_hand_qty', string='Qty Available')
    print_manufacture =  fields.Boolean('Print on Report')
    
    @api.multi
    @api.depends('qty_on_hand')
    def _get_on_hand_qty(self):
        """
            This method calculate aqy available
        """
        for cost in self:
            cost.qty_on_hand = cost.qty_available    

    @api.onchange('non_invenotry_item')
    def onchange_currency_id(self):
        for rec in self:
            curr = rec.non_invenotry_item
            if curr:
                rec.type = 'service'
            else:
                rec.type = 'product'
                    
#    @api.v7
#    def _check_product_code_unique(self, cr, uid, ids, context=None):
#        for product in self.browse(cr, uid, ids, context=context):
#            product = self.search(cr, uid, [('cust_code', '=', partner.cust_code),
#                                                 ('customer','=', True)])
#            if partners and len(partners) > 1:
#                return False
#        return True


class container_container(models.Model):
    _name = 'container.container'
    _description = "Containers"

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')


class brand(models.Model):
    _name = 'brand.brand'
    _description = "Product Brand"

    name = fields.Char('Name')
    code = fields.Char('Code')


class flavor(models.Model):
    _name = 'flavor.flavor'
    _description = "Product Flavor"

    name = fields.Char('Name')
    code = fields.Char('Code')


class origin(models.Model):
    _name = 'origin.origin'

    name = fields.Many2one('res.country',required=True)
    code = fields.Char('Code',related='name.code',readonly=True)
    qty = fields.Char('Qty')
    product_id = fields.Many2one('product.template',readonly=True)


    @api.multi
    def name_get(self):
        origin = []
        for onq in self:
            display_str = ''
            if onq.qty:
                display_str += '[' + str(onq.qty) + ']'
            display_str += onq.name.name 
            dept_tuple = (onq.id,display_str)
            origin.append(dept_tuple)
        return origin


class product_product(models.Model):
    _inherit = 'product.product'

    newly_imp_prod = fields.Boolean('Newly Create product')
    partner_ref = fields.Char(compute="_product_partner_ref",string="Customer ref")

    @api.multi
    def _product_partner_ref(self):
        for prod in self:
            prod.partner_ref = prod.name

    def name_get(self, cr, user, ids, context=None):
        if context is None:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not len(ids):
            return []

        def _name_get(d):
            name = d.get('name','')
            code = context.get('display_default_code', True) and d.get('default_code',False) or False
            if code:
                name = '%s %s' % (code, name)
            return (d['id'], name)

        partner_id = context.get('partner_id', False)
        if partner_id:
            partner_ids = [partner_id, self.pool['res.partner'].browse(cr, user, partner_id, context=context).commercial_partner_id.id]
        else:
            partner_ids = []

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights(cr, user, "read")
        self.check_access_rule(cr, user, ids, "read", context=context)

        result = []
        for product in self.browse(cr, SUPERUSER_ID, ids, context=context):
            variant = ", ".join([v.name for v in product.attribute_value_ids])
            name = variant and "%s (%s)" % (product.name, variant) or product.name
            sellers = []
            if partner_ids:
                sellers = filter(lambda x: x.name.id in partner_ids, product.seller_ids)
            if sellers:
                for s in sellers:
                    seller_variant = s.product_name and (
                        variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                        ) or False
                    mydict = {
                              'id': product.id,
#                              'name': seller_variant or name,
                              'default_code': s.product_code or product.default_code,
#                              'qty': product.qty_on_hand
                              }
                    result.append(_name_get(mydict))
            else:
                mydict = {
                          'id': product.id,
#                          'name': product.qty_available,
                          'default_code': product.default_code,
                          }
                result.append(_name_get(mydict))
        return result
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', limit=80, context=None):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            ids = []
            if operator in positive_operators:
                ids = self.search(cr, user, [('default_code', '=', name)] + args, limit=limit, context=context)
                if not ids:
                    ids = self.search(cr, user, [('ean13', '=', name)] + args, limit=limit, context=context)
            if not ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                ids = self.search(cr, user, args + [('default_code', operator, name)], limit=limit, context=context)
                if not limit or len(ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    limit2 = (limit - len(ids)) if limit else False
                    ids += self.search(cr, user, args + [('name', operator, name), ('id', 'not in', ids)], limit=limit2, context=context)
            elif not ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                ids = self.search(cr, user, args + ['&', ('default_code', operator, name), ('name', operator, name)], limit=limit, context=context)
            if not ids and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('default_code', '=', res.group(2))] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('brand.name', operator, name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, user, [('flavor.name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result

class landed_cost(models.Model):
    _name='landed.cost'
    
    name = fields.Char('Name')
    amount = fields.Float('Amount')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
