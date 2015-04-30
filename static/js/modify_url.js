function modify_plus_button_url() {
    var meta_connector_sel = document.getElementById('id_meta_connector');
    var selected_mc = meta_connector_sel.options[meta_connector_sel.selectedIndex].value;
    var url_plus_button = document.getElementById('add_id_url_callback').href;
    if (selected_mc > 0) {
        document.getElementById('add_id_url_callback').style.visibility='visible';
        url_plus_button += '&mcid=' + selected_mc;
    }
    else {
        document.getElementById('add_id_url_callback').style.visibility='hidden';
        idx = url_plus_button.indexOf('&mcid=');
        if (idx != -1) {
            url_plus_button = url_plus_button.substring(0,idx);
        }
    }
    document.getElementById('add_id_url_callback').href = url_plus_button
}

(function($) {
    $(document).ready(function() {
        modify_plus_button_url()
        $("#id_meta_connector").change(function () {
            modify_plus_button_url()
        });
    });
})(django.jQuery);



