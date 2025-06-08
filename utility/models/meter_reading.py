from odoo import models, fields, api, _

from datetime import datetime
from datetime import date  # Add this import at the top
from dateutil.relativedelta import relativedelta
from odoo import tools


from odoo.exceptions import UserError, ValidationError

import logging

class MeterReading(models.Model):
    _name = 'meter.reading'
    _description = 'Water Meter Monthly Readings'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Inherit utility class
    _order = 'reading_date desc'
    _rec_name = 'display_name'
    
    # Fields
    meter_id = fields.Many2one(
        'billing.meter',
        string='Meter',
        required=True,
        ondelete='cascade',
        tracking=True
    )

    customer = fields.Char(string = "Customer", related='meter_id.customer_id.name',
                      store=False,
        readonly=True     
                           )
    
    bill_period = fields.Char(
        string='Billing Period',
        compute='_compute_bill_period',
        store=True,
        help="Format: YYYY-MM"
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
        digits=(12, 2))

    amount = fields.Float(
        string='Bill Amount',
          compute='_compute_amount',
        store=True,
        digits=(12, 2),
        help="Calculated bill amount based on consumption and tariff"
    )
    discount_percentage = fields.Float(related='meter_id.discount_percentage', store = False, readonly=True)
    discount_amount = fields.Float(
        string="Discount Amount",
          compute='_compute_amount',
        store=True,
        digits=(12, 2))
    tax_amount = fields.Float(
        string="Tax Amount",
          compute='_compute_amount',
        store=True,
        digits=(12, 2))
    fixed_charge = fields.Float(
        string='Fixed Charge',
        compute='_compute_amount',
        store=True,
        digits=(12, 2),
        help="Calculated Fixed charge based on consumption and tariff"
    )

    total_bill = fields.Float(
        string='Total Amount',
          compute='_compute_amount',
        store=True,
        digits=(12, 2),
        help="Calculated bill amount based on consumption and tariff"
    )
    
    # tariff_id = fields.Many2one(
    #     related='meter_id.tariff_id',
    #     string='Tariff',
    #     store=True,
    #     readonly=True
    # )

    is_invoiced = fields.Boolean(string='Invoiced', default=False, copy=False)
    invoice_id = fields.Many2one('account.move', string='Invoice', copy=False)
    invoice_date = fields.Date(string='Billing Date')

    # discount_id = fields.Many2one('meter_id.discount_id', string="Discount")
    

    # In your meter.reading model, add this field definition
