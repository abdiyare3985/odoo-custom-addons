from odoo import models

class MeterReport(models.AbstractModel):
    _name = 'report.utility.meter_list_report_template'
    _description = 'Meter Report'

    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('zone_id'):
            domain.append(('zone_id', '=', data['zone_id']))
        if data.get('status'):
            domain.append(('status', '=', data['status']))
        docs = self.env['billing.meter'].search(domain)
        return {
            'docs': docs,
            'data': data,
        }