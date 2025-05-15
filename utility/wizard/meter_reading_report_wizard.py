from odoo import models, fields, api

class MeterReadingReportWizard(models.TransientModel):
    _name = 'meter.reading.report.wizard'
    _description = 'Meter Reading Report Wizard'

    zone_id = fields.Many2one('billing.zone', string='Zone')
    reading_date = fields.Date(string='Reading Date')

    def action_print_report(self):
        data = {
            'zone_id': self.zone_id.id,
            'reading_date': self.reading_date,
        }
        return self.env.ref('utility.action_meter_reading_report_pdf').report_action(self, data=data)