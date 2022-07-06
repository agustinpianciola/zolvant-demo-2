from odoo import api, fields, models, tools, _
from odoo.addons import decimal_precision as dp


class MRPreport(models.Model):
	_inherit = 'mrp.production'

	secondary_quantity = fields.Float("Secondary Qty",compute='_mrp_quantity_secondary_compute', digits=dp.get_precision('Product Unit of Measure'), store=True)
	
	@api.depends('product_id', 'product_qty')
	def _mrp_quantity_secondary_compute(self):
		for order in self:
			if order.product_id.is_secondary_uom:
				uom_quantity = order.product_id.uom_id._compute_quantity(order.product_qty, order.product_id.secondary_uom_id, rounding_method='HALF-UP')
				order.secondary_quantity = uom_quantity	
	def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
		with_ = ("WITH %s" % with_clause) if with_clause else ""
		groupby_ = """
				l.secondary_quantity,
				l.product_id,	
				l.order_id,
				t.uom_id,
				t.categ_id,
				s.name,
				s.date_order,
				s.confirmation_date,
				s.partner_id,
				s.user_id,
				s.state,
				s.company_id,
				s.pricelist_id,
				s.analytic_account_id,
				s.team_id,
				p.product_tmpl_id,
				partner.country_id,
				partner.commercial_partner_id,
				l.discount,
				s.id %s
			""" % (groupby)
		return '%s (SELECT %s FROM %s WHERE l.product_id IS NOT NULL GROUP BY %s)' % (with_, select_, from_, groupby_)	

