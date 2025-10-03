function padNumber(num) {
    return num.toString().padStart(2, '0');
}
frappe.ui.form.on('POS Opening Entry', {
	onload: function(frm){
		frappe.call({
            method: `ury.ury.hooks.pos_opening.get_current_date`,
            callback: function (r) {
				if(frm.doc.docstatus === 0){
					frm.set_value("period_start_date",r.message.date_time);
					frm.set_value("posting_date", r.message.today);
				}
				cur_frm.refresh_field("posting_date");
				cur_frm.refresh_field("period_start_date");
			   
            },
        });
		// fetch('https://worldtimeapi.org/api/ip')
        // .then(response => response.json())
        // .then(data => {
        //     // Extract the time from the response and set it to the "posting_time" field
        //     const internetTime = data.utc_datetime;
        //     // Convert the internet time to a Date object
        //     const dateObject = new Date(internetTime);
            
        //     // Format the date for display
        //     const formattedDateTime =
        //     `${dateObject.getFullYear()}-${padNumber(dateObject.getMonth() + 1)}-${padNumber(dateObject.getDate())} ` +
        //     `${padNumber(dateObject.getHours())}:${padNumber(dateObject.getMinutes())}:${padNumber(dateObject.getSeconds())}`;
        //     const formattedDate =
        //         dateObject.getFullYear() + '-' +
        //         padNumber(dateObject.getMonth() + 1) + '-' +
        //         padNumber(dateObject.getDate());
        //     const formattedTime = dateObject.toLocaleTimeString('en-US', { hour12: false });
            // if(frm.doc.docstatus === 0){
            //     frm.set_value("period_start_date", formattedDateTime);
            //      frm.set_value("posting_date", formattedDate);
            // }
            // cur_frm.refresh_field("period_start_date");
            // cur_frm.refresh_field("posting_date");
            // })
        // .catch(error => {
        //     console.error('Error fetching internet time:', error);
        // });
	},
	custom_shift_type:function(frm){
		frappe.call({
            method: `ury.ury.hooks.pos_opening.get_shift`,
            args: {
              shift_type: frm.doc.custom_shift_type,
            },
            callback: function (r) {
				frm.set_value("custom_employee", r.message.employee);
            },
        });
	},
	check_validation:function(frm){
	    if (frm.doc.check_validation == 1){
	        frm.trigger('validate_stock_reconciliation')
	    }
	},
	validate_stock_reconciliation: function(frm){
        frappe.dom.freeze();
		frappe.call({
			method: 'frappe.client.get_list',
			args: {
				doctype: 'POS Opening Entry',
				fields: ['modified','status'],
				filters: {
					'branch': frm.doc.branch,
					'docstatus': 1
				},
				order_by: 'creation desc',
			},
			callback: function(response) {
			    if (response.message && response.message.length > 0) {
			        if (response.message[0].status == "Closed"){
				        let pos_closed_modified = response.message[0].modified
				        frappe.call({
            				method: 'frappe.client.get_list',
            				args: {
            					doctype: 'Stock Correction',
            					fields: ['modified'],
            					filters: {
            						'branch': frm.doc.branch,
            						'docstatus': 1
            					},
            					order_by: 'modified desc',
            				},
            				callback: function(response) {
            				    if (response.message && response.message.length > 0) {
            				        let stock_recon_modified = response.message[0].modified
            				        if(stock_recon_modified < pos_closed_modified){
            				            frappe.msgprint({
                                            'title': 'Stock Correction Not Completed',
                                            'message': 'Try again after submiting Stock Correction',
                                            'indicator': 'red'
                                        });
                						document.addEventListener('click', function() {
                                            window.location.href = '/app'
                                        });
            				        }
            				        else{
            				            console.log("STOCK RECON COMPLETED")
            				            frappe.dom.unfreeze();
            				        }
            				    }
            				    else{
            				        console.log("STOCK RECON NOT FOUND")
            				        frappe.msgprint({
                                        'title': 'Stock Correction Not Completed',
                                        'message': 'Try again after submiting Stock Correction',
                                        'indicator': 'red'
                                    });
            						document.addEventListener('click', function() {
                                        window.location.href = '/app'
                                    });
            				    }
            				}
            			});
			        }
			        else{
			            console.log("POS NOT CLOSED")
			            frappe.dom.unfreeze();
			        }
			    }
			}
		});
	}
})