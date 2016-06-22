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
    def _get_sales_by_product(self, session):
        self.cr.execute("select p.name name, sum(pol.qty) qty, sum(pol.total) total"
                        "from pos_order po, pos_order_line pol, product_product p"
                        "where po.session_id = %s and"
                        "      po.id = pol.order_id and"
                        "      pol.prduct_id = p.id"
                        "absl.statement_id = abs.id and abs.journal_id = aj.id  and absl.id IN %s " \
                        "group by p.name", session.id)

        allRecords = self.cr.dictfetchall()

        return allRecords

    def __init__(self, cr, uid, name, context):
        super(session_details, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_sales_by_product': self._get_sales_by_product,
        })


class report_session_details(osv.AbstractModel):
    _name = 'report.point_of_sale.report_sessionsummary'
    _inherit = 'report.abstract_report'
    _template = 'point_of_sale.report_sessionsummary'
    _wrapped_report_class = session_details

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
