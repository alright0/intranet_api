import plotly.express as px
import plotly
import json


def get_fig():
    fig = px.scatter(x=[0, 1, 2, 3, 4], y=[0, 1, 4, 9, 16])
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON


# print(get_fig())
# fig.show()
