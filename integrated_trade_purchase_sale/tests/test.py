# -*- encoding: utf-8 -*-
##############################################################################
#
#    Integrated Trade - Purchase & Sale module for Odoo
#    Copyright (C) 2014-Today GRAP (http://www.grap.coop)
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
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

from openerp.osv.osv import except_osv
from openerp.tests.common import TransactionCase


class Test(TransactionCase):

    # Overload Section
    def setUp(self):
        super(Test, self).setUp()

        # Get Registries
        self.imd_obj = self.registry('ir.model.data')
        self.pp_obj = self.registry('product.product')
        self.po_obj = self.registry('purchase.order')
        self.pol_obj = self.registry('purchase.order.line')
        self.so_obj = self.registry('sale.order')
        self.sol_obj = self.registry('sale.order.line')
        self.rit_obj = self.registry('res.integrated.trade')
        self.pitc_obj = self.registry('product.integrated.trade.catalog')
        self.itwlp_obj = self.registry('integrated.trade.wizard.link.product')

        # Get ids from xml_ids
        self.rit_id = self.imd_obj.get_object_reference(
            self.cr, self.uid,
            'integrated_trade_base', 'integrated_trade')[1]
        self.rit = self.rit_obj.browse(self.cr, self.uid, self.rit_id)

        self.product_customer_apple =\
            self.imd_obj.get_object_reference(
                self.cr, self.uid, 'integrated_trade_product',
                'product_customer_apple')[1]

        self.product_supplier_apple =\
            self.imd_obj.get_object_reference(
                self.cr, self.uid, 'integrated_trade_product',
                'product_supplier_apple')[1]

        self.customer_user_id = self.imd_obj.get_object_reference(
            self.cr, self.uid,
            'integrated_trade_base', 'customer_user')[1]

        self.supplier_user_id = self.imd_obj.get_object_reference(
            self.cr, self.uid,
            'integrated_trade_base', 'supplier_user')[1]

    def test_01_create_purchase_order(self):
        """
            Create a Purchase Order (Supplier Invoice) by the customer
            must create a Sale Order
        """
        cr, cus_uid, sup_uid =\
            self.cr, self.customer_user_id, self.supplier_user_id

        sup_pp = self.pp_obj.browse(
            cr, sup_uid, self.product_supplier_apple)

        # Associate a product
        active_id = self.pitc_obj.search(cr, cus_uid, [(
            'supplier_product_id', '=',
            self.product_supplier_apple)])[0]

        itwlp_id = self.itwlp_obj.create(cr, cus_uid, {
            'customer_product_id': self.product_customer_apple,
        }, context={'active_id': active_id})
        self.itwlp_obj.link_product(cr, cus_uid, [itwlp_id])

        # Create a Purchase Order
        po_vals = {
            'partner_id': self.rit.supplier_partner_id.id,
            'invoice_method': 'picking',
        }
        po_vals.update(self.po_obj.onchange_partner_id(
            cr, cus_uid, False, self.rit.supplier_partner_id.id)['value'])
        po_vals.update(self.po_obj.onchange_dest_address_id(
            cr, cus_uid, False, self.rit.supplier_partner_id.id)['value'])

        cus_po_id = self.po_obj.create(cr, cus_uid, po_vals)

        # Checks creation of the according Sale Order
        SUPER_po = self.po_obj.browse(cr, self.uid, cus_po_id)
        SUPER_so_other = SUPER_po.integrated_trade_sale_order_id

        self.assertNotEqual(
            SUPER_so_other.id, False,
            """Create a Purchase Order must create a Sale Order.""")

        # Create a Purchase Order Line
        pol_vals = {
            'order_id': cus_po_id,
            'product_id': self.product_customer_apple,
        }
        pol_vals.update(self.pol_obj.onchange_product_id(
            cr, cus_uid, False, False, self.product_customer_apple, False,
            False, False)['value'])
        cus_pol_id = self.pol_obj.create(cr, cus_uid, pol_vals)

        # Checks creation of the according SO Line
        SUPER_pol = self.pol_obj.browse(cr, self.uid, cus_pol_id)
        SUPER_sol_other = SUPER_pol.integrated_trade_sale_order_line_id

        sup_sol_id = SUPER_sol_other.id

        self.assertNotEqual(
            SUPER_sol_other, False,
            """Create a PO Line must create a SO Line.""")

        self.assertEqual(
            SUPER_sol_other.price_unit, sup_pp.list_price,
            """Create a PO Line must automatically reset the"""
            """ price_unit, using the sale price of the supplier.""")

        # Update PO Line (change price = must fail)
        with self.assertRaises(except_osv):
            self.pol_obj.write(
                cr, cus_uid, [cus_pol_id], {'price_unit': sup_pp.list_price})

        # Update PO Line (change quantity = must succeed)
        self.pol_obj.write(
            cr, cus_uid, [cus_pol_id], {'product_qty': 2})
        SUPER_pol = self.pol_obj.browse(cr, self.uid, cus_pol_id)
        SUPER_sol_other = SUPER_pol.integrated_trade_sale_order_line_id

        self.assertEqual(
            SUPER_sol_other.price_subtotal, 2 * sup_pp.list_price,
            """Double Quantity asked by the customer must double price"""
            """ subtotal of the according Sale Order of the supplier.""")

        # Unlink PO line (must unlink according SO line)
        self.pol_obj.unlink(cr, cus_uid, [cus_pol_id])
        count_sol = self.sol_obj.search(cr, sup_uid, [('id', '=', sup_sol_id)])

        self.assertEqual(
            len(count_sol), 0,
            """Delete customer PO Line must delete according"""
            """ Supplier SO Line.""")

        # Unlink Purchase Order (must unlink according supplier Sale Order)
        # FIXME: See purchase_order.py file.
