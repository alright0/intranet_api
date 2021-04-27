function responsive_plot(plot_json, div_id, WIDTH = 99, HEIGHT = 50) {
    var d3 = Plotly.d3;

    /* ширина и высота родительского элемента*/
    var gd3 = d3.select('#' + div_id)
        .style({
            width: WIDTH + '%',
            height: HEIGHT + 'vh',
        });

    var gd = gd3.node();


    /*встраивание переменной jinja2*/
    var graph_json = plot_json;

    /*здесь создается график*/
    graph = Plotly.plot(div_id, graph_json);

    /* событие изменения ширины*/
    window.addEventListener("resize", function (event) {
        gd3.style({
            width: WIDTH + '%',
            height: HEIGHT + 'vh',
        });
        gd = gd3.node()
        Plotly.Plots.resize(gd);;
    });
};

function get_response(requst_form) {
    var form = $("#" + requst_form);
    $.ajax({
        type: form.attr('method'),
        url: form.attr('action'),
        data: form.serialize(),
        success: function (response) {
            var server_data = jQuery.parseJSON(response);
            var figure = jQuery.parseJSON(server_data.plot);
            var average_table = server_data.average;

            $("#average_container").empty();
            $.each(average_table, function (index) {
                $("#average_container").append(`<div class="production_plan_stdblock" 
                    id="#line_average_${index}"><p>${index}</p> ${average_table[index]}</div>`);
            });

            Plotly.newPlot("plot", figure.data, figure.layout);
            $('#table').html(server_data.table);

        }

    });
};