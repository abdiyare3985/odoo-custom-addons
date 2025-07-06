from odoo import models, fields

class CustomHelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # Add your custom fields here (e.g.)
    custom_field = fields.Char(string="Custom Field")