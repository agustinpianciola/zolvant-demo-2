# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.float_utils import float_round
from datetime import datetime
import operator as py_operator

OPERATORS = {
	'<': py_operator.lt,
	'>': py_operator.gt,
	'<=': py_operator.le,
	'>=': py_operator.ge,
	'=': py_operator.eq,
	'!=': py_operator.ne
}


class ProductTemplate(models.Model):
	_inherit = 'product.template'
	_check_company_auto = True

	secondary_uom_id = fields.Many2one('uom.uom', string="Secondary UOM")
	secondary_uom_name = fields.Char(string='Unit of Measure Name', related='secondary_uom_id.name', readonly=True)
	secondary_qty = fields.Float('Secondary Qty', compute='_compute_second_quantities', search='_search_second_qty_available',
		digits='Product Unit of Measure', compute_sudo=False)
	is_secondary_uom = fields.Boolean("Secondary Unit")

	@api.depends(
		'product_variant_ids',
		'product_variant_ids.stock_move_ids.product_qty',
		'product_variant_ids.stock_move_ids.state',
	)
	@api.depends_context('company')
	def _compute_second_quantities(self):
		res = self._compute_second_quantities_dict()
		for template in self:
			template.secondary_qty = res[template.id]['secondary_qty']
			template.update({'secondary_qty' : res[template.id]['secondary_qty']})

	def _is_cost_method_standard(self):
		return True

	def _compute_second_quantities_dict(self):
		# TDE FIXME: why not using directly the function fields ?
		variants_available = {
			p['id']: p for p in self.product_variant_ids.read(['secondary_qty'])
		}
		prod_available = {}
		for template in self:
			secondary_qty = 0
			for p in template.with_context(active_test=False).product_variant_ids:
				secondary_qty += variants_available[p.id]["secondary_qty"]
			prod_available[template.id] = {
				"secondary_qty": secondary_qty
			}
		return prod_available

	def _search_second_qty_available(self, operator, value):
		domain = [('qty_available', operator, value)]
		product_variant_ids = self.env['product.product'].search(domain)
		return [('product_variant_ids', 'in', product_variant_ids.ids)]

	def action_view_orderpoints(self):
		products = self.mapped('product_variant_ids')
		action = self.env.ref('stock.product_open_orderpoint').read()[0]
		if products and len(products) == 1:
			action['context'] = {'default_product_id': products.ids[0], 'search_default_product_id': products.ids[0]}
		else:
			action['domain'] = [('product_id', 'in', products.ids)]
			action['context'] = {}
		return action

	def action_open_secondary_quants(self):
		return self.with_context(active_test=False).product_variant_ids.filtered(lambda p: p.active or p.second_qty_available != 0).action_open_secondary_quants()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4::