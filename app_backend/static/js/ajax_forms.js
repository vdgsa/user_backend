function disable_form_buttons(form) {
  form.find('button').attr('disabled', true);
}

// IMPORTANT: This default class selector should match the class used in
// templates/utils/form_body.tmpl
// Check for other occurrences of this class when changing.
function update_form_body(form, response_data, body_selector = '.form-body-wrapper') {
  if (response_data.rendered_form) {
    form.find(body_selector).html(response_data.rendered_form);
  }
}

function reenable_form_buttons(form) {
  form.find('button').attr('disabled', false);
}

function setup_ajax_submit(
  form_id,
  {
    before_submit = disable_form_buttons,
    success = update_form_body,
    complete = reenable_form_buttons,
  }
) {
  let form = $('#' + form_id);
  form.on('submit', function(event) {
    event.preventDefault();
    before_submit(form);

    $.ajax(form.attr('action'), {
      type: 'POST',
      headers: {
          'X-CSRFToken': get_cookie('csrftoken')
      },
      data: form.serialize(),
      success: function(data) {
        success(form, data)
      },
      error: function(response) {
        console.log(response);
        // TODO: detect network/other errors and adjust message
        alert('An unexpected error occured');
      },
      complete: function() {
        complete(form);
      }
    });
  });
}

// Source: https://docs.djangoproject.com/en/3.1/ref/csrf/#ajax
function get_cookie(name) {
  let cookie_value = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookie_value = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookie_value;
}
