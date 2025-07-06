from odoo import models, fields

class PaymentSummaryReportWizard(models.TransientModel):
    _name = 'payment.summary.report.wizard'
    _description = 'Payment Summary Report Wizard'

    date_from = fields.Date(string="From", required=True)
    date_to = fields.Date(string="To", required=True)

    def action_print_summary_report(self):
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        return self.env.ref('e_payment.action_report_payment_summary').report_action(self, data=data)