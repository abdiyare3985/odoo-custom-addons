from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date
import re

class billingMeter(models.Model):
    _name = 'billing.meter'
    _description = 'Water Consumption Meter'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'connection_date desc, name'
    _sql_constraints = [
        ('serial_unique', 'UNIQUE(serial_id)', 'This serial number is already assigned to another meter!'),
        ('coordinates_format', "CHECK(coordinates ~ '^-?\\d{1,3}\\.\\d+,-?\\d{1,3}\\.\\d+$')", 
         'Coordinates must be in "lat,lng" format (e.g. "12.345,-12.345")'),
    ]

    # ========== IDENTIFICATION FIELDS ==========
    name = fields.Integer(
        string='Meter ID',
        required=True,
        index=True,
        tracking=True,
        #default=lambda self: self.env['ir.sequence'].next_by_code('water.meter'),
        help="Unique meter identification number"
    )

    customer_id = fields.Many2one(
    'res.partner',
    string='Customer',
    domain="[('is_company','=',False), ('customer_rank','>',0)]",
    tracking=True,
    help="Customer account linked to this meter"
)
    
    serial_id = fields.Many2one(
        'meter.serial',
        string='Serial Number',
        required=True,
        domain="[('state','=','available')]",
        ondelete='restrict',
        tracking=True
    )
    
    serial_number = fields.Char(
        related='serial_id.serial_number',
        string='Serial Number',
        store=True,
        readonly=True
    )

    # ========== CUSTOMER & LOCATION FIELDS ==========
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        domain="[('is_company','=',False), ('customer_rank','>',0)]",
        tracking=True,
        help="Customer account linked to this meter"
    )
    
    zone_id = fields.Many2one(
        'billing.zone',
        string='Zone',
        required=True,
        tracking=True,
        index=True,
        help="Geographical zone where meter is installed"
    )
    
    group_id = fields.Many2one(
        'meter.group',
        string='Technical Group',
        tracking=True,
        help="Functional grouping of meters"
    )
    
    coordinates = fields.Char(
        string='GPS Coordinates',
        tracking=True,
        help="Latitude,Longitude (e.g. '12.345,-12.345')"
    )
    
    latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
        compute='_compute_lat_lng',
        store=True
    )
    
    longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
        compute='_compute_lat_lng',
        store=True
    )
    
    house_number = fields.Char(
        string='House Number',
        tracking=True,
        size=16
    )
    
    street = fields.Char(
        string='Street',
        tracking=True
    )
    
    area = fields.Char(
        string='Area/Neighborhood',
        tracking=True
    )

    # ========== SERVICE FIELDS ==========
    connection_date = fields.Date(
        string='Connection Date',
        default=fields.Date.today,
        required=True,
        tracking=True
    )
    
    status = fields.Selection(
        [('connected', 'Connected'),
         ('disconnected', 'Disconnected'),
         ('blocked', 'Blocked')],
        string='Connection Status',
        default='connected',
        tracking=True,
        index=True
    )
    
    tariff_id = fields.Many2one(
        'product.template',
        domain="[('is_billing_plan', '=', True)]",
        string='Tariff Plan',
        required=True,
        tracking=True,
        help="Pricing plan applied to this meter"
    )
    
    discount_id = fields.Many2one(
        'meter.discount',
        string='Discount',
        tracking=True,
        #domain="[('active','=',True)]"
    )
    
    
    discount_percentage = fields.Float(
        related='discount_id.percentage',
        string='Discount (%)',
        store=True,
        digits=(5, 2)
    )
    # One2many field linking to meter.reading
    # meter_reading_ids = fields.One2many(
    #     comodel_name='meter.reading',
    #     inverse_name='meter_id',
    #     string='Meter Readings'
    # )

    meter_reading_count = fields.Integer(
        string="Meter Reading Count",
        compute="_compute_meter_reading_count",
        readonly=True
    )
    payment_count = fields.Integer(
        string="Payment Count",
        compute="_compute_payment_count",
        readonly=True
    )

    
    def _compute_payment_count(self):
        for meter in self:
            meter.payment_count = self.env['account.payment'].search_count([('partner_id', '=', self.customer_id.id)])

    #@api.depends('id')
    def _compute_meter_reading_count(self):
        for meter in self:
            meter.meter_reading_count = self.env['meter.reading'].search_count([('meter_id', '=', meter.id)])

    def action_view_payments(self):
        """Action to view payments related to the customer of this meter."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payments',
            'res_model': 'account.payment',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.customer_id.id)],
            'target': 'new',  # Open in a modal popup
        }
    reference = fields.Char(string='Reference', readonly=True, copy=False, default=lambda self: self.env['ir.sequence'].next_by_code('water.meter'))

    # Add to water.meter model
    def _compute_invoice_count(self):
     for meter in self:
        meter.invoice_count = self.env['account.move'].search_count([
            ('invoice_line_ids.name', 'ilike', meter.name),
            ('move_type', '=', 'out_invoice')
        ])

    total_balance = fields.Float(
        string="Total Balance",
        compute="_compute_total_balance",
        readonly=True
    )

    @api.depends('customer_id')
    def _compute_total_balance(self):
        """Compute the total balance for the meter based on the customer's balance."""
        for meter in self:
            if meter.customer_id:
                # Use the customer's total balance (e.g., from account.move or account.payment)
                meter.total_balance = meter.customer_id.credit - meter.customer_id.debit
            else:
                meter.total_balance = 0.0

    def action_view_total_balance(self):
     """Action to view the total balance details with running balance."""
     self.ensure_one()
     return {
        'type': 'ir.actions.act_window',
        'name': 'Total Balance',
        'res_model': 'account.move',
        'view_mode': 'tree',
        'view_id': self.env.ref('utility.view_account_move_tree_with_running_balance').id,
        'domain': [('partner_id', '=', self.customer_id.id)],
        'target': 'new',  # Open in a modal popup
    }
    

    

    invoice_count = fields.Integer(compute='_compute_invoice_count')
    
    @api.model
    def create(self, vals):
        # Only assign reference if creation succeeds
        if 'reference' not in vals:
            vals['reference'] = self.env['ir.sequence'].next_by_code('billing.meter') or '/'
        return super(billingMeter, self).create(vals)

    # ========== TECHNICAL FIELDS ==========
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True
    )
    
    last_reading = fields.Float(
        string='Last Reading (m³)',
       # compute='_compute_last_reading',
        store=True,
        digits=(12, 3)
    )
    
    last_reading_date = fields.Date(
        string='Last Reading Date',
       # compute='_compute_last_reading',
        store=True
    )

    # ========== COMPUTED METHODS ==========
    @api.depends('coordinates')
    def _compute_lat_lng(self):
        for meter in self:
            lat, lng = 0.0, 0.0
            if meter.coordinates:
                try:
                    coords = meter.coordinates.split(',')
                    if len(coords) == 2:
                        lat = float(coords[0].strip())
                        lng = float(coords[1].strip())
                except (ValueError, AttributeError):
                    pass
            meter.latitude = lat
            meter.longitude = lng

    # @api.depends('reading_ids')
    # def _compute_last_reading(self):
    #     for meter in self:
    #         last_reading = self.env['water.meter.reading'].search([
    #             ('meter_id', '=', meter.id)
    #         ], order='reading_date desc', limit=1)
    #         meter.last_reading = last_reading.value if last_reading else 0
    #         meter.last_reading_date = last_reading.reading_date if last_reading else False

    # ========== CONSTRAINTS & VALIDATIONS ==========
    @api.constrains('coordinates')
    def _check_coordinates(self):
        for meter in self:
            if meter.coordinates:
                if not re.match(r'^-?\d{1,3}\.\d+,-?\d{1,3}\.\d+$', meter.coordinates):
                    raise ValidationError(_("Invalid coordinates format. Use 'latitude,longitude' (e.g. '12.345,-12.345')"))

    @api.constrains('connection_date')
    def _check_connection_date(self):
        for meter in self:
            if meter.connection_date > fields.Date.today():
                raise ValidationError(_("Connection date cannot be in the future"))
    
    @api.constrains('house_number')
    def _check_house_number(self):
        for meter in self:
            if meter.house_number and not re.match(r'^[a-zA-Z0-9\-\/]+$', meter.house_number):
                raise ValidationError(_("House number can only contain alphanumeric characters, hyphens and slashes"))

    # ========== BUSINESS METHODS ==========
    # def action_view_readings(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': _('Meter Readings'),
    #         'view_mode': 'tree,form',
    #         'res_model': 'water.meter.reading',
    #         'domain': [('meter_id', '=', self.id)],
    #         'context': {
    #             'default_meter_id': self.id,
    #             'search_default_meter_id': self.id
    #         }
    #     }
    
    def action_disconnect(self):
        self.write({'status': 'disconnected'})
    
    def action_connect(self):
        self.write({'status': 'connected'})
    
    def action_block(self):
        self.write({'status': 'blocked'})



    def action_open_billing_meter_wizard(self):
        """Open the Billing Meter Wizard with the partner_id pre-filled."""
        self.ensure_one()  # Ensure the method is called for a single record
        return {
            'type': 'ir.actions.act_window',
            'name': 'Billing Meter Wizard',
            'res_model': 'billing.meter.wizard',
            'view_mode': 'form',
            'target': 'new',  # Open in a modal popup
            'context': {
                'default_partner_id': self.customer_id.id,  # Pass the partner_id
            },
        }


   