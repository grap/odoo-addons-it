# -*- coding: utf-8 -*-
# Copyright (C) 2015 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from openerp.exceptions import Warning as UserError
from openerp.tests.common import TransactionCase


class Test(TransactionCase):

    # Overload Section
    def setUp(self):
        super(Test, self).setUp()

        # Get Registries
        self.invoice_obj = self.env['account.invoice']
        self.invoice_line_obj = self.env['account.invoice.line']
        self.product_obj = self.env['product.product]
        self.catalog_obj = self.env['product.intercompany.trade.catalog']
        self.config_obj = self.env['intercompany.trade.config']
        self.link_obj = self.env['intercompany.trade.wizard.link.product']

        # Get ids from xml_ids
        self.config = self.env.ref(
            'intercompany_trade_base.intercompany_trade')

        self.customer_user = self.env.ref(
            'intercompany_trade_base.customer_user')
        self.supplier_user = self.env.ref(
            'intercompany_trade_base.supplier_user')

        self.product_uom_unit = self.env.ref(
            'product.product_uom_unit')

        self.product_customer_apple = self.env.ref(
            'intercompany_trade_product.product_customer_apple')

        self.product_supplier_service_25_incl = self.env.ref(
            'intercompany_trade_account.product_supplier_service_25_incl')
        self.product_supplier_service_10_incl = self.env.ref(
            'intercompany_trade_account.product_supplier_service_10_incl')
        self.product_supplier_service_10_excl = self.env.ref(
            'intercompany_trade_account.product_supplier_service_10_excl')
        self.product_customer_service_10_excl = self.env.ref(
            'intercompany_trade_account.product_customer_service_10_excl')
        self.purchase_journal = self.env.ref(
            'intercompany_trade_account.customer_journal_purchase')
        self.customer_account_payable = self.env.ref(
            'intercompany_trade_account.customer_account_payable')


    def test_01_vat_association_bad(self):
        """
            [Functional Test] Associate products with incompatible VAT
            must fail
        """
        cr, uid = self.cr, self.customer_user.id

        # Associate with bad VAT
        # (Customer Service VAT 10% EXCLUDED - Supplier Service VAT 25%)
        active_id = self.pitc_obj.search(cr, uid, [(
            'supplier_product_id', '=',
            self.product_supplier_service_25_incl.id)])[0]

        itwlp_id = self.itwlp_obj.create(cr, uid, {
            'customer_product_id': self.product_customer_service_10_excl.id,
        }, context={'active_id': active_id})
        with self.assertRaises(UserError):
            self.itwlp_obj.link_product(cr, uid, [itwlp_id])

        # Associate with bad VAT
        # (Customer Product with no VAT -> Supplier Service VAT 25%)
        active_id = self.pitc_obj.search(cr, uid, [(
            'supplier_product_id', '=',
            self.product_supplier_service_25_incl.id)])[0]

        itwlp_id = self.itwlp_obj.create(cr, uid, {
            'customer_product_id': self.product_customer_apple.id,
        }, context={'active_id': active_id})
        with self.assertRaises(UserError):
            self.itwlp_obj.link_product(cr, uid, [itwlp_id])

####    def test_02_vat_association_good(self):
####        """
####            [Functional Test] Associate products with compatible VAT
####            must succeed (Incl / excl)
####        """
####        cr, uid = self.cr, self.customer_user.id
####        # Associate with good VAT
####        # (Customer Service VAT 10% EXCLUDED
####        # -> Supplier Service VAT 10% INCLUDE)
####        active_id = self.pitc_obj.search(cr, uid, [(
####            'supplier_product_id', '=',
####            self.product_supplier_service_10_incl.id)])[0]

####        itwlp_id = self.itwlp_obj.create(cr, uid, {
####            'customer_product_id': self.product_customer_service_10_excl.id,
####        }, context={'active_id': active_id})

####        try:
####            self.itwlp_obj.link_product(cr, uid, [itwlp_id])
####        except:
####            self.assertTrue(
####                """Associate a Customer Product with 10% Excl VAT to """
####                """ a supplier Product with 10% Incl VAT"""
####                """ must succeed.""")

####    def test_03_create_invoice_in(self):
####        """
####            Create an In Invoice (Supplier Invoice) by the customer
####            must create an Out Invoice
####        """
####        cr, cus_uid, sup_uid =\
####            self.cr, self.customer_user.id, self.supplier_user.id

####        # Associate a product
####        active_id = self.pitc_obj.search(cr, cus_uid, [(
####            'supplier_product_id', '=',
####            self.product_supplier_service_10_excl.id)])[0]

####        itwlp_id = self.itwlp_obj.create(cr, cus_uid, {
####            'customer_product_id': self.product_customer_service_10_excl.id,
####        }, context={'active_id': active_id})
####        self.itwlp_obj.link_product(cr, cus_uid, [itwlp_id])

####        sup_pp = self.pp_obj.browse(
####            cr, sup_uid, self.product_supplier_service_10_excl.id)

####        # Create a Invoice
####        context = {
####            'type': 'in_invoice',
####            'tracking_disable': True,
####        }
####        vals = self.ai_obj.default_get(
####            cr, cus_uid, ['currency_id', 'journal_id'],
####            context=context)
####        vals.update({
####            'partner_id': self.config.supplier_partner_id.id,
####            'account_id': self.customer_account_payable.id,
####        })

####        cus_ai_id = self.ai_obj.create(cr, cus_uid, vals, context=context)

####        # Checks creation of the according Invoice
####        SUPER_ai = self.ai_obj.browse(cr, self.uid, cus_ai_id)
####        SUPER_ai_other = self.ai_obj(
####            cr, self.uid, SUPER_ai.intercompany_trade_account_invoice_id)

####        sup_ai_id = SUPER_ai.intercompany_trade_account_invoice_id

####        self.assertNotEqual(
####            SUPER_ai_other.id, False,
####            """Create a Invoice must create another invoice.""")

####        self.assertEqual(
####            SUPER_ai_other.type, 'out_invoice',
####            """Create an In Invoice must create an Out invoice.""")

####        # Create a Invoice Line
####        vals = self.ail_obj.default_get(
####            cr, cus_uid, ['account_id', 'quantity'],
####            context=context)
####        vals.update({
####            'invoice_id': cus_ai_id,
####            'name': 'TEST',
####            'product_id': self.product_customer_service_10_excl.id,
####            'uos_id': self.product_uom_unit.id,
####        })

####        cus_ail_id = self.ail_obj.create(cr, cus_uid, vals, context=context)

####        # Checks creation of the according Invoice Line
####        SUPER_ail = self.ail_obj.browse(cr, self.uid, cus_ail_id)
####        SUPER_ail_other = SUPER_ail.intercompany_trade_account_invoice_line_id

####        sup_ail_id = SUPER_ail.intercompany_trade_account_invoice_line_id.id

####        self.assertNotEqual(
####            SUPER_ail_other, False,
####            """Create a Invoice Line must create another invoice Line.""")

####        sup_pp = sup_pp
####        # self.assertEqual(
####        #    SUPER_ail_other.price_unit, sup_pp.list_price,
####        #    """Create a In Invoice Line must automatically reset the"""
####        #    """ price_unit, using the sale price of the supplier.""")

####        # Update Invoice Line (change price = must fail)
####        with self.assertRaises(UserError):
####            self.ail_obj.write(
####                cr, cus_uid, [cus_ail_id], {'price_unit': 10}, context=context)

####        # Update Invoice Line (change quantity = must succeed)
####        # self.ail_obj.write(
####        #    cr, cus_uid, [cus_ail_id], {'quantity': 2}, context=context)
####        # SUPER_ail = self.ail_obj.browse(cr, self.uid, cus_ail_id)
####        # SUPER_ail_other =\
####        #     SUPER_ail.intercompany_trade_account_invoice_line_id

####        # self.assertEqual(
####        #    SUPER_ail_other.price_subtotal, 2 * sup_pp.list_price,
####        #    """Double Quantity asked by the customer must double price"""
####        #    """ subtotal of the according Sale Invoice of the supplier.""")

####        # Unlink customer Invoice line (must unlink according supplier line)
####        self.ail_obj.unlink(cr, cus_uid, [cus_ail_id], context=context)
####        count_ail = self.ail_obj.search(cr, sup_uid, [('id', '=', sup_ail_id)])

####        self.assertEqual(
####            len(count_ail), 0,
####            """Delete customer Invoice Line must delete according"""
####            """ Supplier Invoice Line.""")

####        # Unlink customer Invoice (must unlink according supplier Invoice)
####        self.ai_obj.unlink(cr, cus_uid, [cus_ai_id], context=context)
####        count_ai = self.ai_obj.search(cr, sup_uid, [('id', '=', sup_ai_id)])

####        self.assertEqual(
####            len(count_ai), 0,
####            """Delete customer Invoice must delete according"""
####            """ Supplier Invoice.""")
