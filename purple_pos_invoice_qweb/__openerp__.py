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

{
    'name' : 'POS Print receipt as Invoice',
    'version' : '1.0',
    'author' : 'CYSFuturo',
    'summary': 'POS receipts as a full page Invoice',
    'description': """
Prints the POS receipts as a full page Invoices
    """,
    'category': 'Accounting & Finance',
    'sequence': 4,
    'website' : 'http://cysfuturo.com',
    'depends' : ['point_of_sale'],
    'demo' : [],
    'data' : [
        'pos_invoice_view.xml',
        'views/report_pos_invoice_qweb.xml',
    ],
    'test' : [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
