{
    'name': "Utility",
    'summary': """Various utility functions and tools""",
    'description': """
        This module provides various utility functions and tools
        that can be used across other Odoo modules.
    """,
    'author': "Your Name",
    'website': "http://www.yourcompany.com",
    'category': 'Tools',
    'version': '17.0.1.0.0',
    'depends': ['base',
         'account',
         'product', 'crm', 'mail','contacts',
         
        'sale',
        # 'crm',
        # 'stock',
        # 'helpdesk',
         'web',],
    'data': [
        'security/ir.model.access.csv',
        'views/menus.xml',
        'views/zone_views.xml',
        'views/product_views.xml',
        'views/meter_serial_views.xml',
        'views/meter_group_views.xml',
        'views/meter_discount_views.xml',
        'views/billing_meter_views.xml',
        'views/crm_lead_inherid_views.xml',
        'views/create_customer_meter_wizard_views.xml',
        'views/meter_reading_views.xml',
        'views/account_move_views.xml',
        'views/customer_views.xml',
        'views/billing_meter_form_views.xml',

        'views/meter_reading_report_wizard_view.xml',
    'report/meter_reading_report.xml',
    'report/meter_reading_report_template.xml',

    'views/meter_report_wizard_view.xml',
    'report/meter_report.xml',
    'report/meter_report_template.xml',
    'views/res_users_inherit_view.xml',
    # 'views/helpdesk_ticket_custom_form.xml',
    # 'views/help_desk_inherit_view.xml',
    # 'views/ticket_views.xml',

    
    'report/partner_statement_report/report_action.xml',
    'report/partner_statement_report/report_template.xml',

    ],
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
    'web.assets_backend': [
        #'utility/static/src/css/meter_reading.css',
        #'utility/static/src/js/notebook_page_listener.js',
        #'utility/static/src/js/select_meter_info_page.js',
    ],
},
   
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}