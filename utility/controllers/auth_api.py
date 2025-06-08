from odoo import http
from odoo.http import request, Response
import json
import logging
from odoo.exceptions import AccessDenied

_logger = logging.getLogger(__name__)

class AuthAPI(http.Controller):
    
    @http.route('/api/auth/login', auth='none', type='http', methods=['POST'], csrf=False)
    def login(self, **post):
        """
        Authenticate user and establish session
        Sample payload:
        {
            "login": "admin",
            "password": "admin",
            "db": "production_db"
        }
        """
        try:
            # Get credentials from JSON payload
            data = json.loads(request.httprequest.data)
            login = data.get('login')
            password = data.get('password')
            db = data.get('db')
            
            if not all([login, password, db]):
                return Response(
                    json.dumps({
                        'status': 'error',
                        'message': 'Missing required parameters (login, password, db)'
                    }),
                    status=400,
                    content_type='application/json'
                )

            # Authenticate with Odoo's session manager
            request.session.authenticate(db, login, password)
            
            # Get the user context correctly
            user_context = request.env['res.users'].context_get()
            
            # Return session information
            return Response(
                json.dumps({
                    'status': 'success',
                    'session_id': request.session.sid,
                    'uid': request.session.uid,
                    'user_context': user_context,
                    'db': db,
                    'username': request.env.user.name,
                    'login': request.env.user.login
                }),
                status=200,
                content_type='application/json',
                headers=[('Set-Cookie', f'session_id={request.session.sid}; Path=/')]
            )
            
        except AccessDenied:
            _logger.warning("Login failed for db:%s login:%s", db, login)
            return Response(
                json.dumps({
                    'status': 'error',
                    'message': 'Invalid credentials'
                }),
                status=401,
                content_type='application/json'
            )
        except Exception as e:
            _logger.error("Login error: %s", str(e), exc_info=True)
            return Response(
                json.dumps({
                    'status': 'error',
                    'message': 'Internal server error'
                }),
                status=500,
                content_type='application/json'
            )
        
    @http.route('/api/auth/logout', auth='user', type='http', methods=['POST'], csrf=False)
    def logout(self):
        """
        Destroy current session
        """
        try:
            request.session.logout()
            return Response(
                json.dumps({
                    'status': 'success',
                    'message': 'Logged out successfully'
                }),
                status=200,
                content_type='application/json'
            )
        except Exception as e:
            _logger.error("Logout error: %s", str(e), exc_info=True)
            return Response(
                json.dumps({
                    'status': 'error',
                    'message': 'Logout failed'
                }),
                status=500,
                content_type='application/json'
            )
        
    @http.route('/api/meter/submit100', auth='user', type='json', methods=['POST'], csrf=False)
    def submit_meter_reading(self, **post):
        """
        Submit a meter reading (requires session authentication).
        Payload example:
        {
            "meter_id": 1,
            "prev_reading": 100,
            "current_reading": 120,
            "reading_date": "2025-06-07"
        }
        """
        try:
            user = request.env.user
            print("User ID:", user.id)
            session_id = request.session.sid
            print("Session ID:", session_id)
            data = request.get_json_data()
            meter_id = data.get('meter_id')
            prev_reading = data.get('prev_reading')
            current_reading = data.get('current_reading')
            reading_date = data.get('reading_date')

            if not all([meter_id, prev_reading, current_reading, reading_date]):
                return {
                    'status': 'error',
                    'message': 'Missing required parameters'
                }
            
            #reading = request.env['meter.reading'].with_context(from_api=True).sudo(user).create(reading_vals) 

            reading = request.env['meter.reading'].sudo().create({
                'meter_id': meter_id,
                'prev_reading': prev_reading,
                'current_reading': current_reading,
                'consumption': float(current_reading) - float(prev_reading),
                'reading_date': reading_date,
            })

            return {
                'status': 'success',
                'message': 'Meter reading submitted',
                'reading_id': reading.id,
                'user_id': user.id,
                'username': user.name,
            }
        except Exception as e:
            _logger.error("Meter reading error: %s", str(e), exc_info=True)
            return {
                'status': 'error',
                'message': 'Internal server error'
            }
        

    @http.route('/api/v1/meters/by-zone', auth='user', type='http', methods=['GET'], csrf=False)
    def get_meters_by_zone(self, **kwargs):
       
        print(f"get_meters_by_zone called ")
        try:
        # Get the 'zone' parameter from the query string
         zone_id = request.httprequest.args.get('zone_id')
         if not zone_id:
            return Response(
                json.dumps({
                    'status': 'error',
                    'message': 'Missing required parameter: zone'
                }),
                status=400,
                content_type='application/json'
            )

        # Search for meters in the given zone
         meters = request.env['billing.meter'].sudo().search([('zone_id', '=', int(zone_id))])
         meter_list = []
         for meter in meters:
            meter_list.append({
                'id': meter.id,
                'name': meter.customer_id.name,
                'serial': getattr(meter, 'serial_number', ''),
                'zone_id': meter.zone_id.id if meter.zone_id else None,
                'status': meter.status,
                'zone_name': meter.zone_id.name if meter.zone_id else '',
            })

         return Response(
            json.dumps({
                'status': 'success',
                'message': 'Meters fetched successfully',
                'data': meter_list,
            }),
            status=200,
            content_type='application/json'
        )
        except Exception as e:
         _logger.error("API Error: %s", str(e), exc_info=True)
        return Response(
            json.dumps({
                'status': 'error',
                'message': 'Internal server error'
            }),
            status=500,
            content_type='application/json'
        )
        