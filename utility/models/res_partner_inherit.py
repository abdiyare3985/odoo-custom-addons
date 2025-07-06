from odoo import models, fields, api

class ResPartnerInherit(models.Model):
    _inherit = 'res.partner'
    # _rec_names_search=['name', 'billing_account']
    
    billing_account = fields.Char(string="Billing Account")
    # billing_meter_id = fields.Many2one(
    #     comodel_name='billing.meter',
    #     string='Billing Meter',
    #     store=True,
    #     help='The billing meter associated with this customer'
    # )
    meter_ids = fields.One2many(
        'billing.meter', 
        'customer_id', 
        string="Meters",
        readonly=True
    ) 
    meter_id = fields.Many2one(
        'billing.meter',
        string='Meter ID',
       # compute='_compute_meter_fields',
        store=True
    )
    meter_name = fields.Char(
       
        string='Meter Name',
       # compute='_compute_meter_fields',
        store=True
    )
    # # meter_reading_ids = fields.One2many(
    # #     comodel_name='meter.reading',
    # #     inverse_name='meter_id',
    # #     string='Meter Readings',
    # #     related="meter_id.meter_reading_ids",
    # #     readonly=True
    # # )
    # meter_reading_ids = fields.One2many(
    #     comodel_name='meter.reading',
    #     inverse_name='meter_id',
    #     string='Meter Readings',
    #     compute='_compute_meter_readings',
    #     readonly=True
    # )

    # # Related fields from billing.meter
    meter_serial_number = fields.Char(
        string="Meter Serial Number",
        compute='_compute_meter_fields',
        readonly=True
    )
    meter_zone = fields.Char(
        #comodel_name="zone",
        string="Meter Zone",
        compute='_compute_meter_fields',
       # related="billing_meter_id.zone_id.name",
        readonly=True
    )
    meter_status = fields.Char(
        string="Meter Status",
        #related="billing_meter_id.status",
        compute='_compute_meter_fields',
        readonly=True
    )
    discount_name = fields.Char(
        string="Discount Name",
        related="meter_id.discount_id.name",
        store = False
    )
    # active_tab = fields.Selection([
    #     ('meter_info', 'Meter Info'),
    #     ('billing', 'Billing'),
    # ], string="Active Tab", default='meter_info')
    
    # meter_reading_count = fields.Integer(
    #     string="Meter Reading Count",
    #     compute="_compute_meter_reading_count",
    #     readonly=True
    # )

    # @api.depends('meter_id')
    # def _compute_meter_reading_count(self):
    #     for partner in self:
    #         if partner.meter_id:
    #             partner.meter_reading_count = self.env['meter.reading'].search_count([('meter_id', '=', partner.meter_id.id)])
    #         else:
    #             partner.meter_reading_count = 0


    # @api.depends('active_tab', 'meter_id')
    # def _compute_meter_readings(self):
    #     """Populate meter_reading_ids only when Billing tab is selected."""
    #     for partner in self:
    #         if partner.active_tab == 'billing' and partner.meter_id:
    #             print("Yeah, Billing tab is selected", partner.active_tab)
    #             partner.meter_reading_ids = partner.meter_id.meter_reading_ids
    #         else:
    #             print("No, Billing tab is not selected")
    #             partner.meter_reading_ids = False

    # @api.onchange('active_tab')
    # def _onchange_active_tab(self):
    #     if self.active_tab == 'billing':
    #         # Add your logic here when the Billing tab is selected
    #         print("Billing tab is opened")

    @api.depends('meter_ids')
    def _compute_meter_fields(self):
        print("Compute Meter STATUS")
        for partner in self:
            # if partner.meter_ids and int(partner.billing_account) > 0:
            if partner.meter_ids:
                # partner.meter_id=partner.meter_ids[0].id
                # partner.meter_name=partner.meter_ids[0].name
                # partner.meter_tariff_id = partner.meter_ids[0].tariff_id
                partner.meter_zone = partner.meter_ids[0].zone_id.name
                partner.meter_serial_number = partner.meter_ids[0].serial_id.serial_number
                partner.meter_status=partner.meter_ids[0].status
                print("WOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOW")
               # print(f"Meter of this customer is: {partner.meter_ids[0].status}")
            else:
                partner.meter_id=False
                partner.meter_name = False
                # partner.meter_tariff_id = False
                # partner.meter_zone_id = False
                # partner.meter_serial_id = False
                # print("STATUS DOES NOT EXIST")
                # #meter_status='Disconnected'
                partner.meter_status = False



    @api.depends('name', 'billing_account')
    def _compute_display_name(self):
        for record in self:
            name = record.name or ''
            if record.billing_account:
                name += " (" + record.billing_account + ")"
            record.display_name = name


    # def call_me(self):
    #     print("This is a test function in the res.partner model.")
    #     return True