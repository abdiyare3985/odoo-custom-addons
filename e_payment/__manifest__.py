{
    'name': 'E-Payment',
    'version': '17.0.1.0.0',
    'summary': 'Electronic payment for customer invoices',
    'description': 'Module to handle electronic payments for customer invoices.',
    'category': 'Accounting',
    'author': 'Your Name',
    'depends': ['account','utility'],
    'data': [
        # Add your views, security, etc. here
        'security/ir.model.access.csv',
        'views/menus.xml',
        'views/account_payment_inherit_views.xml',
        'wizard/payment_list/payment_report_wizard_view.xml',
        'report/payment_list/payment_list_report.xml',
        'report/payment_list/payment_report_action.xml',
        'wizard/payment_summary/report_payment_summary_wizard.xml',
        'report/payment_summary/payment_summary_report_tem.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}