from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    is_technitian = fields.Boolean(string="Is Technician")
    is_meterreader = fields.Boolean(string="Is Meter Reader")