#        self.po_obj.unlink(cr, cus_uid, [cus_po_id])
#        count_so = self.so_obj.search(cr, sup_uid, [('id', '=', sup_so_id)])

#        self.assertEqual(
#            len(count_so), 0,
#            """Delete customer Purchase Order must delete according"""
#            """ Sale Order.""")

    def test_02_create_sale_order(self):
        """
            Create a Sale Order by the customer
            must create a Purchase Order
        """
        cr, cus_uid, sup_uid =\
            self.cr, self.customer_user_id, self.supplier_user_id

        # Associate a product
        active_id = self.pitc_obj.search(cr, cus_uid, [(
            'supplier_product_id', '=',
            self.product_supplier_apple)])[0]

        itwlp_id = self.itwlp_obj.create(cr, cus_uid, {
            'customer_product_id': self.product_customer_apple,
        }, context={'active_id': active_id})
        self.itwlp_obj.link_product(cr, cus_uid, [itwlp_id])

        # Create a Sale Order
        so_vals = self.po_obj.default_get(
            cr, sup_uid, ['shop_id'])

        so_vals.update({
            'partner_id': self.rit.customer_partner_id.id,
            'order_policy': 'picking',
        })
        so_vals.update(self.so_obj.onchange_partner_id(
            cr, sup_uid, False, self.rit.customer_partner_id.id)['value'])
        sup_so_id = self.so_obj.create(cr, sup_uid, so_vals)

        # Checks creation of the according Sale Order
        SUPER_so = self.so_obj.browse(cr, self.uid, sup_so_id)
        SUPER_po_other = SUPER_so.integrated_trade_purchase_order_id

        cus_po_id = SUPER_po_other.id

        self.assertNotEqual(
            cus_po_id, False,
            """Create a Sale Order must create a Purchase Order.""")

        # Create a Sale Order Line
        sol_vals = {
            'order_id': sup_so_id,
            'product_id': self.product_supplier_apple,
            'price_unit': 15,
        }
        sol_vals.update(self.sol_obj.product_id_change(
            cr, sup_uid, False, False, self.product_supplier_apple,
            partner_id=self.rit.customer_partner_id.id)['value'])
        sup_sol_id = self.sol_obj.create(cr, sup_uid, sol_vals)

        # Checks creation of the according PO Line
        SUPER_sol = self.sol_obj.browse(cr, self.uid, sup_sol_id)
        SUPER_pol_other = SUPER_sol.integrated_trade_purchase_order_line_id

        cus_pol_id = SUPER_pol_other.id

        self.assertNotEqual(
            cus_pol_id, False,
            """Create a PO Line must create a SO Line.""")

        # Update SO Line (change quantity = must succeed)
        self.sol_obj.write(
            cr, sup_uid, [sup_sol_id], {
                'product_uom_qty': 2,
                'product_uos_qty': 2,
            })
        SUPER_sol = self.sol_obj.browse(cr, self.uid, sup_sol_id)
        SUPER_pol_other = SUPER_sol.integrated_trade_purchase_order_line_id

        self.assertEqual(
            SUPER_pol_other.price_subtotal, 2 * 15,
            """Double Quantity asked by the supplier must double price"""
            """ subtotal of the according Sale Order of the customer.""")

        # Unlink customer SO line (must unlink according PO line)
        self.sol_obj.unlink(cr, sup_uid, [sup_sol_id])
        count_pol = self.pol_obj.search(cr, cus_uid, [('id', '=', cus_pol_id)])

        self.assertEqual(
            len(count_pol), 0,
            """Delete supplier SO Line must delete according"""
            """ customer PO Line.""")

        # Unlink SO (must unlink according Customer PO)
        self.so_obj.unlink(cr, sup_uid, [sup_so_id])
        count_po = self.po_obj.search(cr, cus_uid, [('id', '=', cus_po_id)])

        self.assertEqual(
            len(count_po), 0,
            """Delete Supplier SO must delete according"""
            """ Customer PO.""")