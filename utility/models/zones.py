from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class Zones(models.Model):
    _name = 'billing.zone'
    _description = 'Utility Zone'
    _order = 'name'
    
    name = fields.Char(
        string='Zone Name',
        required=True,
        help='Administrative or geographical zone name')
    
    code = fields.Char(
        string='Zone Code',
        required=True,
        help='Short code for the zone (e.g., ZN-001)')
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to archive this zone')
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True)
    collector_id = fields.Many2one(
        'res.users',
        string='Zone Collector',
        help='User responsible for collecting meter readings in this zone'
    )
    
    # meter_ids = fields.One2many(
    #     'water.meter',
    #     'zone_id',
    #     string='Meters in this Zone')
    
    # meter_count = fields.Integer(
    #     string='Meter Count',
    #     compute='_compute_meter_count')
    
    # notes = fields.Text(string='Internal Notes')
    
    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 
         'Zone code must be unique per company!'),
    ]
    
    # @api.depends('meter_ids')
    # def _compute_meter_count(self):
    #     for zone in self:
    #         zone.meter_count = len(zone.meter_ids)
    
    @api.constrains('code')
    def _check_code_format(self):
        for zone in self:
            if not zone.code or len(zone.code.strip()) < 1:
                raise ValidationError(_('Zone code must be at least 3 characters long'))