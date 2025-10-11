
let user_input = $("#user-input")
let userSelect = $('#replaceable-content')
const endpoint = '/rentals/user/search'
const delay_by_in_ms = 700
let scheduled_function = false


$().ready(function() {

 user_input = $("#user-input")
 userPickList = $('#replaceable-content')


let ajax_call = function (endpoint, request_parameters) {
	$.getJSON(endpoint, request_parameters)
		.done(response => {
			// fade out the userSelect, then:
			userPickList.fadeTo('fast', 0).promise().then(() => {
				// replace the HTML contents
				userPickList.html(response['html_from_view'])
				// fade-in the div with new contents
				userPickList.fadeTo('fast', 1)
			})
		})
}


user_input.on('keyup', function () {
	
	const request_parameters = {
		q: $(this).val() // value of user_input: the HTML element with ID user-input
	}

	// if scheduled_function is NOT false, cancel the execution of the function
	if (scheduled_function) {
		clearTimeout(scheduled_function)
	}

	// setTimeout returns the ID of the function to be executed
	scheduled_function = setTimeout(ajax_call, delay_by_in_ms, endpoint, request_parameters)
})
})
