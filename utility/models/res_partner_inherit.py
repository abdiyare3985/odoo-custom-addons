from odoo import models, fields, api

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'
    # _rec_names_search=['name', 'billing_account']
    
    billing_account = fields.Char(string="Billing Account")