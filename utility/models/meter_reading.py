from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from calendar import monthrange
import logging

_logger = logging.getLogger(__name__)

class MeterReading(models.Model):
    _name = 'meter.reading'
    _description = 'Water Meter Monthly Readings'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'reading_date desc'
    _rec_name = 'display_name'
    
    # ===============================
    # Field Definitions
    # ===============================
    meter_id = fields.Many2one(
        'billing.meter',
        string='Meter',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    customer = fields.Char(
        string="Customer",
        related='meter_id.customer_id.name',
        readonly=True
    )
    period = fields.Date(
        string='Billing Period',
        compute='_compute_bill_period',
        store=True,
        help="End date of billing period (YYYY-MM-DD)"
    )
    reading_date = fields.Date(
        string='Reading Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    display_name = fields.Char(
        string='Reference',
        compute='_compute_display_name',
        store=True
    )
    prev_reading = fields.Float(
        string='Previous Reading',
        digits=(12, 3),
        required=True
    )
    current_reading = fields.Float(
        string='Current Reading',
        digits=(12, 3),
        required=True
    )
    consumption = fields.Float(
        string='Consumption',
        digits=(12, 3),
        compute='_compute_consumption',
        store=True
    )
    rate = fields.Float(
        string="Rate",
        compute='_compute_amount',
        store=True,
        digits=(12, 2)
    )
    # Add back the amount field
    amount = fields.Float(
    string='Base Amount',
    compute='_compute_amount',
    store=True,
    digits=(12, 2),
    help="Calculated amount before discount and tax"
)

# Add back amount_before_discount for clarity
    amount_before_discount = fields.Float(
    string="Amount Before Discount",
    compute='_compute_amount',
    store=True,
    digits=(12, 2),
    help="Consumption amount before applying discount"
)
    discount_percentage = fields.Float(
        related='meter_id.discount_percentage',
        readonly=True
    )
    discount_amount = fields.Float(
        string="Discount Amount",
        compute='_compute_amount',
        store=True,
        digits=(12, 2)
    )
    tax_amount = fields.Float(
        string="Tax Amount",
        compute='_compute_amount',
        store=True,
        digits=(12, 2)
    )
    fixed_charge = fields.Float(
        string='Fixed Charge',
        compute='_compute_amount',
        store=True,
        digits=(12, 2)
    )
    total_bill = fields.Float(
        string='Total Amount',
        compute='_compute_amount',
        store=True,
        digits=(12, 2)
    )
    is_invoiced = fields.Boolean(
        string='Invoiced',
        default=False,
        copy=False
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        copy=False
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ],
        string='Invoice State',
        related='invoice_id.state',
        store=True,
        readonly=True
    )
    payment_state = fields.Selection(
        related='invoice_id.payment_state',
        string='Payment State',
        store=False
    )
    invoice_date = fields.Date(string='Billing Date')

    # ===============================
    # SQL Constraints
    # ===============================
    _sql_constraints = [
        ('unique_reading_per_month', 
         'UNIQUE(meter_id, period)',
         'Only one reading per meter per billing period is allowed!'),
        
        ('reading_validation',
         'CHECK(current_reading >= prev_reading)',
         'Current reading must be greater than or equal to previous reading!')
    ]

    # ===============================
    # Compute Methods
    # ===============================
    @api.depends('reading_date')
    def _compute_bill_period(self):
        """ Compute billing period end date """
        for record in self:
            if not record.reading_date:
                record.period = False
                continue

            reading_day = record.reading_date.day
            reading_month = record.reading_date.month
            reading_year = record.reading_date.year

            # Determine billing period (22nd to end of month)
            if 22 <= reading_day <= 31:
                last_day = monthrange(reading_year, reading_month)[1]
                record.period = record.reading_date.replace(day=last_day)
            else:
                prev_date = record.reading_date - relativedelta(months=1)
                last_day = monthrange(prev_date.year, prev_date.month)[1]
                record.period = prev_date.replace(day=last_day)

    @api.depends('current_reading', 'prev_reading')
    def _compute_consumption(self):
        for record in self:
            record.consumption = record.current_reading - record.prev_reading

    @api.depends('meter_id', 'period', 'consumption', 'total_bill')
    def _compute_display_name(self):
        for record in self:
            if record.meter_id and record.period:
                record.display_name = (
                    f"{record.meter_id.name}/{record.period.strftime('%Y-%m')} "
                    f"(Cons: {record.consumption:.2f}, Amt: {record.total_bill:.2f})"
                )
            else:
                record.display_name = False

    
    # Update the _compute_amount method
    @api.depends('consumption', 'meter_id.tariff_id', 'discount_percentage')
    def _compute_amount(self):
     for record in self:
        # Initialize all amount fields safely
        amounts = {
            'rate': 0.0,
            'fixed_charge': 0.0,
            'amount': 0.0,
            'amount_before_discount': 0.0,
            'discount_amount': 0.0,
            'tax_amount': 0.0,
            'total_bill': 0.0
        }
        
        tariff = record.meter_id.tariff_id
        if not tariff or not record.consumption:
            record.update(amounts)
            continue

        # Fixed charge (never discounted)
        fixed_charge = tariff.fixed_charge or 0.0
        amounts['fixed_charge'] = fixed_charge
        
        # Consumption calculation
        consumption_amount = 0.0
        if tariff.pricing_method == 'block_rate':
            remaining = record.consumption
            for block in tariff.block_ids.sorted('sequence'):
                if remaining <= 0:
                    break
                block_usage = min(remaining, block.limit) if block.limit > 0 else remaining
                consumption_amount += block_usage * block.rate
                remaining -= block_usage
        elif tariff.pricing_method == 'consumption_based':
            consumption_amount = record.consumption * tariff.consumption_rate
            amounts['rate'] = tariff.consumption_rate
        elif tariff.pricing_method == 'range_based':
            for r in tariff.range_ids.sorted('min_value'):
                if record.consumption >= r.min_value and (not r.max_value or record.consumption <= r.max_value):
                    consumption_amount = record.consumption * r.rate
                    amounts['rate'] = r.rate
                    break
        
        # Set amount values
        amounts['amount'] = fixed_charge + consumption_amount
        amounts['amount_before_discount'] = consumption_amount
        
        # Discount calculation
        if record.discount_percentage:
            amounts['discount_amount'] = consumption_amount * (record.discount_percentage / 100)
        
        # Tax calculation (on discounted consumption only)
        discounted_consumption = consumption_amount - amounts['discount_amount']
        if tariff.taxes_id:
            taxes_res = tariff.taxes_id.compute_all(
                discounted_consumption,
                currency=record.env.company.currency_id,
                quantity=1.0,
                partner=record.meter_id.customer_id
            )
            amounts['tax_amount'] = taxes_res['total_included'] - taxes_res['total_excluded']
        
        # Final total
        amounts['total_bill'] = amounts['amount'] - amounts['discount_amount'] + amounts['tax_amount']
        
        # Safely update all fields
        record.update(amounts)

    # ===============================
    # Constraint Methods
    # ===============================
    @api.constrains('reading_date')
    def _check_reading_date(self):
        today = fields.Date.today()
        for record in self:
            if record.reading_date > today:
                raise ValidationError(_(
                    "Reading date cannot be in the future! "
                    f"(Provided: {record.reading_date}, Today: {today})"
                ))
            
    @api.constrains('amount_before_discount', 'discount_amount')
    def _check_amount_consistency(self):
     for record in self:
        if record.discount_amount > record.amount_before_discount:
            raise ValidationError(_("Discount cannot exceed the base amount!"))

    # ===============================
    # CRUD Methods
    # ===============================
    @api.model
    def create(self, vals):
        # Auto-fetch previous reading
        if 'prev_reading' not in vals and vals.get('meter_id'):
            last_reading = self.search([
                ('meter_id', '=', vals['meter_id']),
                ('state', '=', 'posted')
            ], order='reading_date desc', limit=1)
            vals['prev_reading'] = last_reading.current_reading if last_reading else 0.0

        record = super().create(vals)
        record.action_validate_reading()
        record.action_create_invoice()
        return record

    # ===============================
    # Business Logic
    # ===============================
    def action_validate_reading(self):
        """ Validate consumption value """
        for record in self:
            if record.consumption < 0:
                raise ValidationError(_("Negative consumption detected!"))

    def action_create_invoice(self):
        self.ensure_one()
        if self.is_invoiced:
            return  # Skip if already invoiced

        # Prepare invoice lines
        invoice_lines = []
        tariff = self.meter_id.tariff_id
        partner = self.meter_id.customer_id

        # Fixed charge line
        if self.fixed_charge:
            invoice_lines.append(self._prepare_fixed_charge_line())

        # Consumption line
        invoice_lines.append(self._prepare_consumption_line())

        # Create invoice
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'partner_id': partner.id,
            'invoice_line_ids': invoice_lines,
            'invoice_origin': f"Meter Reading: {self.display_name}",
            'meter_reading_id': self.id,
        })
        invoice.action_post()

        # Update reading status
        self.write({
            'is_invoiced': True,
            'invoice_id': invoice.id,
            'invoice_date': fields.Date.today(),
        })

    def _prepare_fixed_charge_line(self):
        tariff = self.meter_id.tariff_id
        account = self.env['account.account'].search([('code', '=', '21005')], limit=1)
        fixed_charge_product = self.env['product.product'].sudo().browse(2)
        
        return (0, 0, {
            'product_id': fixed_charge_product.id,
            'name': f"Water Service Fixed Charge ({self.period.strftime('%Y-%m')})",
            'price_unit': self.fixed_charge,
            'quantity': 1,
            'account_id': account.id,
            'tax_ids': [(6, 0, [])],
        })

    def _prepare_consumption_line(self):
        tariff = self.meter_id.tariff_id
        account = self.env['account.account'].search([('code', '=', '40001')], limit=1)
        
        return (0, 0, {
            'product_id': tariff.id,
            'name': f"Consumption: {self.consumption:.2f}m³ @ {self.rate:.2f}/m³",
            'price_unit': self.rate,
            'quantity': self.consumption,
            'discount': self.discount_percentage,
            'account_id': account.id,
            'tax_ids': [(6, 0, tariff.taxes_id.ids)],
        })

    # ===============================
    # Invoice Actions
    # ===============================
    def action_post_invoice(self):
        for record in self:
            if record.invoice_id.state == 'draft':
                record.invoice_id.action_post()

    def action_cancel_invoice(self):
        for record in self:
            if record.invoice_id.state in ['draft', 'posted']:
                record.invoice_id.button_cancel()

    def action_view_invoice(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_reset_to_draft(self):
   
     for record in self:
        try:
            # Reset the reading itself
            record.write({
                'is_invoiced': False,
                'invoice_date': False,
            })

            # Handle linked invoice if exists
            if record.invoice_id:
                if record.invoice_id.state == 'posted':
                    # Reset invoice to draft first
                    record.invoice_id.button_draft()
                
                if record.invoice_id.state == 'draft':
                    # Only unlink if in draft state to prevent accounting issues
                    record.invoice_id.unlink()
                    record.invoice_id = False
            
            # Log the action
            record.message_post(
                body=_("Meter reading reset to draft by %s") % self.env.user.name,
                subject="Reading Reset"
            )
            
        except Exception as e:
            _logger.error("Failed to reset reading %s: %s", record.display_name, str(e))
            raise UserError(_(
                "Could not reset reading %(name)s: %(error)s",
                name=record.display_name,
                error=str(e)
            ))
        return True