__author__ = 'tbri'
from openerp import models, fields, api, _

class res_partner(models.Model):
    _inherit = 'res.partner'

    einvoice_address = fields.Char(string = _('Einvoice address'), help='Destination party identifier when sending EHF invoices.')