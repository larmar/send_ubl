{
    'name': 'Send EHF Invoice',
    'version': '1.0',
    'author': 'Bringsvor Consulting AS',
    'website': 'http://www.bringsvor.com',
    'category': 'Accounting',
    'description': """Enables sending invoices from Odoo in EHF format.
""",
    'depends': ['base', 'account'],
    'data': [
        'views/company_view.xml',
        'views/partner_view.xml',
        'views/invoice_view.xml',
    ],
    'demo': [],
    'test': [
        ],
    'installable': True,
    'auto_install': False,
}

