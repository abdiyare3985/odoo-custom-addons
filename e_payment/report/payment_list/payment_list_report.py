from odoo import models, api

class ReportPaymentList(models.AbstractModel):
    _name = 'report.e_payment.report_payment_list'  # <module>.<template_id>
    _description = 'Payment List Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        print("Generating payment list report with data:", data)
        payments = self.env['account.payment'].search([
            ('date', '>=', data.get('date_from')),
            ('date', '<=', data.get('date_to')),
        ])
        print("Found {} payments in the specified date range.".format(len(payments)))
        return {
            'doc_ids': payments.ids,
            'doc_model': 'account.payment',
            'docs': payments,
            'data': data,
        }