# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright :
#        (c) 2015 VMCloud Solution (http://vmcloudsolution.pe)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import datetime
from openerp.osv import fields, osv

class account_invoice(osv.osv):
    _inherit = "account.invoice"

    def set_value_space(self, value, space=7):
        if not value:
            value = ''
        value_space = ' ' * space + str(value)
        return value_space[-space:]

    def get_date_formats(self, cr, uid, context=None):
        lang = self.pool.get('res.users').browse(cr, uid, uid).lang
        res_lang = self.pool.get('res.lang')
        lang_params = {}
        if lang:
            ids = res_lang.search(cr, uid, [("code", "=", lang)])
            if ids:
                lang_params = res_lang.read(cr, uid, ids[0], ["date_format", "time_format"])
        format_date = lang_params.get("date_format", '%m/%d/%Y').encode('utf-8')
        format_time = lang_params.get("time_format", '%H:%M:%S').encode('utf-8')
        return format_date, format_time

    def export_for_printing(self, cr, uid, invoice_ids, context=None):
        receipts = []
        date_format = self.get_date_formats(cr, uid, context=context)
        dp_account = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        dp_qty = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Unit of Measure')
        dp_price = self.pool.get('decimal.precision').precision_get(cr, uid, 'Unit Price')
        for invoice_id in invoice_ids:
            account_invoice_obj = self.pool.get("account.invoice").browse(cr, uid, invoice_id, context=context)
            receipt = {
                'id': invoice_id,
                'number': account_invoice_obj.number,
                'date_invoice': datetime.strptime(account_invoice_obj.date_invoice, '%Y-%m-%d').strftime(date_format[0]),
                'date_invoice2': datetime.strptime(account_invoice_obj.date_invoice, '%Y-%m-%d').strftime('%d de %B del %Y'),
                'day': datetime.strptime(account_invoice_obj.date_invoice, '%Y-%m-%d').strftime('%d'),
                'month': datetime.strptime(account_invoice_obj.date_invoice, '%Y-%m-%d').strftime('%m'),
                'year': datetime.strptime(account_invoice_obj.date_invoice, '%Y-%m-%d').strftime('%Y'),
                'partner': {
                    'name': account_invoice_obj.partner_id.name.encode('utf-8', 'ignore'),
                    'vat': account_invoice_obj.partner_id.vat[3:] if account_invoice_obj.partner_id.vat else '',
                    'street': (account_invoice_obj.partner_id.street.encode('utf-8', 'ignore') + ' ' if account_invoice_obj.partner_id.street else '') \
                              + (account_invoice_obj.partner_id.street2.encode('utf-8', 'ignore') + ' ' if account_invoice_obj.partner_id.street2 else '') \
                              + (account_invoice_obj.partner_id.city.encode('utf-8', 'ignore') + ' ' if account_invoice_obj.partner_id.city else ''),
                },
                'amount_untaxed': round(account_invoice_obj.amount_untaxed, dp_account),
                'amount_tax': round(account_invoice_obj.amount_tax, dp_account),
                'amount_total': round(account_invoice_obj.amount_total, dp_account),
                'currency': {
                    'symbol': account_invoice_obj.currency_id.symbol,
                },
                'amount_text': account_invoice_obj.amount_text,
                'max_product': 10,
            }
            invoice_line = []
            for line in account_invoice_obj.invoice_line:
                quantity_str = str(round(line.quantity, dp_qty))
                if dp_qty == 0:
                    quantity_str = str(int(line.quantity))
                invoice_line.append(
                    {
                        'id': line.id,
                        'product': {
                            'name': line.product_id.name.encode('utf-8', 'ignore'),
                            'ean13': line.product_id.ean13 if line.product_id.ean13 else '',
                            'default_code': line.product_id.default_code.encode('utf-8', 'ignore') if line.product_id.default_code else '',
                            'uom': line.product_id.uom_id.name,
                            'quantity': quantity_str,
                            'price_unit_str': self.set_value_space(round(line.price_unit, dp_price), 8),
                            'price_subtotal_str': self.set_value_space(round(line.price_subtotal, dp_account), 13),
                        }
                    }
                )
            receipt['invoice_line'] = invoice_line
            receipts.append(receipt)
        return receipts