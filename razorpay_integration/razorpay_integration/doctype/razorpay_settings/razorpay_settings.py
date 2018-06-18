# -*- coding: utf-8 -*-
# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import dataent
from dataent import _
from dataent.model.document import Document
from razorpay_integration.utils import get_razorpay_settings
from razorpay_integration.razorpay_requests import get_request
from razorpay_integration.exceptions import AuthenticationError

class RazorpaySettings(Document):
	def validate(self):
		validate_razorpay_credentials(razorpay_settings=dataent._dict({
			"api_key": self.api_key,
			"api_secret": self.get_password(fieldname="api_secret")
		}))

	def on_update(self):
		create_payment_gateway_and_account()

def validate_razorpay_credentials(doc=None, method=None, razorpay_settings=None):
	if not razorpay_settings:
		razorpay_settings = get_razorpay_settings()

	try:
		get_request(url="https://api.razorpay.com/v1/payments", auth=dataent._dict({
			"api_key": razorpay_settings.api_key,
			"api_secret": razorpay_settings.api_secret
		}))
	except AuthenticationError, e:
		dataent.throw(_(e.message))

def create_payment_gateway_and_account():
	"""If EPAAS is installed, create Payment Gateway and Payment Gateway Account"""
	if "epaas" not in dataent.get_installed_apps():
		return

	create_payment_gateway()
	create_payment_gateway_account()

def create_payment_gateway():
	# NOTE: we don't translate Payment Gateway name because it is an internal doctype
	if not dataent.db.exists("Payment Gateway", "Razorpay"):
		payment_gateway = dataent.get_doc({
			"doctype": "Payment Gateway",
			"gateway": "Razorpay"
		})
		payment_gateway.insert(ignore_permissions=True)

def create_payment_gateway_account():
	from epaas.setup.setup_wizard.setup_wizard import create_bank_account

	company = dataent.db.get_value("Global Defaults", None, "default_company")
	if not company:
		return

	# NOTE: we translate Payment Gateway account name because that is going to be used by the end user
	bank_account = dataent.db.get_value("Account", {"account_name": _("Razorpay"), "company": company},
		["name", 'account_currency'], as_dict=1)

	if not bank_account:
		# check for untranslated one
		bank_account = dataent.db.get_value("Account", {"account_name": "Razorpay", "company": company},
			["name", 'account_currency'], as_dict=1)

	if not bank_account:
		# try creating one
		bank_account = create_bank_account({"company_name": company, "bank_account": _("Razorpay")})

	if not bank_account:
		dataent.throw(_("Payment Gateway Account not created, please create one manually."))

	# if payment gateway account exists, return
	if dataent.db.exists("Payment Gateway Account",
		{"payment_gateway": "Razorpay", "currency": bank_account.account_currency}):
		return

	try:
		dataent.get_doc({
			"doctype": "Payment Gateway Account",
			"is_default": 1,
			"payment_gateway": "Razorpay",
			"payment_account": bank_account.name,
			"currency": bank_account.account_currency
		}).insert(ignore_permissions=True)

	except dataent.DuplicateEntryError:
		# already exists, due to a reinstall?
		pass
