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

import urllib2
import json
import logging
from operator import itemgetter

_logger = logging.getLogger(__name__)

class pos_session(osv.osv):
    _inherit = "pos.session"

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

    def export_for_printing(self, cr, uid, pos_session_ids, context=None):
        receipts = []
        date_format = self.get_date_formats(cr, uid, context=context)
        dp_account = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        dp_qty = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Unit of Measure')
        dp_price = self.pool.get('decimal.precision').precision_get(cr, uid, 'Unit Price')
        for pos_session_id in pos_session_ids:
            pos_session_obj = self.pool.get("pos.session").browse(cr, uid, pos_session_id, context=context)
            receipt = {
                'id': pos_session_id,
                'company': pos_session_obj.user_id.company_id.name,
                'name': pos_session_obj.name,
                'start_at': datetime.strptime(pos_session_obj.start_at, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S'),
                'stop_at': pos_session_obj.stop_at and datetime.strptime(pos_session_obj.stop_at, '%Y-%m-%d %H:%M:%S').strftime('%d-%m-%Y %H:%M:%S') or False,
                'point_of_sale': pos_session_obj.config_id.name,
                'responsible': pos_session_obj.user_id.name,
                'state': pos_session_obj.state,
            }
            journal_lines = []
            journal_total = journal_total_real = 0.0
            for line in pos_session_obj.statement_ids:
                journal_lines.append(
                    {
                        'id': line.id,
                        'name': line.journal_id.name,
                        'total': line.balance_end,
                        'total_real': line.balance_end_real,
                    })
                journal_total += line.balance_end
                journal_total_real += line.balance_end_real
            receipt['journal_lines'] = journal_lines
            receipt['journal_total'] = journal_total
            receipt['journal_total_real'] = journal_total_real

            order_lines = []
            orders_total = 0.0
            orders_tax = 0.0
            total_fichas = 0
            categ_lines = {}
            for order in pos_session_obj.order_ids:
                orders_total += order.amount_total
                orders_tax += order.amount_tax
                for order_line in order.lines:
                    category = order_line.product_id.name
                    code = order_line.product_id.default_code
                    qty,total,dummy = categ_lines.get( category, (0,0,""))
                    qty += order_line.qty
                    total += order_line.price_subtotal
                    categ_lines[category] = (qty,total,code)
                    total_fichas += qty*order_line.product_id.volume
            receipt['categ_lines'] = sorted([{'name':key,'qty':value[0],'total':value[1],'code':value[2]} for key, value in categ_lines.iteritems()],key=itemgetter('code'))
            receipt['total_fichas'] = total_fichas
            receipt['orders_tax'] = orders_tax
            receipt['orders_total'] = orders_total
            receipt['orders_subtotal'] = orders_total - orders_tax
            receipts.append(receipt)
        return receipts

