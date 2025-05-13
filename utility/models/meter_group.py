from odoo import models, fields, api

class MeterGroup(models.Model):
    _name = 'meter.group'
    _description = 'Water Meter Group'
    
    name = fields.Char(string='Group Name', required=True)
    code = fields.Char(string='Group Code', required=True)
    description = fields.Text(string='Description')
    # company_id = fields.Many2one(
    #     'res.company', 
    #     string='Company',
    #     default=lambda self: self.env.company
    # )
    # meter_ids = fields.One2many(
    #     'water.meter',
    #     'group_id',
    #     string='Meters in Group'
    # )
    # meter_count = fields.Integer(
    #     string='Meter Count',
    #     compute='_compute_meter_count'
    # )
    
    # _sql_constraints = [
    #     ('code_uniq', 'unique(code, company_id)', 'Group code must be unique per company!'),
    # ]
    
    # @api.depends('meter_ids')
    # def _compute_meter_count(self):
    #     for group in self:
    #         group.meter_count = len(group.meter_ids)