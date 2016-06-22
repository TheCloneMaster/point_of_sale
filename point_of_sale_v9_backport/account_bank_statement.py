# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 PC Solutions (<http://pcsol.be>). All Rights Reserved
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

from openerp.osv import fields, osv

class account_journal(osv.osv):
    _inherit = 'account.journal'
    _columns = {
        'journal_user': fields.boolean('PoS Payment Method', help="Check this box if this journal define a payment method that can be used in point of sales."),

        'amount_authorized_diff' : fields.float('Amount Authorized Difference', help="This field depicts the maximum difference allowed between the ending balance and the theorical cash when closing a session, for non-POS managers. If this maximum is reached, the user will have an error message at the closing of his session saying that he needs to contact his manager."),
        'self_checkout_payment_method' : fields.boolean('Self Checkout Payment Method'), #FIXME : this field is obsolete
    }
    _defaults = {
        'self_checkout_payment_method' : False,
    }


class account_cash_statement(osv.osv):
    _inherit = 'account.bank.statement'
    _columns = {
        'pos_session_id' : fields.many2one('pos.session', copy=False),
    }

    def balance_check(self, cr, uid, st_id, journal_type='bank', context=None):
        st = self.browse(cr, uid, st_id, context=context)

        if abs(st.difference) > st.journal_id.amount_authorized_diff:
            # The pos manager can close statements with maximums.
            if not self.pool.get('ir.model.access').check_groups(cr, uid, "point_of_sale.group_pos_manager"):
                raise osv.except_osv( _('Error!'),
                    _("Your ending balance is too different from the theoretical cash closing (%.2f), the maximum allowed is: %.2f. You can contact your manager to force it.") % (st.difference, st.journal_id.amount_authorized_diff))

        return True
        #old check in bank statement...
        if not ((abs((st.balance_end or 0.0) - st.balance_end_real) < 0.0001) or (abs((st.balance_end or 0.0) - st.balance_end_real) < 0.0001)):
            raise osv.except_osv(_('Error!'),
                    _('The statement balance is incorrect !\nThe expected balance (%.2f) is different than the computed one. (%.2f)') % (st.balance_end_real, st.balance_end))


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