#     amount_before_discount = fields.Float(
#     string="Amount Before Discount",
#       compute='_compute_amount',
#     readonly=True,
#     digits=(12, 2),
#     store=True
# )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ],
        string='Invoice State',
        related='invoice_id.state',
        default='draft',
        store=True,
        readonly=True
    )
    

    payment_state = fields.Selection(
        related='invoice_id.payment_state',
        string='Payment State',
        store=False
    )
    
    # tax_ids = fields.Many2many(
    #     'account.tax',
    #     string="Taxes",
    #     related='meter_id.tariff_id.tax_ids',  # Pull taxes from the tariff
    #     store=True
    # )
    
    # tax_amount = fields.Float(
    #     string="Tax Amount",
    #       compute='_compute_amount',
    #     store=True,
    #     digits=(12, 2))
    
    # amount_total = fields.Float(
    #     string="Total Amount",
    #       compute='_compute_amount',
    #     store=True,
    #     digits=(12, 2))
    
    # currency_id = fields.Many2one(
    #     'res.currency',
    #     # default=lambda self: self.env.company.currency_id
    #     default=lambda self: self.env.user.company_id.currency_id
    # )

    
    
    # amount_total = fields.Float(
    #     string="Total Amount",
    #       compute='_compute_amount',
    #     store=True,
    #     digits=(12, 2))


    def get_sales_data(self):
    #  self.env.cr.execute("SELECT get_product_sales(%s)", (56,))
    #  print(f"self.env.cr.fetchone()[0]: {self.env.cr.fetchone()[0]}")
     #return self.env.cr.fetchone()[0]
     pass

    @api.onchange('meter_id')
    def _onchange_meter_id(self):
     """Auto-populate previous reading when meter is selected"""

     for record in self:
        if record.meter_id:
            self.get_sales_data()
            try:
                last_reading = self.search([
                    ('meter_id', '=', record.meter_id.id),
                    ('id', '!=', record.id or False),('state', '=', 'posted')  # Exclude current record if editing
                ], order='reading_date desc, create_date desc', limit=1)
                print(f"ONCHANGE last_reading: {last_reading}")
                record.prev_reading = last_reading.current_reading if last_reading else 0.0
                
                # Auto-set reading date to today if empty
                if not record.reading_date:
                    record.reading_date = fields.Date.context_today(record)
                    
            except Exception as e:
                # Log error but don't break the form
                _#logger.error("Failed to fetch last reading: %s", str(e))
                record.prev_reading = 0.0

    @api.depends('amount_before_discount', 'meter_id.discount_id')
    def _compute_discount_amount(self):
     for record in self:
        if record.meter_id.discount_id:
            print(f"Amount before discount: {record.amount_before_discount}")
            
            record.discount_amount = record.amount_before_discount * (record.discount_percentage / 100)
        else:
            record.discount_amount = 0.0
    
    # Constraints
    _sql_constraints = [
        ('unique_reading_per_month', 
         'UNIQUE(meter_id, bill_period)',
         'Only one reading per meter per billing period is allowed!'),
        
        ('reading_validation',
         'CHECK(current_reading >= prev_reading)',
         'Current reading must be greater than or equal to previous reading!')
    ]
    
    # Computed Methods
    # @api.depends('reading_date')
    # def _compute_bill_period(self):
    #     for record in self:
    #         if record.reading_date:
    #             record.bill_period = record.reading_date.strftime('%Y-%m')
    #         else:
    #             record.bill_period = False
    
    

    @api.depends('reading_date')
    def _compute_bill_period(self):
        """ Compute billing period with date validation """
        for record in self:
            if not record.reading_date:
                record.bill_period = False
                continue
            
            # Skip validation during onchange to avoid blocking form opening
            if not self.env.context.get('onchange_reading_date'):
                try:
                    self._validate_reading_date(record.reading_date)
                except ValidationError:
                    # If date is invalid, still compute bill_period but don't crash
                    record.bill_period = False
                    continue
            
            if record.reading_date.day >= 22:
                bill_date = record.reading_date
            else:
                bill_date = record.reading_date + relativedelta(months=-1)
            
            record.bill_period = bill_date.strftime('%Y-%m-%d')

    def _validate_reading_date(self, reading_date):
        """ Validate reading date with proper context handling """
        today = date.today()
        if reading_date > today:
            raise ValidationError(
                _("Reading date cannot be in the future! "
                  f"(Date provided: {reading_date}, Today: {today})")
            )
    
    @api.constrains('reading_date')
    def _check_reading_date(self):
        """ Ensure all records have valid dates """
        for record in self:
            if record.reading_date:
                self._validate_reading_date(record.reading_date)
    



    @api.depends('current_reading', 'prev_reading')
    def _compute_consumption(self):
        for record in self:
            record.consumption = record.current_reading - record.prev_reading
    
    @api.depends('meter_id.name', 'bill_period')
    def _compute_display_name(self):
        for record in self:
            if record.meter_id and record.bill_period:
                record.display_name = f"{record.meter_id.name}/{record.bill_period}"
            else:
                record.display_name = False
    
    # Business Logic
    # @api.model
    # def create(self, vals):
    #     # Auto-fetch previous reading if not provided
    #     if 'prev_reading' not in vals:
    #         last_reading = self.search([
    #             ('meter_id', '=', vals.get('meter_id'))
    #         ], order='reading_date desc', limit=1)
            
    #         vals['prev_reading'] = last_reading.current_reading if last_reading else 0.0


    #     print(f"Trying to save {vals}")
    #     record = super().create(vals)
    #     print(f"Save result: {record}")
    #     if record:
    #        print("successfuly saved")
    #        record.action_create_invoice()

        
        
    #     return record

    # def calculate_bill(self):
    #     reading_vals = {}
    #     for record in self:
    #         meter = record.meter_id
    #         tariff = record.meter_id.tariff_id
    #         if not tariff:
    #           raise UserError(_("No tariff defined for this meter!"))
    #     print(f" meter: {meter.id}")
        
        #return reading_vals

    # def calculate_bill(self):
    #  for record in self:
    #     meter = record.meter_id  # This is the related billing.meter record
    #     # Now you can use meter fields, e.g.:
    #     print("Meter name:", meter.name)
    #     # ... your calculation logic ...

    # @api.model
    # def create(self, vals):
    #   # print(f"Creating Meter Reading with values: {vals}")
    #    vals = self._calculate_bill_vals(vals)
    
    #    record = super().create(vals)
    #    return record

      # Business Logic
    @api.model
    def create(self, vals):
        # Auto-fetch previous reading if not provided
        # if 'prev_reading' not in vals:
        #     last_reading = self.search([
        #         ('meter_id', '=', vals.get('meter_id'))
        #     ], order='reading_date desc', limit=1)
            
        #     vals['prev_reading'] = last_reading.current_reading if last_reading else 0.0


        print(f"Trying to save {vals}")
        record = super().create(vals)
        print(f"Save result: {record}")
        record.action_validate_reading()
        if record:
           print("successfuly saved")
           record.action_create_invoice()

        
        
        return record

    def _calculate_bill_vals(self, vals):
    # You can access meter, tariff, etc. using vals['meter_id'], vals['current_reading'], etc.
        meter = self.env['billing.meter'].browse(vals.get('meter_id'))
        if not meter:
            raise UserError(_("Meter not found!"))
        if not meter.tariff_id:
            raise UserError(_("No tariff defined for this meter!"))
        
        tariff = meter.tariff_id
        print(f"Calculating bill for meter: {meter.name}, tariff: {tariff.name}")
       # consumption = vals.get('current_reading', 0) - vals.get('prev_reading', 0)
        amount = 0.0
        tax_amount = 0.0
        vals['amount'] = amount
        vals['tax_amount'] = tax_amount
   
        return vals

    
    def action_validate_reading(self):
        """ Additional validation logic if needed """
        for record in self:
            if record.consumption < 0:
                raise ValidationError(_("Negative consumption detected!"))
            

    



   

   # @api.depends('consumption', 'meter_id.tariff_id', 'discount_percentage')
    
    @api.depends(
    'consumption',
    'meter_id.tariff_id.fixed_charge',
    'meter_id.tariff_id.pricing_method',
    'meter_id.tariff_id.block_ids',
    'meter_id.tariff_id.range_ids',
    'meter_id.tariff_id.taxes_id',
    'discount_percentage'
)
    def _compute_amount(self):
     for record in self:
        amount = 0.0
        amount_before_discount = 0.0
        record.rate = 0.0
        record.fixed_charge = 0.0
        record.tax_amount = 0.0
        record.discount_amount = 0.0
        record.amount = 0.0
        record.total_bill = 0.0

        tariff = record.meter_id.tariff_id
        if not record.consumption or not tariff:
            continue


        # Fixed charge
        fixed_charge = tariff.fixed_charge or 0.0
        record.fixed_charge = fixed_charge
        #amount += fixed_charge
       # amount_before_discount += fixed_charge

        # Consumption charges
        if tariff.pricing_method == 'block_rate':
            remaining = record.consumption
            for block in tariff.block_ids.sorted('sequence'):
                if remaining <= 0:
                    break
                block_consumption = min(remaining, block.limit) if block.limit > 0 else remaining
                amount += block_consumption * block.rate
                remaining -= block_consumption
        elif tariff.pricing_method == 'consumption_based':
            amount += record.consumption * tariff.consumption_rate
            record.rate = tariff.consumption_rate
        elif tariff.pricing_method == 'range_based':
            applicable_range = tariff.range_ids.sorted('min_value').filtered(
                lambda r: (r.min_value <= record.consumption) and
                (not r.max_value or record.consumption <= r.max_value))
            if applicable_range:
                amount += record.consumption * applicable_range[0].rate
                record.rate = applicable_range[0].rate
            else:
                highest_range = tariff.range_ids.sorted('min_value', reverse=True)[:1]
                if highest_range:
                    amount += record.consumption * highest_range[0].rate
                    record.rate = highest_range[0].rate

        #amount_before_discount = amount - fixed_charge

        # Discount
        discounted_consumption = 0 
        if record.discount_percentage:
            discounted_consumption = amount * ( (record.discount_percentage / 100))
            record.discount_amount = discounted_consumption
            #amount = amount + fixed_charge + discounted_consumption

        # Taxes
        taxes = tariff.taxes_id
        tax_amount = 0.0
        for tax in taxes:
            tax_amount += (tax.amount / 100) * (amount)
            # tax_amount += (tax.amount / 100) * discounted_consumption
            record.tax_amount = tax_amount

        # Final amounts
        #record.amount_before_discount = tools.float_round(amount_before_discount, precision_digits=2)
        record.amount = tools.float_round(amount, precision_digits=2) 
        record.total_bill = (record.amount + tax_amount + fixed_charge) - discounted_consumption

    def create8888(self):
   
    # Recompute if needed
     self._compute_amount()
    
    # Create invoices
     for record in self.filtered(lambda r: not r.is_invoiced):
        record.action_create_invoice()
    
     return True
        









    
    # Update display name to include amount
    @api.depends('meter_id.name', 'bill_period', 'amount')
    def _compute_display_name(self):
        for record in self:
            if record.meter_id and record.bill_period:
                record.display_name = (
                    f"{record.meter_id.name}/{record.bill_period} "
                    f"(Consumption: {record.consumption:.2f}, Amount: {record.amount:.2f})"
                )
            else:
                record.display_name = False



    # def action_create_invoice(self):
    #  self.ensure_one()
    #  if self.is_invoiced:
    #     raise UserError(_("This reading was already invoiced!"))
    
    #  tariff = self.meter_id.tariff_id
    #  invoice_lines = []
    
    # # 1. Fixed Charge (never discounted)

    #  if tariff.fixed_charge > 0:
    #     horomarinta_product = self.env['product.product'].browse(9)
    #     invoice_lines.append((0, 0, {
    #         'product_id': horomarinta_product.id,
    #         'name': f"Water Service Fixed Charge ({self.bill_period})",
    #         'price_unit': tariff.fixed_charge,
    #         'quantity': 1,
    #     }))

    # # 2. Consumption Charges
    #  consumption_desc = ""
    #  if tariff.pricing_method == 'block_rate':
    #     # Block rate logic remains same
    #     ...
    #  elif tariff.pricing_method == 'range_based':
    #     applicable_range = tariff.range_ids.sorted('min_value').filtered(
    #         lambda r: (r.min_value <= self.consumption) and 
    #         (not r.max_value or self.consumption <= r.max_value))
    #     rate = applicable_range[0].rate if applicable_range else tariff.range_ids.sorted('min_value', reverse=True)[0].rate
    #     consumption_desc = f"{self.consumption}m³ @ {rate}/m³ (Range-Based)"
    #     invoice_lines.append((0, 0, {
    #         'product_id': tariff.id,
    #         'name': f"Water Consumption {consumption_desc}",
    #         'price_unit': rate,
    #         'quantity': self.consumption,
    #         'discount': self.discount_percentage if self.discount_percentage else 0,
    #         'tax_ids': [(6, 0, tariff.taxes_id.ids)] if tariff.taxes_id else False,
    #     }))

    # # 3. Discount Line (with safe fallback)
    #  if self.discount_percentage:
    #     try:
    #         print(f"Trying..............................")
    #         #discount_product = self.env.ref('water_utility.discount_product')
    #         discount_product = self.env['product.product'].browse(8)
    #         print(f"Tried.................................................")
    #     except ValueError:
    #         discount_product = self.env['product.product'].create({
    #             'name': "Water Service Discount",
    #             'type': 'service',
    #             'list_price': 0,
    #         })
       
    #     # discount_amount = (self.amount_before_discount - (self.amount - tariff.fixed_charge)) if tariff.fixed_charge \
    #     #                  else (self.amount_before_discount - self.amount)
    #     discount_amount = self.net_bill * self.discount_percentage/100

        
    #     print(f"Before inserting discount line: {self.meter_id.discount_id.name}")
    #     invoice_lines.append((0, 0, {
    #         'product_id': discount_product.id,
    #         'name': f"Discount: {self.meter_id.discount_id.name or ''} ({self.discount_percentage}%)",
    #         'price_unit': -discount_amount,
    #         'quantity': 1,
    #     }))
    #     print(f"After inserting discount line: {discount_product.id}")

    # # Create invoice
    #  invoice = self.env['account.move'].create({
    #     'move_type': 'out_invoice',
    #     'invoice_date': fields.Date.today(),
    #     'partner_id': self.meter_id.customer_id.id,
    #     'invoice_line_ids': invoice_lines,
    #  })
    
    #  self.write({
    #     'is_invoiced': True,
    #     'invoice_id': invoice.id,
    #     'invoice_date': fields.Date.today(),
    # })
    
    #  return {
    #     'type': 'ir.actions.act_window',
    #     'res_model': 'account.move',
    #     'res_id': invoice.id,
    #     'view_mode': 'form',
    #     'target': 'current',
    # }


    
    # def action_create_invoice(self):
    #  self.ensure_one()
    #  #if self.is_invoiced:
    #     #raise UserError(_("This reading was already invoiced!"))

    #  tariff = self.meter_id.tariff_id
    #  invoice_lines = []
    #  currency = self.env.company.currency_id

    # # 1. Fixed Charge (never discounted, no tax)
    #  if tariff.fixed_charge > 0:
    #     horomarinta_product = self.env['product.product'].browse(9)
    #     invoice_lines.append((0, 0, {
    #         'product_id': horomarinta_product.id,
    #         'name': f"Water Service Fixed Charge ({self.bill_period})",
    #         'price_unit': tariff.fixed_charge,
    #         'quantity': 1,
    #         'tax_ids': False,  # Explicitly no tax
    #     }))

    # # 2. Consumption Charges (tax calculated before discount)
    #  if tariff.pricing_method == 'range_based':
    #     applicable_range = tariff.range_ids.sorted('min_value').filtered(
    #         lambda r: (r.min_value <= self.consumption) and 
    #         (not r.max_value or self.consumption <= r.max_value))
    #     rate = applicable_range[0].rate if applicable_range else tariff.range_ids.sorted('min_value', reverse=True)[0].rate
    #     consumption_desc = f"{self.consumption}m³ @ {rate}/m³ (Range-Based)"
        
    #     # Calculate base amount
    #     base_amount = self.consumption * rate
        
    #     # Compute taxes on full amount (pre-discount)
    #     taxes = tariff.taxes_id.compute_all(
    #         base_amount,
    #         currency=currency,
    #         product=tariff,
    #         quantity=1
    #     ) if tariff.taxes_id else None
        
    #     # Apply discount to tax-included amount if exists
    #     if self.discount_percentage:
    #         discount_factor = (100 - self.discount_percentage) / 100
    #         price_unit = (taxes['total_included'] if taxes else base_amount) * discount_factor
    #     else:
    #         price_unit = taxes['total_included'] if taxes else base_amount
        
    #     invoice_lines.append((0, 0, {
    #         'product_id': tariff.id,
    #         'name': f"Water Consumption {consumption_desc}",
    #         'price_unit': price_unit / self.consumption,  # Convert back to unit price
    #         'quantity': self.consumption,
    #         'discount': 0,  # Discount already applied in calculation
    #         'tax_ids': [(6, 0, tariff.taxes_id.ids)] if tariff.taxes_id else [],
    #     }))

    # # 3. Discount Line (optional - set if condition to True to enable)
    #  if self.discount_percentage and False:  # Change to True for separate discount line
    #     discount_product = self.env['product.product'].browse(8)
    #     discount_amount = base_amount * (self.discount_percentage / 100)
    #     invoice_lines.append((0, 0, {
    #         'product_id': discount_product.id,
    #         'name': f"Discount: {self.meter_id.discount_id.name or ''} ({self.discount_percentage}%)",
    #         'price_unit': -discount_amount,
    #         'quantity': 1,
    #         'tax_ids': [(6, 0, tariff.taxes_id.ids)] if tariff.taxes_id else [],
    #     }))

    # # Create invoice
    #  invoice = self.env['account.move'].create({
    #     'move_type': 'out_invoice',
    #     'invoice_date': fields.Date.today(),
    #     'partner_id': self.meter_id.customer_id.id,
    #     'invoice_line_ids': invoice_lines,
    #     'invoice_origin': self.display_name,
    # })
    
    #  self.write({
    #     'is_invoiced': True,
    #     'invoice_id': invoice.id,
    #     'invoice_date': fields.Date.today(),
    # })
    
    #  return {
    #     'type': 'ir.actions.act_window',
    #     'res_model': 'account.move',
    #     'res_id': invoice.id,
    #     'view_mode': 'form',
    #     'target': 'current',
    # }

    def action_create_invoice(self):
        self.ensure_one()
        if self.is_invoiced:
           raise UserError(_("This reading was already invoiced!"))
        
        print(f"111111111111111111111: {self.meter_id}")
        tariff = self.meter_id.tariff_id
        customer = self.meter_id.customer_id.id
        invoice_lines = []
        # currency = self.env.user.company_id.currency_id
        print(f"22222222222222222222222222: {customer}")

        #income_account = tariff.property_account_income_id or tariff.categ_id.property_account_income_categ_id
        income_account = self.env['account.account'].sudo().search([('code', '=', '40001')], limit=1)
        if not income_account:
           raise UserError(_("Please configure income account for the tariff product!"))
        
        print("33333333333333333333333333")
        if tariff.fixed_charge > 0:
           fixed_charge_product = self.env['product.product'].sudo().browse(2)  # Replace with your fixed charge product ID
           #fixed_account = fixed_charge_product.property_account_income_id or fixed_charge_product.categ_id.property_account_income_categ_id
           fixed_account = self.env['account.account'].search([('code', '=', '21007')], limit=1)
           invoice_lines.append((0, 0, {
            'product_id': fixed_charge_product.id,
            'name': f"Water Service Fixed Charge ({self.bill_period})",
            'price_unit': tariff.fixed_charge,
            'quantity': 1,
            'account_id': fixed_account.id,  # Explicit account
            'tax_ids': [(6, 0, [])],  # No tax on fixed charge
        }))
           

        # 2. Consumption Charges
        consumption_amount = 0.0
        consumption_desc = ""
        rate = 0.0

        print("444444444444444444444")

        invoice_lines.append((0, 0, {
            'product_id': tariff.id,
            'name': f"Water Consumption {consumption_desc}",
            'price_unit': self.rate,  # Show original rate
            'quantity': self.consumption,
            'discount': self.discount_percentage,
            'account_id': income_account.id,  # Explicit account
            'tax_ids': [(6, 0, tariff.taxes_id.ids)] if tariff.taxes_id else [],
        }))

        print(f"55555555555555555555555 ")
        # company_id = self.env.user.company_id.id
        # if not company_id:
        #    raise UserError(_("No company set for the current user!"))
        
        # print(f"company_id: {company_id}")


        invoice = self.env['account.move'].sudo().create({
        'move_type': 'out_invoice',
        'invoice_date': fields.Date.today(),
        'partner_id': customer,
        'invoice_line_ids': invoice_lines,
        'invoice_origin': f"Water Reading {self.display_name}",
        #'company_id': 1,  # <-- Add this line
        #'meter_reading_id': self.id,  # Link the meter reading
        #'meter_id': self.meter_id.id,  # Link the meter reading
    })
        
        print("66666666666666666666666")
        
        invoice.action_post()

        
        print("77777777777777777777777")
                
        
        self.write({
        'is_invoiced': True,
        'invoice_id': invoice.id,
        'invoice_date': fields.Date.today(),
    })
        
        # Additional operations
        #self.reconcile_invoice_credits(invoice)

        return {
        'type': 'ir.actions.act_window',
        'res_model': 'account.move',
        'res_id': invoice.id,
        'view_mode': 'form',
        'target': 'current',
    }


    def action_post_invoice(self):
     """ Post the linked invoice """
     for record in self:
        if not record.invoice_id:
            raise UserError(_("No invoice exists for this reading!"))
        if record.invoice_id.state != 'draft':
            raise UserError(_("Invoice is already posted  or cancelled!"))
        
        # Post the invoice
        record.invoice_id.action_post()
        
        # Log the action
        record.message_post(
            body=_("Invoice was posted by %s") % self.env.user.name,
            subject="Invoice Posted"
        )
     return True

    def action_cancel_invoice(self):
   
     for record in self:
        if not record.invoice_id:
            raise UserError(_("No invoice exists for this reading!"))

        invoice = record.invoice_id

        # Validate state - Only allow cancellation from draft
        if invoice.state != 'draft':
            raise UserError(_(
                "Only draft invoices can be cancelled directly! "
                "Current state: %s"
            ) % invoice.state)

        try:
            # Execute cancellation
            invoice.button_cancel()
            
            # Log the action
            record.message_post(
                body=_("Invoice was cancelled from draft state by %s") % self.env.user.name,
                subject="Invoice Cancelled",
                message_type="comment"
            )
            
        except Exception as e:
            _logger.error("Failed to cancel draft invoice: %s", str(e))
            raise UserError(_(
                "Failed to cancel invoice: %s"
            ) % str(e))
    
     return True

    def action_reset_draft_invoice(self):
      
     for record in self:
        if not record.invoice_id:
            raise UserError(_("No invoice exists for this reading!"))
        if record.invoice_id.state != 'cancel':
            raise UserError(_("Only cancelled invoices can be reset to draft!"))
        
        # Reset to draft
        record.invoice_id.button_draft()
        
        # Log the action
        record.message_post(
            body=_("Invoice was reset to draft by %s") % self.env.user.name,
            subject="Invoice Reset"
        )
     return True
        





    
        

    



    def action_open_invoice(self):
     self.ensure_one()
     return {
        'type': 'ir.actions.act_window',
        'res_model': 'account.move',
        'res_id': self.invoice_id.id,
        'views': [(False, 'form')],
        'target': 'current',
    }

    def action_confirm(self):
     self.write({'state': 'confirmed'})

    def action_invoice(self):
     self.write({'state': 'invoiced'})

    def reconcile_invoice_credits(self, invoice):
        invoice_receivable_lines = invoice.line_ids.filtered(
        lambda l: l.account_id.account_type == 'asset_receivable' and not l.reconciled
    )
        if not invoice_receivable_lines:
           return False
        ar_account_id = invoice_receivable_lines[0].account_id.id
        credit_lines = self.env['account.move.line'].search([
        ('partner_id', '=', invoice.partner_id.id),
        ('account_id', '=', ar_account_id),
        ('move_id.state', '=', 'posted'),
        ('reconciled', '=', False),
        ('balance', '<', 0),
    ])
        for c_line in credit_lines.sorted(key=lambda x: x.date):
            if not invoice_receivable_lines:
               break
            (c_line + invoice_receivable_lines).reconcile()
            invoice_receivable_lines = invoice_receivable_lines.filtered(lambda l: not l.reconciled)
        return True
    
    def cancel(self):
     
     for record in self:
        invoice = record.invoice_id
        if not invoice:
            # No invoice, just do whatever local logic you want.
            continue

        # 1) If invoice is already in draft, just cancel it (or do your reading logic).
        if invoice.state == 'draft':
            invoice.button_cancel()
            record.invoice_status = 'no_invoice'

        # 2) If invoice is posted, revert to draft (if allowed), then cancel if desired
        elif invoice.state == 'posted':
            # Revert to draft
            invoice.button_draft()  # This is only possible if "Allow Cancelling Entries" is on.
            # Now it's in draft, so we can truly cancel it if needed
            invoice.button_cancel()
            record.invoice_status = 'no_invoice'

        # 3) If invoice is in some other state (e.g. 'cancel'), do your own logic
        # e.g., pass or raise an error
        else:
            pass

        # If you want the reading itself to go back to a "draft" stage, define a local
        # reading_state field or something similar and set record.reading_state = 'draft'.

        return True
     
    def action_reset_to_draft(self):
    
     try:
        for record in self:
            with self.env.cr.savepoint():  # Creates a transaction savepoint
                invoice = record.invoice_id
                if invoice and invoice.state in ['posted']:
                    # 1. Reset invoice to draft
                    invoice.button_draft()
                    print("I am about to update balance after reset to draft")
                    #record.update_meter_balance(action='reset',model_name=invoice.name, desc='Invoice reset to draft',amount_to_update=record.invoice_id.amount_total)
                elif invoice and invoice.state in ['cancel']:    
                    # 2. Update meter balance
                    #record.update_meter_balance(action='reset')
                    invoice.button_draft()
                    
                return True
        
     except Exception as e:
        _logger.error("Failed to reset to draft: %s", str(e), exc_info=True)
        raise UserError(_("Failed to reset to draft: %s") % str(e))
     