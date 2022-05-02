// функция, добавляющая адаптивность для графиков plotly
function responsive_plot(plot_json, div_id, WIDTH = 32, HEIGHT = 70) {
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
    data = graph_json.data
    layout = graph_json.layout
    config = { 'editable': false, 'displayModeBar': false }
    graph = Plotly.newPlot(div_id, data, layout, config);

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

// функция тмечает все чекбоксы с указанным именем
function toggle_all(source, elem_name) {
    checkboxes = document.getElementsByName(elem_name);
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
                    `<div class="graph_container" id="graph_container_${line}"
                    style="display: flex; margin-top: 25px; flex-direction: row; justify-content: space-between">
                    </div>`
                );

                var plot = plots[line];
                // for each для списка смен
                $.each(plot, function (shift) {
                    var graph_info = jQuery.parseJSON(plot[shift]);
                    // добавление в основной график контейнеров для графиков
                    $(`#graph_container_${line}`).append(
                        `<div class="graph_container" id="graph_container_${line}_${shift}" >
                </div>`);
                    // создание графиков
                    responsive_plot(graph_info, `graph_container_${line}_${shift}`);
                });
            });
            } else {
                $("#main_container").append("<p>Нет данных для отображения</p>")
            };
        },
        error: function () { $("#main_container").append("<p>Ошибка. Нет данных для отображения</p>"); }
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
                var defect_rate = line_info.camera;

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

                // сообщение о времени последнего обновления страницы
                var updated = new Date().toTimeString().slice(0, 8);
                $("#updated").html(`Updated at: ${updated}`);
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
