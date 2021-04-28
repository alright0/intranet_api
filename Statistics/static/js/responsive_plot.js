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

/*функция возвращает ответы сервера в production plan*/
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

            /* очистить контейнер, содержащий элементы средней выработки */
            $("#average_container").empty();

            /* наполнить контейнер средней выработки заново */
            $.each(average_table, function (index) {
                $("#average_container").append(`<div class="production_plan_stdblock" 
                    id="#line_average_${index}"><p>${index}</p> ${average_table[index]}</div>`);
            });

            /* построить график и встроить его в таблицу */
            Plotly.newPlot("plot", figure.data, figure.layout);

            /* вставить актуальную таблицу выработки по сменам */
            $('#table').html(server_data.table);

        }

    });
};


/* функция вызывается из источника по событию on_click 
и отмечает все чекбоксы с указанным именем */
function toggle_all(source, elem_name) {

    /* обратиться к каждому элементу по имени */
    checkboxes = document.getElementsByName(elem_name);

    /* передать каждому элементу состояние чекбокса, из которого вызывается скрипт */
    for (var i = 0, n = checkboxes.length; i < n; i++) {
        checkboxes[i].checked = source.checked;
    }
}

function daily_report_return(request_form) {
    var form = $(`#${request_form}`);
    $.ajax({
        type: form.attr('method'),
        url: form.attr('action'),
        data: form.serialize(),
        success: function (response) {

            var plots = jQuery.parseJSON(response);

            /* очистка контейнера с графиками */
            $("#main_container").empty();

            if (Object.keys(plots).length > 0) {
                /* for each для списка линий */
                $.each(plots, function (line) {
                    $("#main_container").append(
                        `<div class="graph_container" id="graph_container_${line}"></div>`);

                    var plot = plots[line];

                    /* for each для списка смен */
                    $.each(plot, function (shift) {

                        var graph_info = jQuery.parseJSON(plot[shift]);

                        /* добавление в основной график контейнеров для графиков */
                        $(`#graph_container_${line}`).append(
                            `<div class="graph_container" id="graph_container_${line}_${shift}">
                    </div>`);

                        /* создание графиков */
                        responsive_plot(graph_info, `graph_container_${line}_${shift}`);

                    });
                });
            } else {
                $("#main_container").append("<p>Нет данных для отображения</p>")
            };

        },
        error: function () { $("#main_container").append("<p>Нет данных для отображения</p>"); }

    })
};