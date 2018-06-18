# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent import _

def get_payment_url(doc, method):
	if doc.docstatus == 1:
		if doc.payment_gateway == "Razorpay":
			dataent.local.response["type"] = "redirect"
			dataent.local.response["location"] = "./razorpay_checkout?payment_request={0}".format(doc.name)
	else:
		dataent.respond_as_web_page(_("Invalid Payment Request"),
			_("Payment Request has been canceled by vendor"), success=False,
			http_status_code=dataent.ValidationError.http_status_code)

def validate_price_list_currency(doc, method):
	'''Called from Shopping Cart Settings hook'''
	if doc.enabled and doc.enable_checkout:
		if not doc.payment_gateway_account:
			doc.enable_checkout = 0
			return

		payment_gateway_account = dataent.get_doc("Payment Gateway Account", doc.payment_gateway_account)

		if payment_gateway_account.payment_gateway=="Razorpay":
			price_list_currency = dataent.db.get_value("Price List", doc.price_list, "currency")

			validate_transaction_currency(price_list_currency)

			if price_list_currency != payment_gateway_account.currency:
				dataent.throw(_("Currency '{0}' of Price List '{1}' should be same as the Currency '{2}' of Payment Gateway Account '{3}'").format(price_list_currency, doc.price_list, payment_gateway_account.currency, payment_gateway_account.name))

def validate_transaction_currency(transaction_currency):
	if transaction_currency != "INR":
		dataent.throw(_("Please select another payment method. Razorpay does not support transactions in currency '{0}'").format(transaction_currency))

def make_log_entry(error, params):
	dataent.db.rollback()

	dataent.get_doc({
		"doctype": "Razorpay Log",
		"error": error,
		"params": params
	}).insert(ignore_permissions=True)

	dataent.db.commit()

def get_razorpay_settings():
	settings = dataent.db.get_singles_dict('Razorpay Settings')

	if settings.api_key and settings.api_secret:
		settings["api_secret"] = dataent.get_doc("Razorpay Settings").get_password(fieldname="api_secret")

	elif not settings.api_key and dataent.local.conf.get('Razorpay Settings', {}).get('api_key'):
		settings = dataent._dict(dataent.local.conf['Razorpay Settings'])

	return settings
