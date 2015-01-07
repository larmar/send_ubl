__author__ = 'tbri'
from openerp import models, fields, api, _

class res_company(models.Model):
    _inherit = 'res.company'

    einvoice_ftp_endpoint = fields.Char(_('eInvoice ftp server'), help='Destination to send eInvoices.')
    einvoice_ftp_user = fields.Char(_('eInvoice ftp user'))
    einvoice_ftp_password = fields.Char(_('eInvoice ftp password'))
