// Copyright (c) 2016, Dataent Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

dataent.ui.form.on('Razorpay Settings', {
	refresh: function(frm) {
		frm.add_custom_button(__("Razorpay Logs"), function() {
			dataent.set_route("List", "Razorpay Log");
		})
		frm.add_custom_button(__("Payment Logs"), function() {
			dataent.set_route("List", "Razorpay Payment");
		});
		frm.add_custom_button(__("Payment Gateway Accounts"), function() {
			dataent.route_options = {"payment_gateway": "Razorpay"};
			dataent.set_route("List", "Payment Gateway Account");
		});
	}
});
