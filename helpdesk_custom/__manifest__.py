{
    'name': 'Custom Helpdesk',
    'version': '1.0',
    'summary': 'Custom Helpdesk Ticket Creation',
    'description': 'Replace default ticket creation with custom form',
    'author': 'Your Name',
    'depends': ['helpdesk'],
    'data': [
        #'views/helpdesk_ticket_views.xml',
        #'views/custom_ticket_form.xml',
        #'views/helpdesk_ticket_custom_form.xml',
        # 'views/helpdesk_ticket_views.xml',
        # #'views/custom_ticket_form.xml',
        # 'views/custom_ticket_views.xml',
        #'views/helpdesk_ticket_custom_form.xml',
        'views/help_desk_inherit_view.xml',
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'custom_helpdesk/static/src/js/custom_button.js',
    #     ],
    # },
    'installable': True,
    'application': True,
}