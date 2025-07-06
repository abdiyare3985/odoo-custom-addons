from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    #meter_id = fields.Integer(string="Meter ID")
    meter_id = fields.Many2one(
        'billing.meter',
        string='Meter ID',
       # compute='_compute_meter_fields',
        #store=True
    )
    meter_name = fields.Integer(string="Meter Name")
    zone_id = fields.Many2one('billing.zone', string='Zone')


    def action_open_create_customer_meter_wizard(self):
        print("*******************************************")
        # Open the wizard to create a customer and meter
        return {
        'type': 'ir.actions.act_window',
        'name': 'Create Customer and Meter',
        'res_model': 'create.customer.meter.wizard',
        'view_mode': 'form',
        'target': 'new',  # optional but typical for wizards
        'context': {
            'default_lead_id': self.id,
            'default_customer_name': self.partner_name or self.name,
            'default_phone': self.phone,
            'default_email': self.email_from,
            'default_zone_id': self.zone_id.id if self.zone_id else False,
        },
    }