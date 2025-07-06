from odoo import models, fields, api

class CustomHelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    # Add your custom fields here (e.g.)
    custom_field = fields.Char(string="Custom Field")
    zone_id = fields.Char(string="Zone")
    street = fields.Char(string="Street")
    contacts = fields.Char(string="Contacts")
    comments = fields.Text(string="Comments")


    # @api.depends('partner_id')
    # def _compute_zone_and_street(self):
    #  print("Computing zone_id and street for helpdesk tickets...")
    #  for rec in self:
    #     print(f"Processing ticket for partner: {rec.partner_id.name if rec.partner_id else 'None'}")
    #     if rec.partner_id:
    #         meter = self.env['billing.meter'].search([('customer_id', '=', rec.partner_id.id)], limit=1)
    #         rec.zone_id = meter.zone_id.name if meter and meter.zone_id else False
    #         rec.street = meter.street if meter else False
            
    #     else:
    #         rec.zone_id = False
    #         rec.street = False
    #     print(f"Computed zone_id: {rec.zone_id}, street: {rec.street} for partner: {rec.partner_id.name if rec.partner_id else 'None'}")

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        print(f"Onchange triggered for partner_id: {self.partner_id.name if self.partner_id else 'None'}")
        if self.partner_id:
            meter = self.env['billing.meter'].search([('customer_id', '=', self.partner_id.id)], limit=1)
            print(f"Found meter: {meter.id if meter else 'None'} for partner: {self.partner_id.name}")
            if meter:
                print(f"Meter found: {meter.id}, Zone: {meter.zone_id.name if meter.zone_id else 'None'}, Street: {meter.street if meter.street else 'None'}")
                self.zone_id = meter.zone_id.name if meter.zone_id else False
                self.street = meter.street or False

            else:
                self.zone_id = False
                self.street = False
        else:
            self.zone_id = False
            self.street = False


    # @api.onchange('partner_id')
    # def _onchange_partner_id(self):
    #     print(f"Partner changed to: {self.partner_id.name if self.partner_id else 'None'}")
    #     """When customer is selected, fetch related meter and fill fields."""
    #     if self.partner_id:
    #         print(f"Searching for meter for customer: {self.partner_id.id}")
    #         meter = self.env['billing.meter'].search([('customer_id', '=', self.partner_id.id)], limit=1)
    #         print(f"Meter search result: {meter.id if meter else 'None'}")
    #         if meter:
    #             print(f"Found meter: {meter.id} for customer: {self.partner_id.name}")
    #             self.zone_id = meter.zone_id.name
    #             self.street = meter.street if hasattr(meter, 'street') else False
    #             print(f"Meter found: {meter.id}, Zone: {self.zone_id}, Street: {self.street}")
    #         else:
    #             self.zone_id = False
    #             self.street = False
    #     else:
    #         self.zone_id = False
    #         self.street = False


    @api.model
    def create(self, vals):
        # If user_id2 is set, assign it to user_id before creation
        if vals.get('user_id2'):
            vals['user_id'] = vals['user_id2']

        # If zone_id or street are not set, compute them from partner_id
        if vals.get('partner_id') and (not vals.get('zone_id') or not vals.get('street')):
         meter = self.env['billing.meter'].search([('customer_id', '=', vals['partner_id'])], limit=1)
         if meter:
            if not vals.get('zone_id'):
                vals['zone_id'] = meter.zone_id.name if meter.zone_id else False
            if not vals.get('street'):
                vals['street'] = meter.street or False
        print(f"Creating ticket with user_id: {vals.get('user_id')}, zone_id: {vals.get('zone_id')}, street: {vals.get('street')}")
        return super().create(vals)


    # @api.model
    # def create(self, vals):

    #     # If user_id2 is set, assign it to user_id
    #     if vals.get('user_id2'):
    #         vals['user_id'] = vals['user_id2']
    #         # vals['zone_id'] = vals.get('zone_id', False)  # Ensure zone_id is also set if needed
    #         # vals['street'] = vals.get('street', False)  # Ensure street is also set if needed
    #         # print(f"Creating ticket with user_id: {vals['user_id']}, zone_id: {vals['zone_id']}, street: {vals['street']}")
    #     return super().create(vals)
    
    # def write(self, vals):
    #     if vals.get('user_id2'):
    #         vals['user_id'] = vals['user_id2']

    #     vals['zone_id'] = vals.get('zone_id', False)  # Ensure zone_id is also set if needed
    #     vals['street'] = vals.get('street', False)  # Ensure street is also set if needed
    #     print(f"Updating ticket with user_id: {vals['user_id']}, zone_id: {vals['zone_id']}, street: {vals['street']}")
    #     return super().write(vals)
    
    
    # # Add this to your helpdesk_ticket.py model file
    # def action_open_full_form(self):
    #  """ This method handles the button click """
    #  return {
    #     'type': 'ir.actions.act_window',
    #     'name': 'New Ticket',
    #     'res_model': 'helpdesk.ticket',
    #     'view_mode': 'form',
    #     'view_id': self.env.ref('helpdesk.helpdesk_ticket_view_form').id,
    #     'target': 'current',
    #     'context': {
    #         'default_name': 'New Ticket',
    #         'default_team_id': self.env.context.get('default_team_id', False)
    #     }
    # }