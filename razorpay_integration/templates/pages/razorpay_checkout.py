# Copyright (c) 2015, Dataent Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals
import dataent
from dataent import _
from dataent.utils import get_url, flt
from razorpay_integration.utils import make_log_entry, validate_transaction_currency, get_razorpay_settings
from razorpay_integration.exceptions import InvalidRequest, AuthenticationError, GatewayError
import urllib

no_cache = 1
no_sitemap = 1

expected_keys = ('amount', 'title', 'description', 'doctype', 'name',
	'payer_name', 'payer_email', 'order_id')

def get_context(context):
	context.no_cache = 1
	context.api_key = get_razorpay_settings().api_key

	context.brand_image = (dataent.db.get_value("Razorpay Settings", None, "brand_image")
		or './assets/epaas/images/erp-icon.svg')

	if dataent.form_dict.payment_request:
		payment_req = dataent.get_doc('Payment Request', dataent.form_dict.payment_request)
		validate_transaction_currency(payment_req.currency)

		if payment_req.status == "Paid":
			dataent.redirect_to_message(_('Already Paid'), _('You have already paid for this order'))
			return

		reference_doc = dataent.get_doc(payment_req.reference_doctype, payment_req.reference_name)

		context.amount = payment_req.grand_total
		context.title = reference_doc.company
		context.description = payment_req.subject
		context.doctype = payment_req.doctype
		context.name = payment_req.name
		context.payer_name = reference_doc.customer_name
		context.payer_email = reference_doc.get('email_to') or dataent.session.user
		context.order_id = payment_req.name
		context.reference_doctype = payment_req.reference_doctype
		context.reference_name = payment_req.reference_name

	# all these keys exist in form_dict
	elif not (set(expected_keys) - set(dataent.form_dict.keys())):
		for key in expected_keys:
			context[key] = dataent.form_dict[key]

		context['amount'] = flt(context['amount'])
		context['reference_doctype'] = context['reference_name'] = None

	else:
		dataent.redirect_to_message(_('Some information is missing'), _('Looks like someone sent you to an incomplete URL. Please ask them to look into it.'))
		dataent.local.flags.redirect_location = dataent.local.response.location
		raise dataent.Redirect

def get_checkout_url(**kwargs):
	missing_keys = set(expected_keys) - set(kwargs.keys())
	if missing_keys:
		dataent.throw(_('Missing keys to build checkout URL: {0}').format(", ".join(list(missing_keys))))

	return get_url('/razorpay_checkout?{0}'.format(urllib.urlencode(kwargs)))

@dataent.whitelist(allow_guest=True)
def make_payment(razorpay_payment_id, options, reference_doctype, reference_docname):
	try:
		razorpay_payment = dataent.get_doc({
			"doctype": "Razorpay Payment",
			"razorpay_payment_id": razorpay_payment_id,
			"data": options,
			"reference_doctype": reference_doctype,
			"reference_docname": reference_docname
		})

		razorpay_payment.insert(ignore_permissions=True)

		if dataent.db.get_value("Razorpay Payment", razorpay_payment.name, "status") == "Authorized":
			return {
				"redirect_to": razorpay_payment.flags.redirect_to or "razorpay-payment-success",
				"status": 200
			}

	except AuthenticationError, e:
		make_log_entry(e.message, options)
		return{
			"redirect_to": dataent.redirect_to_message(_('Server Error'), _("Seems issue with server's razorpay config. Don't worry, in case of failure amount will get refunded to your account.")),
			"status": 401
		}

	except InvalidRequest, e:
		make_log_entry(e.message, options)
		return {
			"redirect_to": dataent.redirect_to_message(_('Server Error'), _("Seems issue with server's razorpay config. Don't worry, in case of failure amount will get refunded to your account.")),
			"status": 400
		}

	except GatewayError, e:
		make_log_entry(e.message, options)
		return {
			"redirect_to": dataent.redirect_to_message(_('Server Error'), _("Seems issue with server's razorpay config. Don't worry, in case of failure amount will get refunded to your account.")),
			"status": 500
		}
