from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    meter_reading_id = fields.Many2one(
        'meter.reading',
        string='Related Meter Reading',
        readonly=True
    )
    # Related fields to access meter information directly
    meter_id = fields.Many2one(
        'water.meter',
        string='Water Meter',
       
        
    )
    
    # def action_post(self):
    

    #  # Store original state for comparison
    #  original_states = {inv.id: inv.state for inv in self}
    #  print(f"original_states: {original_states}")

    # # Call the original posting method - returns True/False
    #  post_result = super().action_post()
    #  # Find which invoices actually changed state
    #  successfully_posted = self.filtered(
    #     lambda inv: inv.state == 'posted' and original_states[inv.id] != 'posted'
    # )
    #  print(f"original_states2 : {original_states}")
    #  print(f"successfully_posted: {successfully_posted}")
    #  # Process reconciliation for successfully posted invoices
    #  for invoice in successfully_posted:
    #     if invoice.move_type in ('out_invoice', 'out_refund'):
    #         self.reconcile_invoice_credits(invoice)
    
    # # Return True if any invoice was posted, regardless of parent's return
    #  return bool(successfully_posted) or post_result


    def action_post(self):
    
    # 1. Pre-filter only draft invoices (avoids unnecessary processing)
     to_post = self.filtered(lambda inv: inv.state == 'draft')
     if not to_post:
        # Return True if all were already posted, False if any were invalid
        return all(inv.state == 'posted' for inv in self)
    
    # 2. Store original states more efficiently
     original_posted_ids = {inv.id for inv in to_post if inv.state == 'posted'}
    
    # 3. Call parent method only on draft invoices
     post_result = super(AccountMove, to_post).action_post()
    
    # 4. Identify successfully posted invoices more efficiently
     successfully_posted = to_post.filtered(
        lambda inv: (
            inv.state == 'posted' and 
            inv.id not in original_posted_ids and
            inv.move_type in ('out_invoice', 'out_refund')
        )
    )
    
    # 5. Optimized reconciliation with batch processing
     if successfully_posted:
        self.reconcile_invoice_credits(successfully_posted)
    
    # 6. Smarter return value logic
     return post_result if to_post == self else bool(successfully_posted)
    




    def reconcile_invoice_credits(self, invoice):
    
     invoice_receivable_lines = invoice.line_ids.filtered(
        lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
    )
    
     if not invoice_receivable_lines:
        return False
    
     ar_account_id = invoice_receivable_lines[0].account_id.id
    
    # Find available credit lines for this partner
     credit_lines = self.env['account.move.line'].search([
        ('partner_id', '=', invoice.partner_id.id),
        ('account_id', '=', ar_account_id),
        ('move_id.state', '=', 'posted'),
        ('reconciled', '=', False),
        ('balance', '<', 0),
    ], order='date asc')  # Using order parameter instead of sorted()
    
    # Reconcile line by line
     for c_line in credit_lines:
        if not invoice_receivable_lines:
            break
        (c_line + invoice_receivable_lines).reconcile()
        invoice_receivable_lines = invoice_receivable_lines.filtered(lambda l: not l.reconciled)
    
     return True


   