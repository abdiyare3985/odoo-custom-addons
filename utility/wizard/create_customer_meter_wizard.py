from odoo import fields,models,api, _

class CreateCustomerMeterWizard(models.TransientModel):
    _name="create.customer.meter.wizard"
    _description=""

    lead_id = fields.Many2one('crm.lead', string="Opportunity", required=True)
    customer_name = fields.Char(string='Customer Name', required=True)
    phone = fields.Char(string='Phone')
    email = fields.Char(string='Email')

    name = fields.Char(
        string='Meter ID',
        
        index=True,
        tracking=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('water.meter'),
        help="Unique meter identification number"
    )
    
    serial_id = fields.Many2one(
        'meter.serial',
        string='Serial Number',
        required=True,
        domain="[('state','=','available')]",
        ondelete='restrict',
        tracking=True
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
    

    @api.depends('coordinates')
    def _compute_lat_lng(self):
        for wizard in self:
            lat, lng = 0.0, 0.0
            if wizard.coordinates:
                try:
                    coords = wizard.coordinates.split(',')
                    if len(coords) == 2:
                        lat = float(coords[0].strip())
                        lng = float(coords[1].strip())
                except (ValueError, AttributeError):
                    pass
            wizard.latitude = lat
            wizard.longitude = lng

    def action_create_meter(self):
        self.ensure_one()
        print("Creating new Meter")
        print(f"Customer Name: {self.customer_name}")
        customer = self.env['res.partner'].create({
            'name':self.customer_name,
            'phone':self.phone,
            'email':self.email,
            'customer_rank':100
        })

        # Executing raw SQL query in Odoo
        # self.env.cr.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM billing_meter")
        # new_id = self.env.cr.fetchone()[0]
        # print(f"new id is: {new_id}")

        # Get the maximum meter name (assuming it's numeric)
        last_meter = self.env['billing.meter'].search([], order='name desc', limit=1)
        if last_meter and last_meter.name:
         new_id = int(last_meter.name) + 1
        else:
         new_id = 1  # Default to 1 if no meters exist or name is not numeric

        print(f"New Meter ID: {new_id}")



        # last_meter = self.env['water.meter'].search([], order='id desc', limit=1)
        # last_id = last_meter.id if last_meter else 1
        # new_id = last_id + 1

        meter = self.env['billing.meter'].create({
            'name':new_id,
            'serial_id': self.serial_id.id,
            'customer_id': customer.id,
            'zone_id': self.zone_id.id,
            'group_id': self.group_id.id,
            'coordinates': self.coordinates,
            'house_number': self.house_number,
            'street': self.street,
            'area': self.area,
            'connection_date': self.connection_date,
            'status': 'connected',
            'tariff_id': self.tariff_id.id,
            'discount_id': self.discount_id.id,
            
        })
        print(f"ID created after meter: {meter.id}")
        print(f"new_id after meter: {new_id}")
        

        customer.billing_account=meter.name
        customer.meter_name= meter.name
        customer.meter_id = meter.id
        self.lead_id.partner_id = customer.id
        self.lead_id.meter_id = meter.id
        self.lead_id.meter_name=meter.name

        # Create the water meter
        # meter = self.env['water.meter'].create({
        #     'name': self.name,
        #     'serial_id': self.serial_id.id,
        #     'customer_id': self._prepare_customer().id,
        #     'zone_id': self.zone_id.id,
        #     'group_id': self.group_id.id,
        #     'coordinates': self.coordinates,
        #     'house_number': self.house_number,
        #     'street': self.street,
        #     'area': self.area,
        #     'connection_date': self.connection_date,
        #     'status': 'Connected',
        #     'tariff_id': self.tariff_id.id,
        #     'discount_id': self.discount_id.id,
        # })
        
        # Link to the opportunity if needed
        # if self.lead_id:
        #     self.lead_id.write({
        #         'water_meter_id': meter.id,
        #         'stage_id': self.env.ref('water_utility.stage_lead_meter_installed').id
        #     })
       

        # Return action to view the created meter
        return {
            'type': 'ir.actions.act_window',
            'name': 'Water Meter',
            'view_mode': 'form',
            'res_model': 'crm.lead',
            'res_id': self.lead_id.id,
            'target': 'current',
        }
        pass

    def _prepare_customer(self):
        """Create or find existing customer"""
        partner = self.env['res.partner'].search([
            '|',
            ('email', '=', self.email),
            ('phone', '=', self.phone),
            ('customer_rank', '>', 0)
        ], limit=1)
        
        if not partner:
            partner = self.env['res.partner'].create({
                'name': self.customer_name,
                'phone': self.phone,
                'email': self.email,
                'customer_rank': 1
            })
        return partner
    

