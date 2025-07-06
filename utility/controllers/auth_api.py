from odoo import http
from odoo.http import request, Response
import json
import logging
from odoo.exceptions import AccessDenied
from datetime import date
from calendar import monthrange
from collections import defaultdict

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
            print("Received data:", data)
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
            v = request.session.authenticate(db, login, password)
            print(f"Authentication result: {v}")
            user = request.env['res.users'].sudo().browse(v)
            print(f"User ID: {user.id}, User Name: {user.name}")
            # Get the user context correctly
            user_context = request.env['res.users'].context_get()
            print(f"User context: {user_context}")
            
            
            # Return session information
            return Response(
                json.dumps({
                    'status': 'success',
                    'session_id': request.session.sid,
                    'uid': request.session.uid,
                    'is_technitian': user.is_technitian,
                    'is_meterreader': user.is_meterreader,
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
            print("Received data:", data)
            # Check if meter exists
            meter = request.env['billing.meter'].sudo().search([('id', '=', meter_id)], limit=1)
            if not meter:
             return {
                'status': 'error',
                'message': f'Meter with id {meter_id} does not exist'
            }
            print("Meter found:", meter.name)

            # if not all([meter_id, prev_reading, current_reading, reading_date]):
            #     return {
            #         'status': 'error',
            #         'message': 'Missing required parameters100'
            #     }
            
            #reading = request.env['meter.reading'].with_context(from_api=True).sudo(user).create(reading_vals) 
            print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
            reading = request.env['meter.reading'].sudo().create({
                'meter_id': meter_id,
                'prev_reading': prev_reading,
                'current_reading': current_reading,
                'consumption': float(current_reading) - float(prev_reading),
                'reading_date': reading_date,
            })
            print('YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY')

            completed = {

                'reading_id': reading.id,
                'meter_id': meter.id,
                'name': meter.customer_id.name,
                'serial': getattr(meter, 'serial_number', ''),
                'zone_id': meter.zone_id.id if meter.zone_id else None,
                'status': meter.status,
                'zone_name': meter.zone_id.name if meter.zone_id else '',
                'reading_date': reading.reading_date.strftime('%Y-%m-%d') if reading.reading_date else '',
                'current_reading': reading.current_reading,
                'prev_reading': reading.prev_reading,
                'consumption': reading.consumption,
            }

            return {
                'status': 'success',
                'message': 'Meter reading submitted',
                'reading_id': reading.id,
                'user_id': user.id,
                'username': user.name,
                'data': completed
            }
        except Exception as e:
            _logger.error("Meter reading error: %s", str(e), exc_info=True)
            return {
                'status': 'error',
                'message': 'Internal server error'
            }
        

    # @http.route('/api/v1/meters/by-zone', auth='user', type='http', methods=['GET'], csrf=False)
    # def get_meters_by_zone(self, **kwargs):
    #     session_id = request.session.sid
    #     print("Session ID:", session_id)
    #     print(f"get_meters_by_zone called ")
    #     try:
         
    #     # Get the 'zone' parameter from the query string
    #      zone_id = request.httprequest.args.get('zone_id')
    #      if not zone_id:
    #         return Response(
    #             json.dumps({
    #                 'status': 'error',
    #                 'message': 'Missing required parameter: zone'
    #             }),
    #             status=400,
    #             content_type='application/json'
    #         )

    #     # Search for meters in the given zone
    #      meters = request.env['billing.meter'].sudo().search([('zone_id', '=', int(zone_id))])
    #      meter_list = []
    #      for meter in meters:
    #         meter_list.append({
    #             'id': meter.id,
    #             'name': meter.customer_id.name,
    #             'serial': getattr(meter, 'serial_number', ''),
    #             'zone_id': meter.zone_id.id if meter.zone_id else None,
    #             'status': meter.status,
    #             'zone_name': meter.zone_id.name if meter.zone_id else '',
    #         })

    #      return Response(
    #         json.dumps({
    #             'status': 'success',
    #             'message': 'Meters fetched successfully',
    #             'data': meter_list,
    #         }),
    #         status=200,
    #         content_type='application/json'
    #     )
    #     except Exception as e:
    #      _logger.error("API Error: %s", str(e), exc_info=True)
    #     return Response(
    #         json.dumps({
    #             'status': 'error',
    #              'message': 'Missing required parameter: zone',
    #              'session_id': session_id,
    #              'session_uid': request.session.uid,
    #              'user_id': request.env.user.id,
    #         }),
    #         status=500,
    #         content_type='application/json'
    #     )

    @http.route('/api/v1/meters', auth='user', type='http', methods=['GET'], csrf=False)
    def get_meters_by_zone(self, **kwargs):
     session_id = request.session.sid
     print("Session ID:", session_id)
     print(f"get_meters_by_zone called ")
     try:
        # Get zones assigned to the current user as collector
        collector_id = request.env.user.id
        zones = request.env['billing.zone'].sudo().search([('collector_id', '=', collector_id)])
        if not zones:
            return Response(
                json.dumps({
                    'status': 'error',
                    'message': 'No zone assigned to this user',
                    'data': [],
                }),
                status=404,
                content_type='application/json'
            )
        zone_ids = zones.ids

        # Get meters in these zones
        meters = request.env['billing.meter'].sudo().search([('zone_id', 'in', zone_ids)])
        meter_list = []
        for meter in meters:
            partner = meter.customer_id
            # Calculate balance due (receivable)
            balance_due = round(partner.credit, 2)  # This is the usual "amount due" for the partner in Odoo
            meter_list.append({
                'id': meter.id,
                'name': meter.customer_id.name,
                'serial': getattr(meter, 'serial_number', ''),
                'zone_id': meter.zone_id.id if meter.zone_id else None,
                'status': meter.status,
                'zone_name': meter.zone_id.name if meter.zone_id else '',
                'balance_due': balance_due,
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
     
    @http.route('/api/meters/missing-readings', auth='user', type='http', methods=['GET'], csrf=False)
    def get_meters_missing_readings(self, **kwargs):
     print("Session ID:", request.session.sid)
     try:
        today = date.today()
        day = today.day
        month = today.month
        year = today.year
        print(f"get_meters_missing_readings called for date: {today}")

        # Determine period as last day of current or previous month
        if 22 <= day <= 31:
            last_day = monthrange(year, month)[1]
            period_date = today.replace(day=last_day)
        else:
            if month == 1:
                prev_month = 12
                prev_year = year - 1
            else:
                prev_month = month - 1
                prev_year = year
            last_day = monthrange(prev_year, prev_month)[1]
            period_date = today.replace(year=prev_year, month=prev_month, day=last_day)
        period_str = period_date.strftime('%Y-%m-%d')

        collector_id = request.env.user.id
        zone_ids = request.env['billing.zone'].sudo().search([('collector_id', '=', collector_id)]).ids

        # Find all meters
        all_meters = request.env['billing.meter'].sudo().search([('zone_id', 'in', zone_ids)])
        # Find all meter readings for this period
        readings = request.env['meter.reading'].sudo().search([('bill_period', '=', period_str)])
        meters_with_readings = set(readings.mapped('meter_id').ids)

        # Meters missing readings
        missing_meters = all_meters.filtered(lambda m: m.id not in meters_with_readings)

        meter_list = []
        for meter in missing_meters:
            # Get last posted reading for this meter
            last_reading = request.env['meter.reading'].sudo().search(
                [('meter_id', '=', meter.id), ('state', '=', 'posted')],
                order='reading_date desc, create_date desc',
                limit=1
            )
            meter_list.append({
                'id': meter.id,
                'name': meter.customer_id.name,
                'serial': getattr(meter, 'serial_number', ''),
                'zone_id': meter.zone_id.id if meter.zone_id else None,
                'status': meter.status,
                'zone_name': meter.zone_id.name if meter.zone_id else '',
                'last_reading': last_reading.current_reading if last_reading else 0,
                'last_reading_date': last_reading.reading_date.strftime('%Y-%m-%d') if last_reading and last_reading.reading_date else None,
            })

        return Response(
           json.dumps({
                'status': 'success',
                'message': f'Meters missing readings for period {period_str}',
                'period': period_str,
                'data': meter_list,
            }),
            status=200,
            content_type='application/json'
        )
     except Exception as e:
        _logger.error("Missing readings API error: %s", str(e), exc_info=True)
        return Response(
            json.dumps({
                'status': 'error',
                'message': 'Internal server error'
            }),
            status=500,
            content_type='application/json'
        )
        
    # @http.route('/api/meters/missing-readings', auth='user', type='http', methods=['GET'], csrf=False)
    # def get_meters_missing_readings(self, **kwargs):
    #     print("Session ID:", request.session.sid)
    #     try:
    #         today = date.today()
    #         day = today.day
    #         month = today.month
    #         year = today.year
    #         print(f"get_meters_missing_readings called for date: {today}")

    #         # Determine period as last day of current or previous month
    #         if 22 <= day <= 31:
    #             last_day = monthrange(year, month)[1]
    #             period_date = today.replace(day=last_day)
    #         else:
    #             if month == 1:
    #                 prev_month = 12
    #                 prev_year = year - 1
    #             else:
    #                 prev_month = month - 1
    #                 prev_year = year
    #             last_day = monthrange(prev_year, prev_month)[1]
    #             period_date = today.replace(year=prev_year, month=prev_month, day=last_day)
    #         period_str = period_date.strftime('%Y-%m-%d')

    #         collector_id = request.env.user.id
    #         zone_ids = request.env['billing.zone'].sudo().search([('collector_id', '=', collector_id)]).ids

    #         # Find all meters
    #         all_meters = request.env['billing.meter'].sudo().search([('zone_id', 'in', zone_ids)])
    #         # Find all meter readings for this period
    #         readings = request.env['meter.reading'].sudo().search([('bill_period', '=', period_str)])
    #         meters_with_readings = set(readings.mapped('meter_id').ids)

    #         # Meters missing readings
    #         missing_meters = all_meters.filtered(lambda m: m.id not in meters_with_readings)

    #         meter_list = []
    #         for meter in missing_meters:
    #             last_reading = request.env['meter.reading'].sudo().search(
    #             [('meter_id', '=', meter.id), ('state', '=', 'posted')],
    #             order='reading_date desc, create_date desc',
    #             limit=1
    #         )
    #             meter_list.append({
    #                 'id': meter.id,
    #                 'name': meter.customer_id.name,
    #                 'serial': getattr(meter, 'serial_number', ''),
    #                 'zone_id': meter.zone_id.id if meter.zone_id else None,
    #                 'status': meter.status,
    #                 'zone_name': meter.zone_id.name if meter.zone_id else '',
    #                 'last_reading': last_reading.current_reading if last_reading else None,
    #                 'last_reading_date': last_reading.reading_date.strftime('%Y-%m-%d') if last_reading and last_reading.reading_date else None,
    #             })

    #         return Response(
    #            json.dumps({
    #         'status': 'success',
    #         'message': f'Meters missing readings for period {period_str}',
    #         'period': period_str,
    #         'data': meter_list,
    #     }),
    #     status=200,
    #     content_type='application/json'
    # )
    #     except Exception as e:
    #         _logger.error("Missing readings API error: %s", str(e), exc_info=True)
    #         return {
    #             'status': 'error',
    #             'message': 'Internal server error'
    #         }
        
    @http.route('/api/meters/completed-readings', auth='user', type='http', methods=['GET'], csrf=False)
    def get_meters_completed_readings(self, **kwargs):
     try:
        today = date.today()
        day = today.day
        month = today.month
        year = today.year

        # Determine period as last day of current or previous month
        if 22 <= day <= 31:
            last_day = monthrange(year, month)[1]
            period_date = today.replace(day=last_day)
        else:
            if month == 1:
                prev_month = 12
                prev_year = year - 1
            else:
                prev_month = month - 1
                prev_year = year
            last_day = monthrange(prev_year, prev_month)[1]
            period_date = today.replace(year=prev_year, month=prev_month, day=last_day)
        period_str = period_date.strftime('%Y-%m-%d')

        collector_id = request.env.user.id
        zone_ids = request.env['billing.zone'].sudo().search([('collector_id', '=', collector_id)]).ids

        # Find all meters in collector's zones
        all_meters = request.env['billing.meter'].sudo().search([('zone_id', 'in', zone_ids)])

        # Find all meter readings for this period and these meters
        readings = request.env['meter.reading'].sudo().search([
            ('bill_period', '=', period_str),
            ('meter_id', 'in', all_meters.ids)
        ])

        meter_list = []
        for reading in readings:
            meter = reading.meter_id
            meter_list.append({
                'reading_id': reading.id,
                'meter_id': meter.id,
                'name': meter.customer_id.name,
                'serial': getattr(meter, 'serial_number', ''),
                'zone_id': meter.zone_id.id if meter.zone_id else None,
                'status': meter.status,
                'zone_name': meter.zone_id.name if meter.zone_id else '',
                'reading_date': reading.reading_date.strftime('%Y-%m-%d') if reading.reading_date else '',
                'current_reading': reading.current_reading,
                'prev_reading': reading.prev_reading,
                'consumption': reading.consumption,
            })

        return Response(
            json.dumps({
                'status': 'success',
                'message': f'Readings completed for period {period_str}',
                'period': period_str,
                'data': meter_list,
            }),
            status=200,
            content_type='application/json'
        )
     except Exception as e:
        _logger.error("Completed readings API error: %s", str(e), exc_info=True)
        return Response(
            json.dumps({
                'status': 'error',
                'message': 'Internal server error'
            }),
            status=500,
            content_type='application/json'
        )
     

    @http.route('/api/helpdesk/complaints', auth='user', type='http', methods=['GET'], csrf=False)
    def get_my_complaints(self, **kwargs):
     try:
        technician_id = request.env.user.id
        print("Technician ID:", technician_id)
        

        # Find the "Solved" stage ID first
        solved_stage = request.env['helpdesk.stage'].sudo().search([('name', '=', 'Solved')], limit=1)
        complaints = request.env['helpdesk.ticket'].sudo().search([
    ('user_id', '=', technician_id),
    #('stage_id', '!=', solved_stage.id),
])
        print(f"Found {len(complaints)} complaints for technician {technician_id}")
        print("Complaints:", complaints.mapped('name'))
        data = []
        for c in complaints:
            data.append({
                'id': c.id,
                'name': c.name,
                'customer_name': c.partner_name if c.partner_name else '',
                'phone': c.partner_phone if c.partner_phone else '',
                'weahey':'biil',
                'meter_id': c.partner_id.billing_account if c.partner_id else None,
                'zone':c.zone_id if c.zone_id else '',
                'street': c.street if c.street else '',
                #'meter_id': c.partner_id.billing_account if c.partner_id else None,
                # 'meter_serial': getattr(c.meter_id, 'serial_number', ''),
                'description': c.description,
                'stage': c.stage_id.name if c.stage_id else '',
                'create_date': c.create_date.strftime('%Y-%m-%d %H:%M:%S') if c.create_date else '',
            })
        return Response(
            json.dumps({
                'status': 'success',
                'data': data,
            }),
            status=200,
            content_type='application/json'
        )
     except Exception as e:
        _logger.error("Helpdesk list error: %s", str(e), exc_info=True)
        return Response(
            json.dumps({'status': 'error', 'message': 'Internal server error'}),
            status=500,
            content_type='application/json'
        )
     
    @http.route('/api/helpdesk/complaint/<int:complaint_id>', auth='user', type='http', methods=['GET'], csrf=False)
    def get_complaint_detail(self, complaint_id, **kwargs):
     try:
        print("Session ID:", request.session.sid)
        print(f"Fetching details for complaint ID: {complaint_id}")
        complaint = request.env['helpdesk.ticket'].sudo().browse(complaint_id)
        print(f"Complaint found: {complaint.name if complaint else 'None'}")
        print(f'Complaint: {complaint}')

        if not complaint or complaint.user_id.id != request.env.user.id:
            return Response(
                json.dumps({'status': 'error', 'message': 'Not found or not assigned to you'}),
                status=404,
                content_type='application/json'
            )
        data = {
                'id': complaint.id,
                'name': complaint.name,
                'customer_name': complaint.partner_name if complaint.partner_name else '',
                'phone': complaint.partner_phone if complaint.partner_phone else '',
                
                'meter_id': complaint.partner_id.billing_account if complaint.partner_id else None,
                'zone':complaint.zone_id if complaint.zone_id else '',
                'street': complaint.street if complaint.street else '',
                #'meter_id': c.partner_id.billing_account if c.partner_id else None,
                # 'meter_serial': getattr(c.meter_id, 'serial_number', ''),
                'description': complaint.description,
                'stage': complaint.stage_id.name if complaint.stage_id else '',
                'create_date': complaint.create_date.strftime('%Y-%m-%d %H:%M:%S') if complaint.create_date else '',
            # Add more fields as needed
        }
        return Response(
            json.dumps({'status': 'success', 'data': data}),
            status=200,
            content_type='application/json'
        )
     except Exception as e:
        _logger.error("Helpdesk detail error: %s", str(e), exc_info=True)
        return Response(
            json.dumps({'status': 'error', 'message': 'Internal server error'}),
            status=500,
            content_type='application/json'
        )
     

    @http.route('/api/helpdesk/complaint/<int:complaint_id>/solve', auth='user', type='http', methods=['POST'], csrf=False)
    def solve_complaint(self, complaint_id, **kwargs):
     try:
        complaint = request.env['helpdesk.ticket'].sudo().browse(complaint_id)
        if not complaint or complaint.technician_id.id != request.env.user.id:
            return Response(
                json.dumps({'status': 'error', 'message': 'Not found or not assigned to you'}),
                status=404,
                content_type='application/json'
            )
        # Mark as solved (adjust field names as needed)
        complaint.write({'stage': 'solved'})
        return Response(
            json.dumps({'status': 'success', 'message': 'Complaint marked as solved'}),
            status=200,
            content_type='application/json'
        )
     except Exception as e:
        _logger.error("Helpdesk solve error: %s", str(e), exc_info=True)
        return Response(
            json.dumps({'status': 'error', 'message': 'Internal server error'}),
            status=500,
            content_type='application/json'
        )
     
    @http.route('/api/helpdesk/complaints/grouped-by-stage', auth='user', type='http', methods=['GET'], csrf=False)
    def get_my_complaints_grouped_by_stage(self, **kwargs):
        try:
            technician_id = request.env.user.id
            complaints = request.env['helpdesk.ticket'].sudo().search([
                ('user_id', '=', technician_id),
            ])
            grouped = defaultdict(list)
            for c in complaints:
                stage = c.stage_id.name if c.stage_id else 'No Stage'
                grouped[stage].append({
                    'id': c.id,
                    'name': c.name,
                    'customer_name': c.partner_name if c.partner_name else '',
                    'phone': c.partner_phone if c.partner_phone else '',
                    'meter_id': c.partner_id.billing_account if c.partner_id else None,
                    'zone': c.zone_id if c.zone_id else '',
                    'street': c.street if c.street else '',
                    'description': c.description,
                    'stage': stage,
                    'create_date': c.create_date.strftime('%Y-%m-%d %H:%M:%S') if c.create_date else '',
                })
            # Convert defaultdict to regular dict for JSON serialization
            grouped_dict = dict(grouped)
            return Response(
                json.dumps({
                    'status': 'success',
                    'data': grouped_dict,
                }),
                status=200,
                content_type='application/json'
            )
        except Exception as e:
            _logger.error("Helpdesk grouped list error: %s", str(e), exc_info=True)
            return Response(
                json.dumps({'status': 'error', 'message': 'Internal server error'}),
                status=500,
                content_type='application/json'
            )
        


    
    @http.route('/api/helpdesk/complaints/count-by-stage', auth='user', type='http', methods=['GET'], csrf=False)
    def get_complaint_count_by_stage(self, **kwargs):
     try:
        technician_id = request.env.user.id
        # Find "Solved" and "Cancelled" stage IDs
        excluded_stages = request.env['helpdesk.stage'].sudo().search([
            ('name', 'in', ['Solved', 'Cancelled'])
        ]).ids

        # Group by stage_id and count, excluding those stages
        result = request.env['helpdesk.ticket'].sudo().read_group(
            domain=[
                ('user_id', '=', technician_id),
                ('stage_id', 'not in', excluded_stages)
            ],
            fields=['stage_id'],
            groupby=['stage_id'],
            lazy=False,
        )
        data = []
        for rec in result:
            stage_name = rec['stage_id'][1] if rec['stage_id'] else 'No Stage'
            data.append({
                'stage': stage_name,
                'count': rec['__count'],
            })
        return Response(
            json.dumps({'status': 'success', 'data': data}),
            status=200,
            content_type='application/json'
        )
     except Exception as e:
        _logger.error("Helpdesk count by stage error: %s", str(e), exc_info=True)
        return Response(
            json.dumps({'status': 'error', 'message': 'Internal server error'}),
            status=500,
            content_type='application/json'
        )
     

    @http.route('/api/helpdesk/complaints/by-stage-name', auth='user', type='http', methods=['GET'], csrf=False)
    def get_tickets_by_stage_name(self, **kwargs):
     try:
        technician_id = request.env.user.id
        stage_name = request.httprequest.args.get('stage')
        print("Stage name received:", stage_name)
        if not stage_name:
            return Response(
                json.dumps({'status': 'error', 'message': 'Missing stage parameter'}),
                status=400,
                content_type='application/json'
            )
        # Find the stage by name
        stage = request.env['helpdesk.stage'].sudo().search([('name', '=', stage_name)], limit=1)
        if not stage:
            return Response(
                json.dumps({'status': 'error', 'message': f'Stage "{stage_name}" not found'}),
                status=404,
                content_type='application/json'
            )
        # Search tickets for this user and stage
        tickets = request.env['helpdesk.ticket'].sudo().search([
            ('user_id', '=', technician_id),
            ('stage_id', '=', stage.id),
        ])
        print(f"Found {len(tickets)} tickets for stage '{stage_name}' and technician {technician_id}")
        print("Tickets:", tickets.mapped('name'))
        data = []
        for t in tickets:
            data.append({
                'id': t.id,
                'name': t.name,
                'customer_name': t.partner_name if t.partner_name else '',
                'phone': t.partner_phone if t.partner_phone else '',
                'meter_id': t.partner_id.billing_account if t.partner_id else None,
                'zone': t.zone_id if t.zone_id else '',
                'street': t.street if t.street else '',
                'description': t.description,
                'contacts':t.contacts if t.contacts else '',
                'stage': stage_name,
                'create_date': t.create_date.strftime('%Y-%m-%d %H:%M:%S') if t.create_date else '',
            })
        return Response(
            json.dumps({'status': 'success', 'data': data}),
            status=200,
            content_type='application/json'
        )
     except Exception as e:
        _logger.error("Helpdesk by stage name error: %s", str(e), exc_info=True)
        return Response(
            json.dumps({'status': 'error', 'message': 'Internal server error'}),
            status=500,
            content_type='application/json'
        )
     

    @http.route('/api/helpdesk/complaint/<int:ticket_id>/set-stage', auth='user', type='json', methods=['POST'], csrf=False)
    def set_ticket_stage(self, ticket_id, **post):
     try:


        data = request.get_json_data()
        print("Received data for set_ticket_stage:", data)
        stage_name = data.get('stage_name')
        stage_id = data.get('stage_id')
        comments = data.get('comments')
        print("Received stage_name:", stage_name)
        # Accept either stage_name or stage_id in the payload
        #stage_name = request.jsonrequest.get('stage_name')
        print("Received stage_name:", stage_name)
        #stage_id = request.jsonrequest.get('stage_id')
        if not stage_name and not stage_id:
            return {'status': 'error', 'message': 'Missing stage_name or stage_id'}

        print(f"Ticket id fround: {ticket_id}")
        ticket = request.env['helpdesk.ticket'].sudo().browse(ticket_id)
        if not ticket.exists():
            return {'status': 'error', 'message': 'Ticket not found'}

        # Find the stage
        if stage_id:
            stage = request.env['helpdesk.stage'].sudo().browse(stage_id)
        else:
            stage = request.env['helpdesk.stage'].sudo().search([('name', '=', stage_name)], limit=1)
        if not stage:
            return {'status': 'error', 'message': 'Stage not found'}

        ticket.stage_id = stage.id
        ticket.comments = comments if comments else ''
        return {'status': 'success', 'message': f'Ticket moved to stage {stage.name}'}
     except Exception as e:
        _logger.error("Set ticket stage error: %s", str(e), exc_info=True)
        return {'status': 'error', 'message': 'Internal server error'}