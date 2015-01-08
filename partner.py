__author__ = 'tbri'
from openerp import models, fields, api, _

ADDRESS_SCHEMES = [('NO:ORGNR', 'Norwegian ORG number'),
    ('EU:VAT','EU Vat number'),
    ('OVT','Finnish eInvoice address')]

class res_partner(models.Model):
    _inherit = 'res.partner'

    einvoice_address = fields.Char(string = _('Einvoice address'), help='Destination party identifier when sending EHF invoices.')
    einvoice_address_scheme = fields.Selection(ADDRESS_SCHEMES, string='Einvoice address scheme')