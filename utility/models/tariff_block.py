from odoo import models, fields, api

class WaterTariffBlock(models.Model):
    _name = 'billing.tariff.block'
    _description = 'billing Tariff Consumption Block'
    _order = 'sequence, limit asc'
    
    product_id = fields.Many2one(
        'product.template',
        string='Tariff Plan',
        required=True
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Determines order of block application"
    )
    
    limit = fields.Float(
        string='Upper Limit (m³)',
        digits=(12, 3),
        default=0,
        help="0 means unlimited (last block)"
    )
    
    rate = fields.Float(
        string='Rate per m³',
        digits=(12, 4),
        required=True
    )
    
    name = fields.Char(
        string='Description',
        compute='_compute_name',
        store=True
    )
    
    @api.depends('limit', 'rate')
    def _compute_name(self):
        for block in self:
            if block.limit > 0:
                block.name = f"Up to {block.limit}m³ @ {block.rate}/m³"
            else:
                block.name = f"Above previous limit @ {block.rate}/m³"