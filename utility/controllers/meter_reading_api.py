from odoo import http
from odoo.http import request

class MeterReadingAPI(http.Controller):

    @http.route('/api/meter_readings', type='json', auth='none', methods=['POST'], csrf=False)
    def create_meter_reading(self, **kwargs):
        #api_key = request.httprequest.headers.get('X-API-Key')
        # Replace this with your actual key or a lookup in the database
        # expected_key = 'f0916bc1e2ddf9a652304e042e34a4531fabe08d'
        # if api_key != expected_key:
        #     return {"error": "Invalid API key"}, 401
        
        print("1")

        data = request.jsonrequest
        if not data.get('meter_id') or not data.get('reading_date') or not data.get('current_reading'):
            return {"error": "Missing required fields."}
        print("2")

        meter = request.env['meter.serial'].sudo().browse(data['meter_id'])
        if not meter.exists():
            return {"error": "Meter not found."}
        
        print("3")

        reading = request.env['meter.reading'].sudo().create({
            'meter_id': meter.id,
            'reading_date': data['reading_date'],
            'current_reading': data['current_reading'],
        })
        print("4")
        return {"success": True, "reading_id": reading.id}