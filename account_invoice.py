__author__ = 'tbri'
from openerp import models, fields, api, _
import logging
import create_ehf
from ftplib import FTP
import StringIO

_logger = logging.getLogger(__name__)

class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_invoice_send_einvoice_nofault(self):
        for invoice in self:
            if not invoice.partner_id.einvoice_address:
                continue

            if not invoice.company_id.einvoice_ftp_endpoint or not invoice.company_id.einvoice_ftp_user or not invoice.company_id.einvoice_ftp_password:
                continue
            assert invoice
            xml = create_ehf.create_ehf(invoice)
            xmlfile = StringIO.StringIO(xml)
            _logger.info('Invoice %s generated this EHF-XML: %s' % (invoice.number, xml))

            ftp = FTP(invoice.company_id.einvoice_ftp_endpoint, invoice.company_id.einvoice_ftp_user, invoice.company_id.einvoice_ftp_password)

            ftp.storbinary('STOR Invoice-%s.xml' % (invoice.number), xmlfile)
            ftp.close()




    @api.multi
    def action_invoice_send_einvoice(self):
        for invoice in self:
            if not invoice.partner_id.einvoice_address:
                raise Warning('Partner %s does not have an einvoice address.' % invoice.partner_id.name)

            if not invoice.company_id.einvoice_ftp_endpoint or not invoice.company_id.einvoice_ftp_user or not invoice.company_id.einvoice_ftp_password:
                raise Warning('Missing configuration. Company %s must have einvoice settings configured.' % invoice.company_id.name)

        self.action_invoice_send_einvoice_nofault()