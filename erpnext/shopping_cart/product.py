# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe.utils import cint, fmt_money
from erpnext.shopping_cart.cart import _get_cart_quotation
from erpnext.shopping_cart.doctype.shopping_cart_settings.shopping_cart_settings import is_cart_enabled

@frappe.whitelist(allow_guest=True)
def get_product_info(item_code):
	"""get product price / stock info"""
	if not is_cart_enabled():
		return {}

	qty = 0
	cart_quotation = _get_cart_quotation()
	template_item_code = frappe.db.get_value("Item", item_code, "variant_of")
	in_stock = get_qty_in_stock(item_code, template_item_code)
	price = get_price(item_code, template_item_code, cart_quotation.selling_price_list)

	if price:
		price["formatted_price"] = fmt_money(price["price_list_rate"], currency=price["currency"])

		price["currency"] = not cint(frappe.db.get_default("hide_currency_symbol")) \
			and (frappe.db.get_value("Currency", price.currency, "symbol") or price.currency) \
			or ""

		if frappe.session.user != "Guest":
			item = cart_quotation.get({"item_code": item_code})
			if item:
				qty = item[0].qty

	return {
		"price": price,
		"stock": in_stock,
		"uom": frappe.db.get_value("Item", item_code, "stock_uom"),
		"qty": qty
	}

def get_qty_in_stock(item_code, template_item_code):
	warehouse = frappe.db.get_value("Item", item_code, "website_warehouse")
	if not warehouse and template_item_code and template_item_code != item_code:
		warehouse = frappe.db.get_value("Item", template_item_code, "website_warehouse")

	if warehouse:
		in_stock = frappe.db.sql("""select actual_qty from tabBin where
			item_code=%s and warehouse=%s""", (item_code, warehouse))
		if in_stock:
			in_stock = in_stock[0][0] > 0 and 1 or 0

	else:
		in_stock = -1

	return in_stock

def get_price(item_code, template_item_code, price_list):
	if price_list:
		price = frappe.get_all("Item Price", fields=["price_list_rate", "currency"],
			filters={"price_list": price_list, "item_code": item_code})

		if not price:
			price = frappe.get_all("Item Price", fields=["price_list_rate", "currency"],
				filters={"price_list": price_list, "item_code": template_item_code})

		if price:
			return price[0]
