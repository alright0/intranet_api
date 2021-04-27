function get_response(requst_form) {
    var form = $("#" + requst_form);
    $.ajax({
        type: form.attr('method'),
        url: form.attr('action'),
        data: form.serialize(),
        success: function (response) {
            var data = jQuery.parseJSON(response);

            $('#' + table).html(data);

        }

    });
};

function insert_data(server_data, id) {
    $('#' + id).html(server_data);
};
// /*$('#' + changed_form).html(new_data);*/