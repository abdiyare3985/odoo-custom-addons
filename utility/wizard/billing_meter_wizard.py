from odoo import models, fields, api

class BillingMeterWizard(models.TransientModel):
    _name = 'billing.meter.wizard'
    _description = 'Billing Meter Wizard'

    partner_id = fields.Many2one(
        'res.partner',
        string="Customer",
        readonly=True,
       # required=True
    )
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    lines = fields.Many2many('account.move.line', string="Lines")
    opening_balance = fields.Float(string="Opening Balance")

    def action_confirmOLD(self):
       self.ensure_one()

    # Domain to get all relevant transactions
       domain = [
        ('partner_id', '=', self.partner_id.id),
        ('date', '>=', self.start_date),  # Start date condition
        ('date', '<=', self.end_date), 
        ('parent_state', '=', 'posted'),
        ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable'])
    ]

    # Calculate opening balance (all transactions before start_date)
       opening_domain = [
        ('partner_id', '=', self.partner_id.id),
        ('date', '<', self.start_date),
        ('parent_state', '=', 'posted'),
        ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable'])
    ]
       opening_balance = sum(self.env['account.move.line'].search(opening_domain).mapped('balance'))

    # Get all lines in proper order
       lines = self.env['account.move.line'].search(domain, order="id desc, date desc")
       
       # Calculate running balance
       running_balance = opening_balance
       for line in lines:
        running_balance += line.debit - line.credit
        line.running_balance = running_balance  # Add a custom attribute to store the running balance

       self.lines = lines
       self.opening_balance = opening_balance

    # Pass the current record (self) to the report
       return self.env.ref('utility.action_billing_meter_statement_report').report_action(self)
    

    def action_confirmOLD2(self):
     self.ensure_one()

    # Domain to get all relevant transactions
     domain = [
        ('partner_id', '=', self.partner_id.id),
        ('date', '>=', self.start_date),  # Start date condition
        ('date', '<=', self.end_date),    # End date condition
        ('parent_state', '=', 'posted'),
        ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable'])
    ]

    # Calculate opening balance (all transactions before start_date)
     opening_domain = [
        ('partner_id', '=', self.partner_id.id),
        ('date', '<', self.start_date),
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
            'debit': line.debit,
            'credit': line.credit,
            'balance': line.balance,
            'running_balance': running_balance,
        })

    # Pass the data to the report
     return self.env.ref('utility.action_billing_meter_statement_report').report_action(self, data={
        'partner_id': self.partner_id.name,  # Pass the partner name
        'start_date': self.start_date,
        'end_date': self.end_date,
        'opening_balance': opening_balance,
        'transactions': transactions,
    })

    def action_confirm(self):
     self.ensure_one()
     return self.env.ref('utility.action_billing_meter_statement_report').report_action(self)