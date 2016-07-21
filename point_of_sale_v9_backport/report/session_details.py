# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import time
from openerp.osv import osv
from openerp.report import report_sxw


class session_details(report_sxw.rml_parse):
    def _get_sales_by_category(self, session_id):
        self.cr.execute(" select c.name as name, sum(pol.qty) qty, sum(pol.price_subtotal) total " \
                        " from pos_order po, pos_order_line pol, product_product p, product_template t, pos_category c " \
                        " where po.session_id = %s and " \
                        "       po.id = pol.order_id and " \
                        "       pol.product_id = p.id and " \
                        "       p.product_tmpl_id = t.id and " \
                        "       t.pos_categ_id = c.id " \
                        " group by c.name", (session_id,))
        return self.cr.dictfetchall()

    def _pos_sales_details(self, session):
        data = []
        for pos in session.order_ids:
            if pos.state in ['paid', 'done']:
                subtotal = pos.amount_subtotal
                tax = pos.amount_tax
                total = pos.amount_total
            else:
                subtotal = tax = total = 0

            data.append({
                'pos_name': pos.name + (pos.invoice_id and "-"+pos.invoice_id.number or ""),
                'date_order': pos.date_order,
                'subtotal': subtotal,
                'tax': tax,
                'total': total,
                'state': pos.state,
                'lines': pos.lines,
            })
            if pos.state in ['done','paid']:
                #self.base += (pol.price_unit * pol.qty)
                self.subtotal += pos.amount_subtotal
                self.total += pos.amount_total
                #self.qty += pol.qty
        if data:
            return data
        else:
            return {}

    def _get_tax_amount2(self):
        return self.total - self.subtotal

    def _get_sales_total_2(self):
        return self.total

    def _get_sales_subtotal_2(self):
        return self.subtotal
    
    def __init__(self, cr, uid, name, context):
        super(session_details, self).__init__(cr, uid, name, context=context)
        self.subtotal = 0.0
        self.total = 0.0
        self.localcontext.update({
            'get_sales_by_category': self._get_sales_by_category,
            'pos_sales_details':self._pos_sales_details,
            'getsalessubtotal2': self._get_sales_subtotal_2,
            'getsalestotal2': self._get_sales_total_2,
            'gettaxamount2': self._get_tax_amount2,
        })


class report_session_details(osv.AbstractModel):
    _name = 'report.point_of_sale.report_sessionsummary'
    _inherit = 'report.abstract_report'
    _template = 'point_of_sale.report_sessionsummary'
    _wrapped_report_class = session_details

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
