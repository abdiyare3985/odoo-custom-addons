from odoo import models, api
from datetime import datetime

class ReportPaymentSummary(models.AbstractModel):
    _name = 'report.e_payment.report_payment_summary'
    _description = 'Payment Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        payments = self.env['account.payment'].read_group(
            [('date', '>=', data.get('date_from')),
             ('date', '<=', data.get('date_to'))],
            ['date', 'amount:sum'],
            ['date'],
            orderby='date'
        )
        return {
            'doc_ids': [],
            'doc_model': 'account.payment',
            'docs': payments,
            'data': data,
        }
    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     data = data or {}
    #     payments = self.env['account.payment'].read_group(
    #         [('date', '>=', data.get('date_from')),
    #          ('date', '<=', data.get('date_to'))],
    #         ['date:month', 'amount:sum'],  # Group by month
    #         ['date:month'],
    #         orderby='date:month'
    #     )
    #     # Use the date as-is for month-year format
    #     for p in payments:
    #         p['date_str'] = p['date']  # No need to parse, already 'Month Year'
    #     return {
    #         'doc_ids': [],
    #         'doc_model': 'account.payment',
    #         'docs': payments,
    #         'data': data,
    #     }