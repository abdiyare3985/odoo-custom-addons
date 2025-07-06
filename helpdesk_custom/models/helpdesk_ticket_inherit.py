from odoo import models, fields

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    user_id2 = fields.Many2one(
    'res.users',
    string='Assigned to',
    #domain="[('groups_id', 'in', [ref('base.group_portal')])]",
    
)
    complaint_type = fields.Selection([
        ('leak', 'Leak'),
        ('no_water', 'No Water'),
        ('other', 'Other'),
    ], string="Complaint Type")

    # def action_open_custom_ticket_form(self):
    #     """ Opens a custom ticket form in a popup """
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Custom Ticket Form',
    #         'res_model': 'helpdesk.ticket',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('your_module.view_custom_ticket_form').id,
    #         'target': 'new',  # Opens in a popup/dialog
    #         'context': {'default_name': 'New Custom Ticket'},  # Set defaults
    #     }
    
    # def action_confirm(self):
    #  """ Handle custom form submission """
    #  self.ensure_one()
    # # Add any validation logic here
    #  if not self.name:
    #     raise UserError("Ticket title is required!")
    
    # # Return to kanban view after creation
    #  return {
    #     'type': 'ir.actions.act_window',
    #     'view_mode': 'kanban,tree,form',
    #     'res_model': 'helpdesk.ticket',
    #     'target': 'current',  # Return to main view
    # }