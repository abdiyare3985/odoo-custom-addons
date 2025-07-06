from odoo import models, fields

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    user_id = fields.Many2one(
    'res.users',
    string='Assigned to',
    #domain="[('groups_id', 'in', [ref('base.group_portal')])]",
)