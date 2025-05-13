from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date

class MeterSerial(models.Model):
    _name = 'meter.serial'
    _description = 'Meter Serial Number Registry'
    _order = 'serial_number'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name="serial_number"
    _sql_constraints = [
        ('serial_unique', 'UNIQUE(serial_number)', 'This serial number is already in use!'),
    ]

    # Core Identification
    serial_number = fields.Char(
        string='Serial Number',
        required=True,
        index=True,
        tracking=True,
        help="Unique manufacturer identifier (alphanumeric, min 3 chars)"
    )
    
    # Technical Specifications
    meter_type = fields.Selection(
        [('mechanical', 'Mechanical'),
         ('digital', 'Digital'),
         ('smart', 'Smart Meter')],
        string='Meter Type',
        required=True,
        default='smart',
        tracking=True
    )
    
    
    
    model = fields.Char(
        string='Model Number',
        tracking=True,
        help="Manufacturer's model designation"
    )
    
    
    
    capacity = fields.Float(
        string='Flow Capacity (m³/h)',
        digits=(12, 2),
        tracking=True,
        help="Maximum rated flow capacity"
    )

    # Status Management
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help="Whether this serial number is available for use"
    )
    
    state = fields.Selection(
        [('available', 'Available'),
         ('assigned', 'Assigned'),
         ('retired', 'Retired')],
        string='Status',
        default='available',
        tracking=True,
        #compute='_compute_state',
        store=True
    )
    
    # Relationship Fields (Uncomment when ready)
    # meter_id = fields.One2many(
    #     'water.meter',
    #     'serial_id',
    #     string='Assigned Meter',
    #     readonly=True
    # )

    # Validation Methods
    @api.constrains('serial_number')
    def _check_serial_format(self):
        for record in self:
            if not record.serial_number or len(record.serial_number.strip()) < 3:
                raise ValidationError(_('Serial number must be at least 3 characters long'))
            if not all(c.isalnum() or c in ('-', '_') for c in record.serial_number):
                raise ValidationError(_('Only alphanumeric characters with hyphens/underscores allowed'))

    @api.constrains('manufacture_date')
    def _check_manufacture_date(self):
        for record in self:
            if record.manufacture_date and record.manufacture_date > date.today():
                raise ValidationError(_('Manufacture date cannot be in the future'))

    # Computed Fields
    # @api.depends('meter_id', 'active')
    # def _compute_state(self):
    #     for record in self:
    #         if not record.active:
    #             record.state = 'retired'
    #         elif record.meter_id:
    #             record.state = 'assigned'
    #         else:
    #             record.state = 'available'

    # Smart Methods
    # def action_view_meter(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Assigned Meter',
    #         'view_mode': 'form',
    #         'res_model': 'water.meter',
    #         'res_id': self.meter_id.id,
    #         'target': 'current'
    #     }