from odoo import http, tools
from odoo.http import request, Response
import json
import logging
from datetime import datetime
from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)
from dateutil.relativedelta import relativedelta

class MeterReadingAPI(http.Controller):
    
    def _validate_api_key(self, api_key):
        """ Validate the API key """
        return request.env['res.users.apikeys']._check_credentials(scope='rpc', key=api_key)
    
    def _json_response(self, data=None, message='', status=200):
        """ Standard JSON response format """
        return Response(
            json.dumps({
                'status': status,
                'message': message,
                'data': data or {},
            }),
            content_type='application/json',
            status=status
        )
    
    def _validate_reading_data(self, data):
        """ Validate incoming reading data """
        required_fields = ['meter_id', 'prev_reading', 'current_reading', 'reading_date']
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        if not isinstance(data['current_reading'], (int, float)) or data['current_reading'] < 0:
            raise ValueError("Current reading must be a positive number")
        
        if data['prev_reading'] > data['current_reading']:
            raise ValueError("Current reading must be greater than or equal to previous reading")
        
        try:
            datetime.strptime(data['reading_date'], '%Y-%m-%d')
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
        
    def calculate_bill_amount(self,meter_id, consumption, tariff, fixed_charge, discount_percentage):
        """ Calculate the bill amount based on consumption and tariff """
        if not tariff:
            return 0.0
        # # Calculate amount based on consumption and tariff
        # amount = (consumption * tariff.rate) + fixed_charge
        # # Apply discount if applicable
        # if discount_percentage > 0:
        #     amount -= (amount * (discount_percentage / 100))
        #return round(amount, 2)
        amount = 0.0
        amount_before_discount = 0.0
        
        
            
           
            
            
        amount += fixed_charge
        amount_before_discount += fixed_charge

        if tariff.pricing_method == 'block_rate':
                remaining = consumption
                i=1
                for block in tariff.block_ids.sorted('sequence'):
                    if remaining <= 0: 
                        break
                    block_consumption = (
                        min(remaining, block.limit) 
                        if block.limit > 0 
                        else remaining
                    )
                    print(f"Block Rate: {block.rate}")
                    amount += block_consumption * block.rate
                    amounttwo = block_consumption * block.rate
                    print(f"{block_consumption} * {block.rate} : {amounttwo}")
                    remaining -= block_consumption
                    i=i+1
                    
        elif tariff.pricing_method == 'consumption_based':
                amount += consumption * tariff.consumption_rate
                rate=tariff.consumption_rate
                
        elif tariff.pricing_method == 'range_based':
                 applicable_range = tariff.range_ids.sorted('min_value').filtered(
                 lambda r: (r.min_value <= consumption) and 
                 (not r.max_value or consumption <= r.max_value))
    
                 if applicable_range:
                    amount += consumption * applicable_range[0].rate  # Multiply consumption by range rate
                    rate = applicable_range[0].rate
                 else:
        # Fallback: Use the highest range's rate if consumption exceeds all ranges
                     highest_range = tariff.range_ids.sorted('min_value', reverse=True)[:1]
                     if highest_range:
                        amount += consumption * highest_range[0].rate  # Multiply consumption by high
                        
                        print(f"highest_range[0].rate: {highest_range[0].rate}")

                     #record.rate = highest_range[0].rate
        amount_before_discount = amount - fixed_charge
        taxes = self.meter_id.tariff_id.taxes_id
        net_bill = amount_before_discount
            
            
            # Apply discount only to consumption portion if needed
        if discount_percentage:
                consumption_amount = amount - fixed_charge
                print(f"consumption_amount: {consumption_amount}")
                discounted_consumption = consumption_amount * (1 - (discount_percentage / 100))
                print(f"discounted_consumption: {discounted_consumption}")
                amount = fixed_charge + discounted_consumption
                print(f"amount after discount: {amount}")

        for tax in taxes:
                print(f"Tax {tax.name}: {tax.amount}%")
                print(f"discounted_consumption: {discounted_consumption}")
                tax_amount = (tax.amount/100) * discounted_consumption
        

        
        amount_before_discount = tools.float_round(amount_before_discount, precision_digits=2)

        amount = tools.float_round(amount, precision_digits=2) + tax_amount

        reading_vals = {
                'meter_id': meter_id,
                'prev_reading': float('prev_reading'),
                'current_reading': float('current_reading'),
                'consumption': consumption,
                'reading_date': 'reading_date',
            }
        

    def get_bill_period(self, reading_date):
        """ Compute billing period with date validation """
        bill_period = False
        if not reading_date:
           bill_period = False
           return bill_period
            
            # Skip validation during onchange to avoid blocking form opening
        
            
        if isinstance(reading_date, str):
           reading_date = datetime.strptime(reading_date, '%Y-%m-%d').date()

        if reading_date.day >= 22:
           bill_date = reading_date
        else:
           bill_date = reading_date + relativedelta(months=-1)

        bill_period = bill_date.strftime('%Y-%m')
        return bill_period
    
    def _get_user_from_api_key(self, api_key):
    # Use Odoo's built-in API key check
     api_key_model = request.env['res.users.apikeys'].sudo()
     key_record = api_key_model.search([('index', '=', api_key[:8])], limit=1)
     if key_record and key_record._check_credentials(scope='rpc', key=api_key):
        return key_record.user_id
     return request.env.user
           
    @http.route('/api/v1/meter-readings', type='json', auth='none', methods=['POST'], csrf=False)
    def submit_reading(self, **kwargs):
        print("submit_reading called")

        api_key = request.httprequest.headers.get('Authorization', '').replace('Bearer ', '')
        print(f"API Key: {api_key}")

    # This will raise if the key is invalid, and set the user context if valid
        user = None
        try:
        # Find the API key record (Odoo 17: use 'id' field, not 'key' or 'prefix')
         api_key_model = request.env['res.users.apikeys'].sudo()
         key_record = api_key_model.search([], limit=1000)  # get all, filter below
         for rec in key_record:
            try:
                if rec._check_credentials(scope='rpc', key=api_key):
                    user = rec.user_id
                    break
            except Exception:
                continue
         if not user:
            return {'status': 401, 'message': 'Invalid API key'}
        except Exception:
         return {'status': 401, 'message': 'Invalid API key'}

        print(f"User ID: {user.id}, Login: {user.login}, Name: {user.name}")

        # api_key = request.httprequest.headers.get('Authorization', '').replace('Bearer ', '')
        
        # if not self._validate_api_key(api_key):
        #    return {'status': 401, 'message': 'Invalid API key'}
        
        # #api_key1 = '$pbkdf2-sha512$6000$uhdCKEVo7Z3z3rt3rrX2vg$AzKLkapCZT93tWxC7Tp0TDDb6oqOhyLONBveYKe4dCQx.R/7TcJ3.d/MLTLA9RQtDbaMqET3gbCVbpLzg8gpBQ'
        
        # user = self._get_user_from_api_key(api_key)
        # print(f"User ID: {user.id}, Login: {user.login}, Name: {user.name}")

    # 2. Parse JSON data
        data = request.get_json_data()
        print(f"Received data: {data}")
        meter = request.env['billing.meter'].sudo().browse(int(data['meter_id']))
        if not meter.exists():
            return {'status': 404, 'message': 'Meter not found'}
        print(f"Meter found: {meter.name} (ID: {meter.id})")

        tariff = meter.tariff_id
        if not tariff:
            return {'status': 400, 'message': 'Meter does not have an associated tariff'}
        
        
        
        print(f"Tariff found: {tariff.name}")

        # discount_percentage = meter.discount_id.percentage if meter.discount_id else 0.0

        # fixed_charge = tariff.fixed_charge if tariff.fixed_charge else 0.0

        #print(f"Fixed Charge: {fixed_charge}, Discount: {discount_percentage}%")

        # Get taxes from the product (tariff)
        # taxes = tariff.taxes_id  # This is a recordset of account.tax

       

        consumption = float(data['current_reading']) - float(data['prev_reading'])
        print(f"Consumption calculated: {consumption} m³")
        

        # amount = 0.0
        # discount_amount = 0.0
        # tax_amount = 0.0
        # amount_with_discount = 0.0
        # bill_period = self.get_bill_period(data.get('reading_date', datetime.now().strftime('%Y-%m-%d')))
        


        # if tariff.pricing_method == 'range_based':
        #     applicable_range = tariff.range_ids.sorted('min_value').filtered(
        #          lambda r: (r.min_value <= consumption) and 
        #          (not r.max_value or consumption <= r.max_value))
    
        #     if applicable_range:
        #             amount += consumption * applicable_range[0].rate  # Multiply consumption by range rate
        #             rate = applicable_range[0].rate

        # display_name = (
        #             f"{meter.name}/{bill_period} "
        #             f"(Consumption: {consumption:.2f}, Amount: {amount:.2f})"
        #         )

        # print(f"Amount for applicable range: {rate}")
        # print(f"Amount: {amount}")
        # print(f"Consumption: {consumption}")
        # print(f"Fixed Charge: {fixed_charge}")
        # print(f"Discount Percentage: {discount_percentage}")
        
        # print(f"Tax : {taxes.amount}")
        # print(f"Bill Period: {bill_period}")
        # print(f"Display Name: {display_name}")

        # discount_amount = (amount * discount_percentage / 100) if discount_percentage else 0.0
        # print(f"Discount Amount: {discount_amount}")
        # bill_amount = amount - discount_amount + fixed_charge
        # tax_amount = taxes.amount / 100 * (amount - discount_amount) if taxes else 0.0
        # taxed_bill_amount = bill_amount + tax_amount
        # print(f"Bill Amount: {bill_amount}")
        # print(f"Tax Amount: {tax_amount}")
        # reading_date = data.get('reading_date', datetime.now().strftime('%Y-%m-%d'))
        # reading_vals = {
        #     'meter_id': meter.id,
        #     'prev_reading': float(data['prev_reading']),
        #     'current_reading': float(data['current_reading']),
        #     'consumption': consumption,
        #     'amount': amount,
        #     'net_bill': bill_amount,
        #     #'bill_period': data.get('bill_period', ''),
        #     #'tariff_id': tariff.id,
        #     'fixed_charge': fixed_charge,
        #     'discount_percentage': discount_percentage,
        #     'discount_amount': discount_amount,
        #     'tax_amount': taxed_bill_amount,
        #     'rate': rate,
        #     'display_name': display_name,
        #     'bill_period': bill_period,
        #     'reading_date': reading_date,
        #     #'is_invoiced': data.get('is_invoiced', False),
        #     #'customer': meter.customer_id.id if meter.customer_id else False,
            
        #     #'reading_date': data['reading_date'],
        # }
        reading_vals2 = {
            'meter_id': meter.id,
            'prev_reading': float(data['prev_reading']),
            'current_reading': float(data['current_reading']),
            'consumption': consumption,
        }
        # reading = request.env['meter.reading'].sudo().create(reading_vals)
        # In your controller, when creating the reading:
        #reading = request.env['meter.reading'].with_context(from_api=True).sudo().create(reading_vals)
        #reading = request.env['meter.reading'].with_context(from_api=True).sudo(user).create(reading_vals)  
        print(f"request.env.user.id: {request.env.user.id}")
        #reading = request.env['meter.reading'].with_context(from_api=True).sudo(request.env.user.id).create(reading_vals)
       # After you have the user (a res.users record)
        user_env = request.env(user=user)
        reading = user_env['meter.reading'].with_context(from_api=True).create(reading_vals2)
        # 7. Return success response
        return {
            'status': 200,
            'message': 'Reading created successfully',
            'reading_id': reading.id,
            'consumption': reading.consumption,
            'amount': reading.amount,
            'invoice_id': reading.invoice_id.id if reading.invoice_id else None,
        }
        
        
        
     
        







    @http.route('/api/v1/meter-readingsOLD', auth='none', type='json', methods=['POST'], csrf=False)
    def submit_reading2(self, **kwargs):
        print("submit_reading called")
        try:
            data = request.get_json_data()
            print(f"Received data: {data}")
            api_key = request.httprequest.headers.get('Authorization', '').replace('Bearer ', '')
            if not self._validate_api_key(api_key):
                return {'status': 401, 'message': 'Invalid API key'}
            print(f"API key validated: {api_key}")
            meter = request.env['billing.meter'].sudo().browse(int(data['meter_id']))

            reading_vals = {
                'meter_id': meter.id,
               # 'prev_reading': float(data['prev_reading']),
                'current_reading': float(data['current_reading']),
                #'consumption': consumption,
                #'reading_date': data['reading_date'],
            }
            reading = request.env['meter.reading'].sudo().create(reading_vals)
            print(f"Reading created with ID: {reading.id}")
            reading.action_create_invoice()
            
        except Exception as e:
            _logger.error("Error in submit_reading: %s", str(e), exc_info=True)
            return self._json_response(None, 'Server error', 500)

            
   
   
   
   
    def submit_readingOld(self, **kwargs):
        """ Submit a new meter reading """
        try:
            # For type='json', data is in kwargs
            #data = kwargs
            data = request.get_json_data()
            # Authenticate
            api_key = request.httprequest.headers.get('Authorization', '').replace('Bearer ', '')
            if not self._validate_api_key(api_key):
                return {'status': 401, 'message': 'Invalid API key'}
            
            print(f"Received data: {data}")
            # Validate data
            self._validate_reading_data(data)

            
            
            # Find meter
            #meter = request.env['billing.meter'].browse(int(data['meter_id']))
            meter = request.env['billing.meter'].sudo().browse(int(data['meter_id']))
            if not meter.exists():
                return {'status': 404, 'message': 'Meter not found'}
            print(f"Meter found: {meter.name} (ID: {meter.id})")
            # Prepare reading values
            consumption = float(data['current_reading']) - float(data['prev_reading'])
            tariff = meter.tariff_id
            fixed_charge = tariff.fixed_charge
            print(f"Tariff found: {tariff.name}, Fixed Charge: {fixed_charge}")
            discount_percentage = meter.discount_id.percentage if meter.discount_id else 0.0
            print(f"Consumption calculated: {consumption}, Discount: {discount_percentage}%")

            # reading_vals = request.env['meter.reading'].create({
            #      'meter_id': meter.id,
            #     #'prev_reading': float(data['prev_reading']),
            #     'current_reading': float(data['current_reading']),
            #     #'consumption': consumption,
            #     'reading_date': data['reading_date'],
            #     })
     

            
            reading_vals = {
                'meter_id': meter.id,
               # 'prev_reading': float(data['prev_reading']),
                'current_reading': float(data['current_reading']),
                #'consumption': consumption,
                #'reading_date': data['reading_date'],
            }
            #print(f"Reading values prepared: {reading_vals}")
            # Auto-calculate previous reading if not provided
            # if 'prev_reading' not in data:
            #     last_reading = request.env['meter.reading'].search([
            #         ('meter_id', '=', meter.id)
            #     ], order='reading_date desc', limit=1)
            #     reading_vals['prev_reading'] = last_reading.current_reading if last_reading else 0.0

                
           # print(f"Previous reading set to: {reading_vals['prev_reading']}")
            # Create reading
            reading = request.env['meter.reading'].sudo().create(reading_vals)
            print(f"Reading created with ID: {reading.id}")
            # Auto-create invoice if configured to do so
            if data.get('auto_invoice', False):
                 reading.action_create_invoice()
            
            # Prepare response
            response_data = {
                'reading_id': reading.id,
                'meter_id': reading.meter_id.id,
                'customer': reading.customer,
                'consumption': reading.consumption,
                'amount': reading.amount,
                'invoice_id': reading.invoice_id.id if reading.is_invoiced else None,
                'bill_period': reading.bill_period,
            }
            print(f"Response data prepared: {response_data}")
            return {'status': 200, 'message': 'Reading submitted successfully', 'data': response_data}
            
        except ValueError as e:
            return {'status': 400, 'message': str(e)}
        except Exception as e:
            _logger.error("API Error: %s", str(e), exc_info=True)
            return {'status': 500, 'message': 'Server error'}

    @http.route('/api/v1/meter-readings/<int:reading_id>', auth='none', type='http', methods=['GET'], csrf=False)
    def get_reading(self, reading_id, **kwargs):
        """ Get details of a specific reading """
        try:
            # Authenticate
            api_key = request.httprequest.headers.get('Authorization', '').replace('Bearer ', '')
            if not self._validate_api_key(api_key):
                return self._json_response(None, 'Invalid API key', 401)
            
            # Find reading
            reading = request.env['meter.reading'].sudo().browse(reading_id)
            if not reading.exists():
                return self._json_response(None, 'Reading not found', 404)
            
            # Prepare response
            response_data = {
                'reading_id': reading.id,
                'meter_id': reading.meter_id.id,
                'customer': reading.customer,
                'prev_reading': reading.prev_reading,
                'current_reading': reading.current_reading,
                'consumption': reading.consumption,
                'reading_date': str(reading.reading_date),
                'bill_period': reading.bill_period,
                'amount': reading.amount,
                'is_invoiced': reading.is_invoiced,
                'invoice_id': reading.invoice_id.id if reading.is_invoiced else None,
                'invoice_status': reading.state if reading.is_invoiced else None,
            }
            
            return self._json_response(response_data)
            
        except Exception as e:
            _logger.error("API Error: %s", str(e), exc_info=True)
            return self._json_response(None, 'Server error', 500)
        

    @http.route('/api/v1/meters/by-zone1', type='json', auth='none', methods=['GET'], csrf=False)
    def get_meters_by_zone(self, **kwargs):
     """Return a list of meters filtered by zone_id"""
     try:
        api_key = request.httprequest.headers.get('Authorization', '').replace('Bearer ', '')
        # Validate API key
        user = None
        api_key_model = request.env['res.users.apikeys'].sudo()
        key_record = api_key_model.search([], limit=1000)
        for rec in key_record:
            try:
                if rec._check_credentials(scope='rpc', key=api_key):
                    user = rec.user_id
                    break
            except Exception:
                continue
        if not user:
            return {'status': 401, 'message': 'Invalid API key'}

        data = request.get_json_data()
        zone_id = data.get('zone_id')
        if not zone_id:
            return {'status': 400, 'message': 'zone_id is required'}
        print(f"Zone ID: {zone_id}")

        user_env = request.env(user=user)
        meters = user_env['billing.meter'].search([('zone_id', '=', zone_id)])

        meter_list = []
        for meter in meters:
            meter_list.append({
                'id': meter.id,
                'name': meter.customer_id.name,
                'serial': meter.serial_number if hasattr(meter, 'serial_number') else '',
                'zone_id': meter.zone_id.id if meter.zone_id else None,
                'zone_name': meter.zone_id.name if meter.zone_id else '',
            })

        return {
            'status': 200,
            'message': 'Meters fetched successfully',
            'data': meter_list,
        }
     except Exception as e:
        _logger.error("API Error: %s", str(e), exc_info=True)
        return {'status': 500, 'message': 'Server error'}
     

    @http.route('/api/v1/login', type='json', auth='none', methods=['POST'], csrf=False)
    def api_login(self, **kwargs):
     try:
        data = request.get_json_data()
        db = data.get('db') or request.env.cr.dbname
        login = data.get('login')
        password = data.get('password')
        if not login or not password:
            return {'status': 400, 'message': 'Missing login or password'}

        # Manually call the controller
        from odoo.http import Controller, route, request as odoo_request
        params = {
            'db': db,
            'login': login,
            'password': password,
        }
        # Simulate a JSON-RPC call to /web/session/authenticate
        result = request.env['ir.model'].sudo()._jsonrpc('/web/session/authenticate', params)
        if not result.get('result', {}).get('uid'):
            return {'status': 401, 'message': 'Invalid credentials'}

        return {
            'status': 200,
            'message': 'Login successful',
            'user_id': result['result']['uid'],
            # session_id is set in cookies automatically
        }
     except Exception as e:
        _logger.error("Login API Error: %s", str(e), exc_info=True)
        return {'status': 500, 'message': 'Server error'}