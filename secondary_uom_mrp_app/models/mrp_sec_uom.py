# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round as round
from odoo.addons import decimal_precision as dp

class MRPBomline(models.Model):
	_inherit = 'mrp.bom.line'

	secondary_uom_id = fields.Many2one('uom.uom', string="Secondary UOM")
	secondary_quantity = fields.Float('Secondary Qty')

	@api.onchange('product_qty')
	def change_secondary_qty(self):
		if self.bom_id.product_tmpl_id.is_secondary_uom:
			for line in self.bom_id.bom_line_ids:
				uom_quantity = self.bom_id.product_tmpl_id.uom_id._compute_quantity(self.product_qty, self.bom_id.product_tmpl_id.secondary_uom_id, rounding_method='HALF-UP')
				line.secondary_uom_id = self.bom_id.product_tmpl_id.secondary_uom_id
				line.secondary_quantity = uom_quantity

	@api.depends('product_id', 'product_qty')
	def _mrp_quantity_secondary_compute(self):
		for order in self:
			if order.product_id.is_secondary_uom:
				uom_quantity = order.product_id.uom_id._compute_quantity(order.product_qty, order.product_id.secondary_uom_id, rounding_method='HALF-UP')
				order.secondary_uom_id = order.product_id.secondary_uom_id
				order.secondary_quantity = uom_quantity	


class MRPProduction(models.Model):
	_inherit = 'mrp.production'

	def action_confirm(self):
		res = super(MRPProduction, self).action_confirm()
		if self.env.user.has_group('secondary_uom_mrp_app.group_secondary_uom'):
			for order in self.move_raw_ids:
				uom_quantity = order.product_id.uom_id._compute_quantity(order.product_uom_qty, self.product_id.secondary_uom_id, rounding_method='HALF-UP')
				order.write({'secondary_uom_id':self.product_id.secondary_uom_id.id,
				 'secondary_quantity':uom_quantity})
		else:
			return res


# add  Secondary UOM,Secondary Qty,Secondary Reserved Qty and Secondary Consumed Qty fields in mrp order  line with compute uom
class MRPSmodel(models.Model):
	_inherit = 'stock.move'

	secondary_uom_id = fields.Many2one('uom.uom', compute='_quantity_secondary_compute', string="Secondary UOM", store=True, readonly=True)
	secondary_quantity = fields.Float('Secondary Qty', compute='_quantity_secondary_compute', digits=dp.get_precision('Product Unit of Measure'),store=True, readonly=True)
	secondary_quantity_reserved = fields.Float('Secondary Reserved Qty')
	secondary_quantity_done = fields.Float('Secondary Consumed Qty')

	@api.depends('product_id', 'product_uom_qty')
	def _quantity_secondary_compute(self):
		for order in self:
			if order.product_id.is_secondary_uom:
				uom_quantity = order.product_id.uom_id._compute_quantity(order.product_uom_qty, order.product_id.secondary_uom_id, rounding_method='HALF-UP')
				order.write({'secondary_uom_id' : order.product_id.secondary_uom_id.id})
				order.write({'secondary_quantity' : order.product_uom_qty})
			else:
				order.update({'secondary_uom_id' : False})
				order.update({'secondary_quantity' : 0.0})

	@api.depends('product_id', 'reserved_availability')
	def _reserved_secondary_compute(self):
		for order in self:
			if order.product_id.is_secondary_uom:
				uom_quantity = order.product_id.uom_id._compute_quantity(order.reserved_availability, order.product_id.secondary_uom_id, rounding_method='HALF-UP')
				order.update({'secondary_uom_id' : order.product_id.secondary_uom_id})
				order.update({'secondary_quantity_reserved' : uom_quantity})
			else:
				order.update({'secondary_uom_id' : False})
				order.update({'secondary_quantity_reserved' : 0.0})

	@api.depends('product_id', 'quantity_done')
	def _quantity_done_econdary_compute(self):
		for order in self:
			if order.product_id.is_secondary_uom:
				uom_quantity = order.product_id.uom_id._compute_quantity(order.quantity_done, order.product_id.secondary_uom_id, rounding_method='HALF-UP')
				order.update({'secondary_uom_id' : order.product_id.secondary_uom_id})
				order.update({'secondary_quantity_done' : uom_quantity})
			else:
				order.update({'secondary_uom_id' : False})
				order.update({'secondary_quantity_done' : 0.0})

	def action_confirm(self):
		res = super(MRPSmodel, self).action_confirm()
		
		if self.env.user.has_group('secondary_uom_mrp_app.group_secondary_uom'):
			uom_quantity = self.product_id.uom_id._compute_quantity(self.quantity_done, self.product_id.secondary_uom_id, rounding_method='HALF-UP')
			self.update({'secondary_uom_id' : self.product_id.secondary_uom_id})
			self.update({'secondary_quantity_done' : uom_quantity})
		else:
			return res
