from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class MeterDiscount(models.Model):
    _name = 'meter.discount'
    _description = 'Water Meter Discount'
    _order = 'name'
    
    name = fields.Char(
        string='Discount Name',
        required=True,
        help="Descriptive name for this discount (e.g., Senior Citizen, Bulk Discount)"
    )
    
    percentage = fields.Float(
        string='Discount Percentage',
        required=True,
        digits=(5, 2),  # Allows for 100.00% max with 2 decimal places
        help="Percentage discount to apply (e.g., 10.5 for 10.5% discount)",
        default=0.0
    )
    
  
    description = fields.Text(
        string='Description',
        help="Detailed explanation of discount terms and conditions"
    )
    
 