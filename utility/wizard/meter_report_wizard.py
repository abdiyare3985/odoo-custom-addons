from odoo import models, fields, api

class MeterReadingReportWizard(models.TransientModel):
    _name = 'meter.report.wizard'
    _description = 'Meter Report Wizard'

    zone_id = fields.Many2one('billing.zone', string='Zone')
    status = fields.Selection(
        [('connected', 'Connected'),
         ('disconnected', 'Disconnected'),
         ('blocked', 'Blocked')],
        string='Connection Status',
        default='connected',
        tracking=True,
        index=True
    )

    def action_print_meter_report(self):
        data = {
            'zone_id': self.zone_id.id,
            'status': self.status,
        }
        #return self.env.ref('utility.action_meter_report_pdf').report_action(self, data=data).update({'target': 'new'})
        action = self.env.ref('utility.action_meter_report_pdf').report_action(self, data=data)
        action['target'] = 'new'
        return action