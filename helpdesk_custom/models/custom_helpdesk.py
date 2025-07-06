from odoo import models, fields, api

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'  # Inherits from the original model
    
    # Custom Fields
    custom_reference = fields.Char(
        string="Reference Code",
        help="Internal reference for tracking",
    )
    
    priority_notes = fields.Text(
        string="Priority Justification",
        help="Explain why this ticket is high priority",
    )
    
    # Optional: Override default methods
    @api.model
    def default_get(self, fields):
        """Set default values when creating a new ticket."""
        res = super().default_get(fields)
        res.update({
            'custom_reference': "TICKET-" + fields.Datetime.now(),  # Auto-generate ref
            'priority': '2',  # Default priority = High
        })
        return res