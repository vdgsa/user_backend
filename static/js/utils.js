// Use for showing/hiding a particular element when a radio
// button has a specific value.
// Note that this function will also register a "ready" handler that shows
// or hides the element on page load.
//
// Positional parameters:
// - radio_buttons_name: The "name" attribute for the radio buttons
// - element_to_toggle_selector: A CSS selector for the element to toggle
// Keyword parameters:
// - show_values: A list of values for which the element to toggle should be shown.
//                Defaults to ['yes']
// - on_change: A callback that will be called with the value of the currently
//              selected radio button. Defaults to a no-op.
function radio_button_hide(
    radio_buttons_name,
    element_to_toggle_selector,
    args = {
        show_values: ['yes'],
        on_change: function() {}
    }
) {
    if (args.show_values === undefined) {
        args.show_values = ['yes'];
    }
    if (args.on_change === undefined) {
        args.on_change = function() {};
    };
    $().ready(function() {
        let initial_value = $(`input[name="${radio_buttons_name}"]:checked`).val();
        if (args.show_values.includes(initial_value)) {
            $(element_to_toggle_selector).show();
        }
        else {
            $(element_to_toggle_selector).hide();
        }

        $(`input[name="${radio_buttons_name}"]`).change(function() {
            let value = $(this).val();
            if (args.show_values.includes(value)) {
                $(element_to_toggle_selector).show();
                args.on_change(value);
            }
            else {
                $(element_to_toggle_selector).hide();
                args.on_change(value);
            }
        });
    });
}
