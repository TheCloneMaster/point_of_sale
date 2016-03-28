# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Serial port ESC/POS Hardware Driver',
    'version': '1.0',
    'category': 'Hardware Drivers',
    'sequence': 6,
    'website': 'https://www.odoo.com/page/point-of-sale',
    'summary': 'Hardware Driver for Serial Port ESC/POS Printers and Cashdrawers',
    'description': """
ESC/POS Hardware Driver
=======================

This module allows openerp to print with Serial Port ESC/POS compatible printers
and to open ESC/POS controlled cashdrawers in the point of sale and other modules
that would need such functionality.

""",
    'depends': ['hw_proxy'],
    'external_dependencies': {
        'python' : ['serial','qrcode'],
    },
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}
