function responsive_plot(plot_json, div_id, WIDTH = 99, HEIGHT = 50) {
    var d3 = Plotly.d3;

    /* ширина и высота в процентах*/
    /*var WIDTH = WIDTH,
        HEIGHT = HEIGHT;*/

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
        /*window.onresize = function (event) {*/
        gd3.style({
            width: WIDTH + '%',
            height: HEIGHT + 'vh',
        });
        gd = gd3.node()
        Plotly.Plots.resize(gd);;
    });
};