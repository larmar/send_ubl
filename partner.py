__author__ = 'tbri'
from openerp import models, fields, api, _

ADDRESS_SCHEMES = [('NO:ORGNR', 'Norwegian ORG number'),
                   ('CVR', 'CVR format'),
    ('EU:VAT','EU Vat number'),
    ('FI:OVT','Finnish eInvoice address')]


class res_partner(models.Model):
    _inherit = 'res.partner'

    einvoice_address = fields.Char(string = _('eInvoice address'), help='Destination party identifier when sending EHF invoices.')
    einvoice_address_scheme = fields.Selection(ADDRESS_SCHEMES, string='eInvoice address scheme')