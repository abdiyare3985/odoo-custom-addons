from odoo import models

class StatementReport(models.AbstractModel):
    _name = 'report.utility.billing_meter_statement_report'
    _description = 'Billing Meter Statement Report'

    def _get_report_values(self, docids, data=None):
        # Fetch the wizard record
        wizard = self.env['billing.meter.wizard'].browse(docids)

        # Ensure the wizard record exists
        if not wizard:
            return {}

        # Domain to get all relevant transactions
        domain = [
            ('partner_id', '=', wizard.partner_id.id),
            ('date', '>=', wizard.start_date),  # Start date condition
            ('date', '<=', wizard.end_date),    # End date condition
            ('parent_state', '=', 'posted'),
            ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable'])
        ]

        # Calculate opening balance (all transactions before start_date)
        opening_domain = [
            ('partner_id', '=', wizard.partner_id.id),
            ('date', '<', wizard.start_date),
            ('parent_state', '=', 'posted'),
            ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable'])
        ]
        opening_balance = sum(self.env['account.move.line'].search(opening_domain).mapped('balance'))

        # Get all lines in proper order
        lines = self.env['account.move.line'].search(domain, order="date asc, id asc")

        # Calculate running balance
        running_balance = opening_balance
        transactions = []  # List to store transactions with running balance
        for line in lines:
            running_balance += line.debit - line.credit
            transactions.append({
            'date': line.date,
            'name': line.name,
            'debit': round(line.debit, 2),  # Round debit to 2 decimal places
            'credit': round(line.credit, 2),  # Round credit to 2 decimal places
            'balance': round(line.balance, 2),  # Round balance to 2 decimal places
            'running_balance': round(running_balance, 2),  # Round running balance to 2 decimal places
    })

        # Return the data to the template
        return {
            'partner_name': wizard.partner_id.name,
            'zone':wizard.partner_id.meter_id.zone_id.name if wizard.partner_id.meter_id else '',
            'start_date': wizard.start_date,
            'end_date': wizard.end_date,
            'opening_balance': opening_balance,
            'transactions': transactions,
        }