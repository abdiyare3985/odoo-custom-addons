from odoo import models, fields, api

class WaterTariffRange(models.Model):
    _name = 'billing.tariff.range'
    _description = 'billing Tariff Consumption Range'
    _order = 'sequence, min_value asc'
    
    product_id = fields.Many2one('product.template', string='Tariff Plan', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    min_value = fields.Float(string='Minimum (m³)', digits=(12, 3), required=True)
    max_value = fields.Float(string='Maximum (m³)', digits=(12, 3))
    rate = fields.Float(string='Rate', digits=(12, 4), required=True)
    name = fields.Char(string='Description', compute='_compute_name', store=True)
    
    @api.depends('min_value', 'max_value', 'rate')
    def _compute_name(self):
        for r in self:
            if r.max_value:
                r.name = f"{r.min_value}-{r.max_value}m³ @ {r.rate}"
            else:
                r.name = f"Above {r.min_value}m³ @ {r.rate}"