from odoo import models, fields, api

class PaymentReportWizard(models.TransientModel):
    _name = 'payment.report.wizard'
    _description = 'Payment Report Wizard'

    date_from = fields.Date(string="From", required=True)
    date_to = fields.Date(string="To", required=True)

    def action_print_report(self):
        print("Action triggered to print payment report.")
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }

        print("Generating payment report from {} to {}".format(self.date_from, self.date_to))
        return self.env.ref('e_payment.action_report_payment_list').report_action(self, data=data)
    
    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     data = data or {}
    #     print("Fetching report values for payment report with data:", data)
    #     payments = self.env['account.payment'].search([
    #         ('date', '>=', data['date_from']),
    #         ('date', '<=', data['date_to']),
    #     ])
    #     print("Found {} payments in the specified date range.".format(len(payments)))
    #     return {
    #         'doc_ids': payments.ids,
    #         'doc_model': 'account.payment',
    #         'docs': payments,
    #         'data': data,
    #     }