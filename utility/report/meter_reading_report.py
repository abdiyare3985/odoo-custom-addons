from odoo import models

class MeterReadingReport(models.AbstractModel):
    _name = 'report.utility.meter_reading_report_template'
    _description = 'Meter Reading Report'

    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('zone_id'):
            domain.append(('meter_id.zone_id', '=', data['zone_id']))
        if data.get('reading_date'):
            domain.append(('reading_date', '=', data['reading_date']))
        docs = self.env['meter.reading'].search(domain)
        return {
            'docs': docs,
            'data': data,
        }