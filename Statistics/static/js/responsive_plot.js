// функция, добавляющая адаптивность для графиков plotly
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
    graph = Plotly.newPlot(div_id, graph_json);

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

// функция возвращает ответы сервера в production plan
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


// функция тмечает все чекбоксы с указанным именем
function toggle_all(source, elem_name) {

    // обратиться к каждому элементу по имени
    checkboxes = document.getElementsByName(elem_name);

    // передать каждому элементу состояние чекбокса, из которого вызывается скрипт
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

            // очистка контейнера с графиками
            $("#main_container").empty();

            if (Object.keys(plots).length > 0) {
                // for each для списка линий
                $.each(plots, function (line) {
                    $("#main_container").append(
                        `<div class="graph_container" id="graph_container_${line}"></div>`);

                    var plot = plots[line];

                    // for each для списка смен 
                    $.each(plot, function (shift) {

                        var graph_info = jQuery.parseJSON(plot[shift]);

                        // добавление в основной график контейнеров для графиков 
                        $(`#graph_container_${line}`).append(
                            `<div class="graph_container" id="graph_container_${line}_${shift}">
                    </div>`);

                        // создание графиков
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


function update_current_situation() {
    $.ajax({
        type: "POST",
        url: "#",
        success: function (response) {
            var answer = jQuery.parseJSON(response);
            $.each(answer, function (line) {

                var line_info = answer[line];

                // если статус линии меняется, необходимо поменять сообщение в блоке статуса и класс
                var status = line_info.status;
                var operator = line_info.operator;
                var input = line_info.input;
                var output = line_info.output;
                var defect_rate = line_info.camera;

                // создание строки заказа 
                if (line_info.order.order && line_info.order.description) {
                    var order = `<b>${line_info.order.order}</b>: ${line_info.order.description}`;
                } else {
                    var order = "";
                };

                $(`#status_${line}_p`).text(status);

                // сообщение линии: STOP, RUN, N-A или детальное сообщение об остановке
                if (status.length <= 5) {
                    $(`#status_${line}`).attr('class', `infoboard_block_section status_no_message`);
                    $(`#${line}_container`).attr('class', `infoboard_block ${status}`);
                } else {
                    $(`#status_${line}`).attr('class', `infoboard_block_section status_message`);
                    $(`#${line}_container`).attr('class', `infoboard_block PUCO`);
                };

                $(`#operator_${line}_p`).text(operator); // имя оператора
                $(`#order_${line}_p`).html(order); // номер и описание заказа

                // показания счетчиков, или 0, если линия стоит
                if (status != "STOP" && status != "N-A") {
                    $(`#input_${line}`).html(`<p>INPUT:</p><p><b>${input}</b></p>`);
                    $(`#output_${line}`).html(`<p>OUTPUT:</p><p><b>${output}</b></p>`);

                    /** ключ камера для возвращаемоего словаря есть у всех линий, но только у тех 
                     * линий, которые реально имеют словарь наполняется значениями defrate b last_meas
                    */
                    if (Object.keys(defect_rate).length > 0) {
                        $(`#camera_${line}`).remove();
                        $(`#${line}_container`).append(
                            `<div class="infoboard_block_pair last_block" id="camera_${line}">
                            </div>`
                        );

                        $.each(defect_rate.defrate, function (cam) {

                            var percent = parseFloat(defect_rate.defrate[Number(cam)]).toFixed(2);
                            var minutes_ago = defect_rate.last_meas[Number(cam)];
                            var style_is_red = is_red(percent, 1);


                            $(`#camera_${line}`).append(
                                `<div class="infoboard_block_small" >
                                    <p ${style_is_red}><b>${percent}%</b></p>
                                    <p>${minutes_ago}</p>
                                </div>`)
                        });
                    };

                    // обнулить значения счетчиков и удалить показания камер, если линии остановлены
                } else {
                    $(`#input_${line}`).html(`<p>INPUT:</p><p><b>0</b></p>`);
                    $(`#output_${line}`).html(`<p>OUTPUT:</p><p><b>0</b></p>`);
                    $(`#camera_${line}`).remove()
                };

                // сообщение о времени последнего обновления страницы
                var updated = new Date().toTimeString().slice(0, 8);
                $("#updated").html(`Обновлено в ${updated}`);


            })
        },
        error: { "message": "error" },


    });
};

// функция помечает значения больше указанного количества процентов красным цветом
function is_red(percent, rate) {
    if (percent > rate) {
        return 'style="color:#c05e5e;"';
    } else {
        return "";
    }
};

// функция возвращает текущее время
function get_current_date() {
    var time_now = new Date().toTimeString().slice(0, 8);
    return time_now;
};


function pp_staff_update(graph_id) {
    var form = $("#" + graph_id);
    $.ajax({
        type: 'post',
        url: '#',
        //data: form.serialize(),
        success: function (response) {
            var server_data = jQuery.parseJSON(response);

            // создание графиков
            Plotly.newPlot(graph_id, server_data.data, server_data.layout);
            $("#time_now_p").text(`Обновлено в: ${get_current_date()}`);

        },
        error: function () {
            $("#time_now_p").text(get_current_date() + " Ошибка подключения! Данные не обновлены!")
        }
    });
};
