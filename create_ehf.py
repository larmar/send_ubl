#!/usr/bin/env python
# -.- coding: utf-8 -.-


"""
Generate invoices in EHF format.
"""

__author__ = 'tbri'
from lxml import etree
from lxml.builder import ElementMaker
import logging
import urllib2

nsmap = {None: 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
         'cac': "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
         'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}
customization_id = 'urn:www.cenbii.eu:transaction:biitrns010:ver2.0:extended:urn:www.peppol.eu:bis:peppol5a:ver2.0:extended:urn:www.difi.no:ehf:faktura:ver2.0'
profile_id = 'urn:www.cenbii.eu:profile:bii05:ver2.0'

E = ElementMaker(namespace="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2", nsmap=nsmap)
E_cbc = ElementMaker(namespace="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2", nsmap=nsmap)
E_cac = ElementMaker(namespace='urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2', nsmap=nsmap)


def create_supplier_party(company):
    assert company.company_registry, 'Company %s must have org number' % company.name
    party_scheme = '%s:VAT' % company.country_id.code
    company_number = company.company_registry[2:].replace(' ', '')
    r = E_cac.AccountingSupplierParty(
        E_cac.Party(
            E_cbc.EndpointID(company.partner_id.einvoice_address, schemeID=company.partner_id.einvoice_address_scheme),
            #E_cbc.EndpointID('60 764 05083', schemeID='CVR'),
            E_cac.PartyName(E_cbc.Name(company.name)),
            E_cac.PostalAddress(
                E_cbc.StreetName(company.street),
                E_cbc.CityName(company.city),
                E_cbc.PostalZone(company.zip),
                E_cac.Country(E_cbc.IdentificationCode(company.country_id.code, listID="ISO3166-1:Alpha2")),
            ),
            E_cac.PartyTaxScheme(
                E_cbc.CompanyID('60 764 05083', schemeID='CVR'),
                #E_cbc.CompanyID(company_number, schemeID=party_scheme),
                E_cac.TaxScheme(E_cbc.ID('VAT'))
            ),
            E_cac.PartyLegalEntity(
                E_cbc.RegistrationName(company.name),
                E_cbc.CompanyID(company.vat[2:], schemeID='NO:ORGNR'),
                E_cac.RegistrationAddress(
                    E_cbc.CityName(company.city),
                    E_cac.Country(E_cbc.IdentificationCode(company.country_id.code, listID="ISO3166-1:Alpha2")),
                ),
            ),
            E_cac.Contact(  #E_cbc.ID('Our ref'),  #E_cbc.Name(our_contact),  #E_cbc.Telephone(elmatica_phone),
                            E_cbc.ElectronicMail(company.email),
            ),
        )
    )

    return r


def create_customer_party(partner, customer_contact):
    contact_id = customer_contact.split()[0]
    contact_name = ' '.join(customer_contact.split()[2:])
    assert partner.vat, 'Partner %s must have VAT number' % partner.name
    party_scheme = partner.einvoice_address_scheme or 'FI:OVT'
    company_scheme = '%s:VAT' % partner.country_id.code
    partner_org_number = partner.vat[2:]

    r = E_cac.AccountingCustomerParty(
        E_cac.Party(
            E_cbc.EndpointID(partner.einvoice_address, schemeID=party_scheme), # SKal vere CVR
            #E_cbc.EndpointID('EE101358596', schemeID='FI:VAT'),
            # E_cbc.EndpointID('003710298402', schemeId='CVR'),


            E_cac.PartyIdentification(E_cbc.ID(partner.einvoice_address, schemeID=party_scheme)),
            E_cac.PartyName(E_cbc.Name(partner.name)),
            E_cac.PostalAddress(
                E_cbc.StreetName(partner.street),
                E_cbc.CityName(partner.city),
                E_cbc.PostalZone(partner.zip),
                E_cac.Country(E_cbc.IdentificationCode(partner.country_id.code, listID="ISO3166-1:Alpha2")),
            ),
    #        E_cac.PartyTaxScheme(
    #            E_cbc.CompanyID(partner_org_number, schemeID=party_scheme),
    #            E_cac.TaxScheme(E_cbc.ID('VAT'))
    #        ),
            E_cac.PartyLegalEntity(
                E_cbc.RegistrationName(partner.name),
                E_cbc.CompanyID(partner_org_number, schemeID=company_scheme),
                E_cac.RegistrationAddress(
                    E_cbc.CityName(partner.city),
                    E_cac.Country(E_cbc.IdentificationCode(partner.country_id.code, listID="ISO3166-1:Alpha2")),
                ),
            ),
            E_cac.Contact(
                E_cbc.ID(contact_id),
                E_cbc.Name(contact_name),  # E_cbc.Telephone(customer_contact_phone),
                # E_cbc.ElectronicMail(customer_contact_email),
            ),
        )
    )

    return r


payment_means_code = '31'  # whatever that means
"""
bank_identifier = 'DNBANOKK'
due_date = '2013-07-20'
payment_id = '1000343432321323'
iban_number = 'NO9386011117947'
branch_id = '9710'
"""


def create_payment_means(invoice):
    iban_account = None
    branch_id = None
    for bank_account in invoice.company_id.bank_ids:
        if bank_account.state == 'iban':
            iban_account = bank_account.acc_number.replace(' ', '')
            branch_id = bank_account.bank_bic

    assert iban_account, 'No IBAN account defined for %s' % invoice.company_id.name
    assert branch_id, 'No BIC defined for IBAN account %s of company %s' % (iban_account, invoice.company_id.name)
    date_due = type(invoice.date_due) == str and invoice.date_due or invoice.date_due.strftime('%Y-%m-%d')

    r = E_cac.PaymentMeans(
        E_cbc.PaymentMeansCode(payment_means_code, listID="UNCL4461"),
        E_cbc.PaymentDueDate(date_due),
        #E_cbc.PaymentID(payment_id),
        E_cac.PayeeFinancialAccount(
            E_cbc.ID(iban_account, schemeID="IBAN"),
            E_cac.FinancialInstitutionBranch(
                #E_cbc.ID(branch_id),
                E_cac.FinancialInstitution(
                    E_cbc.ID(branch_id, schemeID="BIC")
                ),
            ),
        ),
    )

    return r


"""
tax_category = 'S'
tax_percent = '25'
net_total = "1000.00"
tax_amount = '250.00'
tax_amount_reporting_currency = '2160.00'
tax_inclusive_total = "1250.00"
"""


def create_monetary_totals(invoice):
    currency_code = invoice.currency_id.name

    r = E_cac.LegalMonetaryTotal(
        E_cbc.LineExtensionAmount('%.2f' % invoice.amount_untaxed, currencyID=currency_code),
        E_cbc.TaxExclusiveAmount('%.2f' % invoice.amount_untaxed, currencyID=currency_code),
        E_cbc.TaxInclusiveAmount('%.2f' % invoice.amount_total, currencyID=currency_code),
        E_cbc.PayableAmount('%.2f' % invoice.amount_total, currencyID=currency_code),
    )
    return r


"""
delivery_date = '2013-05-01'
delivery_street = 'Strandgaten 50'
delivery_city = 'Bergen'
delivery_zip = '5000'
delivery_country = 'NO'
"""


def create_delivery(delivery_date, partner):
    r = E_cac.Delivery(
        E_cbc.ActualDeliveryDate(delivery_date),
        E_cac.DeliveryLocation(
            E_cac.Address(
                E_cbc.StreetName(partner.street),
                E_cbc.CityName(partner.city),
                E_cbc.PostalZone(partner.zip),
                E_cac.Country(E_cbc.IdentificationCode(partner.country_id.code, listID='ISO3166-1:Alpha2')),
            ),
        ),
    )

    return r


def get_tax_totals(invoice):
    tax_sum_invoice_curr = 0.0
    tax_sum_reporting_curr = 0.0
    base_sum_invoice_curr = 0.0
    base_sum_reporting_curr = 0.0
    tax_to_code = {}

    for line in invoice.invoice_line:
        for tax in line.invoice_line_tax_id:
            base_id = tax.base_code_id
            tax_id = tax.tax_code_id
            assert tax.type == 'percent'
            tax_amount = tax.amount
            tax_to_code[tax] = (base_id, tax_id, tax_amount)

    print "TAX_TO_CODE", tax_to_code
    all_taxes = []

    for taxline in invoice.tax_line:
        taxcode = taxline.tax_code_id
        basecode = taxline.base_code_id

        percentage = None
        for tc, tci in tax_to_code.items():
            if tci[0] == basecode and tci[1] == taxcode:
                print "FOUND", tc, tci

                percentage = int(tci[2] * 100)

        tax_info = (taxline.base_amount, taxline.base_amount_in_reporting_currency, taxline.amount,
                    taxline.amount_in_reporting_currency, percentage)
        all_taxes.append(tax_info)
    return all_taxes


tax_category = 'S'


def create_tax_total(invoice):
    assert invoice.type == 'out_invoice', 'We only support outgoing invoices at this time.'
    taxes = {}
    currency_code = invoice.currency_id.name
    reporting_currency_code = invoice.company_id.reporting_currency_id.name

    tax_info = get_tax_totals(invoice)
    if len(tax_info) == 0:
        return

    tax_amount = '%.2f' % sum([x[2] for x in tax_info])

    tax_total = E_cac.TaxTotal(
        E_cbc.TaxAmount(tax_amount, currencyID=currency_code),
    )

    for taxline in tax_info:
        subtotal = E_cac.TaxSubtotal(
            E_cbc.TaxableAmount('%.2f' % taxline[0], currencyID=currency_code),
            E_cbc.TaxAmount('%.2f' % taxline[2], currencyID=currency_code),
            E_cbc.TransactionCurrencyTaxAmount('%.2f' % taxline[3], currencyID=reporting_currency_code),
            E_cac.TaxCategory(
                E_cbc.ID(tax_category, schemeID="UNCL5305"),
                E_cbc.Percent('%d' % taxline[4]),
                E_cac.TaxScheme(E_cbc.ID('VAT')),
            )
        )
        tax_total.append(subtotal)

    return tax_total


"""
lines = [
    {'id': '1',
     'qty': '1',
     'description': 'Test product',
     'seller_id': 'TP',
     'tax_class': 'S',
     'tax_percent': '25',
     'net_price': '1000.00',
     'order_line' : 'OR001234##1',
    }
]
"""


def create_invoice_line(line):
    currency_code = line.invoice_id.currency_id.name
    invoiceline = E_cac.InvoiceLine(
        E_cbc.ID('%d' % line.id),
        E_cbc.InvoicedQuantity('%d' % line.quantity, unitCode="NAR", unitCodeListID="UNECERec20"),
        E_cbc.LineExtensionAmount('%.2f' % line.price_subtotal, currencyID=currency_code),
        # E_cbc.AccountingCost>123</cbc:AccountingCost>
        #E_cac.OrderLineReference(E_cbc.LineID(line['order_line'])),
    )

    item = E_cac.Item(
        E_cbc.Name(line.name),
        E_cac.SellersItemIdentification(E_cbc.ID(line.product_id.name)),
    )

    for tax_id in line.invoice_line_tax_id:
        percent = '%d' % int(round(tax_id.amount, 2) * 100)

        tax = E_cac.ClassifiedTaxCategory(
            E_cbc.ID(tax_category, schemeID="UNCL5305"),
            E_cbc.Percent(percent),
            E_cac.TaxScheme(E_cbc.ID('VAT')),
        )
        item.append(tax)

    invoiceline.append(item)
    invoiceline.append(E_cac.Price(
        E_cbc.PriceAmount('%.3f' % line.price_unit, currencyID=currency_code),
        #E_cbc.BaseQuantity('%d'  % line.quantity)
    )
    )

    return invoiceline


def create_tax_exchange_rate(invoice):
    date_invoice = type(invoice.date_invoice) == str and invoice.date_invoice or invoice.date_invoice.strftime(
        '%Y-%m-%d')
    currency_code = invoice.currency_id.name
    reporting_currency_code = invoice.company_id.reporting_currency_id.name

    #    has_tax, tax_sum_invoice_curr, tax_sum_reporting_curr, base_sum_invoice_curr, base_sum_reporting_curr
    tax_info = get_tax_totals(invoice)
    if len(tax_info) == 0:
        return

    sum_invoice_curr = 0.0
    sum_reporting_curr = 0.0
    for taxline in tax_info:
        sum_invoice_curr += taxline[0]
        sum_reporting_curr += taxline[1]

    calculation_rate = '%.2f' % round(sum_reporting_curr / sum_invoice_curr, 2)

    r = E_cac.TaxExchangeRate(
        E_cbc.SourceCurrencyCode(currency_code, listID="ISO4217"),
        E_cbc.TargetCurrencyCode(reporting_currency_code, listID="ISO4217"),
        E_cbc.CalculationRate(calculation_rate),
        E_cbc.MathematicOperatorCode('Multiply'),
        E_cbc.Date(date_invoice),
    )

    return r

INVOICE_TYPE_CODE = '380'

def create_ehf(invoice):
    date_invoice = type(invoice.date_invoice) == str and invoice.date_invoice or invoice.date_invoice.strftime(
        '%Y-%m-%d')
    note = ''
    if invoice.name:
        note += 'Your PO: %s\n' % invoice.name
    note += 'Customs declaration code: 8534.0000 \n'
    if invoice.supplier_country:
        note += 'Country of origin: %s \n' % invoice.supplier_country
    if invoice.supplier_vat:
        note += 'Supplier VAT no.: %s \n' % invoice.supplier_vat
    if invoice.situation_text:
        note += '%s\n' % invoice.situation_text

    my_doc = E.Invoice(
        E_cbc.UBLVersionID('2.1'),
        E_cbc.CustomizationID(customization_id),
        E_cbc.ProfileID(profile_id),
        E_cbc.ID(invoice.number),
        E_cbc.IssueDate(date_invoice),
        E_cbc.InvoiceTypeCode(INVOICE_TYPE_CODE, listID="UNCL1001"),
        E_cbc.Note(note),
        E_cbc.DocumentCurrencyCode(invoice.currency_id.name, listID="ISO4217")
    )

    if invoice.origin:
        order_ref = E_cac.OrderReference(
            E_cbc.ID(invoice.origin),
        )
        my_doc.append(order_ref)

    tax_info = get_tax_totals(invoice)
    if len(tax_info) > 0:
        E_cbc.TaxCurrencyCode(invoice.company_id.reporting_currency_id.name, listID="ISO4217")

    my_doc.append(create_supplier_party(invoice.company_id))
    my_doc.append(create_customer_party(invoice.partner_id, invoice.customer_contact))
    my_doc.append(create_delivery(date_invoice, invoice.partner_shipping_id))
    my_doc.append(create_payment_means(invoice))


    tax_echange = create_tax_exchange_rate(invoice)
    if tax_echange:
        my_doc.append(tax_echange)

    tax_total = create_tax_total(invoice)
    if tax_total:
        my_doc.append(tax_total)

    monetary_total = create_monetary_totals(invoice)
    my_doc.append(monetary_total)

    for line in invoice.invoice_line:
        my_doc.append(create_invoice_line(line))

    x = etree.tostring(my_doc, pretty_print=True)
    return x


if __name__ == '__main__':
    import oerplib
    #invoice_no = 'OG0011'
    #invoice_no = 'OG0015'
    invoice_no = 'OG0016'
    #invoice_no = 'ON0002'
    #invoice_no = 'ON0018'

    #oerp = oerplib.OERP('localhost', protocol='xmlrpc', port=8069)
    #user = oerp.login('admin', 'X', 'X')
    oerp = oerplib.OERP.load('debug')
    invoice_obj = oerp.get('account.invoice')
    invoice_ids = invoice_obj.search([('number', '=', invoice_no)])
    assert len(invoice_ids) == 1
    invoices = invoice_obj.browse(invoice_ids)
    invoice = None
    for x in invoices:
        invoice = x

    #url = 'http://localhost:8080/validate-ws/'
    url = 'http://vefa.difi.no/validate-ws/'
    data = create_ehf(invoice)
    f = open('test-invoice.xml', 'w')
    f.write(data)
    f.close()
    print "DATA", data
    req = urllib2.Request(url)
    req.add_header('Content-Type', 'application/xml; charset=utf-8')
    req.add_header('Content-Length', len(data))
    response = urllib2.urlopen(req, data)
    f = open('validation-result.xml', 'w')
    f.write(response.read())
    f.close()

    schemaid = 'urn:www.cenbii.eu:profile:bii05:ver2.0#urn:www.cenbii.eu:transaction:biitrns010:ver2.0:extended:urn:www.peppol.eu:bis:peppol5a:ver2.0:extended:urn:www.difi.no:ehf:faktura:ver2.0'
    url = 'http://localhost:8080/validate-ws/2.0/%s/render' % schemaid
    req = urllib2.Request(url)
    req.add_header('Content-Type', 'application/xml; charset=utf-8')
    req.add_header('Content-Length', len(data))
    response = urllib2.urlopen(req, data)
    f = open('render-result.html', 'w')
    f.write(response.read())
    f.close()