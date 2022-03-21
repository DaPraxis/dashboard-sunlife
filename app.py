from numpy import isin
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import dash_table as dt
import plotly.express as px
from sklearn.decomposition import PCA
import datetime
import plotly.graph_objs as go
from datetime import datetime, timedelta
import textwrap

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

df = pd.read_csv('./dataset/df_obfc.csv')
mask = df.columns[df.dtypes==object]
df[mask] = df[mask].astype('category')
df_d = df.copy()
df_d[mask]= df_d[mask].apply(lambda x: x.cat.codes)
pca = PCA(n_components=3)
pca_d = pca.fit_transform(df_d)
df["pca_1"] = pca_d[:,0].tolist()
df["pca_2"] = pca_d[:,1].tolist()
df["pca_3"] = pca_d[:,2].tolist()
role_indicators = df['role'].unique()
dff = None

app.layout = html.Div([
    html.Div([
        html.Div([
        html.H4("Employee Role Type"),
            dcc.Dropdown(
                id='role_filter',
                options=[{'label': i, 'value': i} for i in role_indicators],
                value="role_4"
            )
        ],style={
            'padding': '10px 5px'
        }),
        dcc.Graph(
            id='3d-pca',
        ),
        html.H4("PCA filter"),
        dcc.Dropdown(
            id='color_filter',
            options=[{'label': i, 'value': i} for i in df.drop(columns = ["role"]).columns],
            value="country",
            multi=True
        ),
    ],style={'width': '49%', 'display': 'inline-block', 'padding': '0 20', 'height':'49%'}),
    html.Div([
        dcc.Graph(id="ts"),
        dt.DataTable(
            id='table',
            data=df.head().to_dict('records'),
            columns=[{"name": i, "id": i} for i in df.columns],
        )
    ],style={'width': '49%', 'display': 'inline-block', 'float':'right', 'height':'49%'})
])


@app.callback(
    dash.dependencies.Output('ts', 'figure'),
    [dash.dependencies.Input('table', 'data'),]
    )
def update_ts_graph(data):
    entry = pd.DataFrame.from_dict(data)
    entry['time'] = entry['day_of_yr'].astype(str)
    my_string = '2021-01-01'
    my_date = datetime.strptime(my_string, "%Y-%m-%d")
    entry['time'] = entry.apply(lambda x: my_date+timedelta(days=int(x['day_of_yr'])), axis=1)
    # fig = px.line(entry, x="time", y="no_files", markers=True)
    trace1 = go.Scatter(
                    x = entry.time,
                    y = entry.no_files,
                    mode = "lines+markers",
                    name = "number of files",
                    marker = dict(color = 'rgba(16, 112, 2, 0.8)'),
                    text= entry.subject)
    trace2 = go.Scatter(
                    x = entry.time,
                    y = entry.max_filesize,
                    mode = "lines+markers",
                    name = "maximum file size",
                    marker = dict(color = 'rgba(80, 26, 80, 0.8)'),
                    text= entry.subject)
    trace3 = go.Scatter(
                    x = entry.time,
                    y = entry.sum_filesize,
                    mode = "lines+markers",
                    name = "sum file size",
                    marker = dict(color = 'rgba(255, 128, 2, 0.8)'),
                    text= entry.subject)
    data = [trace1, trace2, trace3]
    layout = dict(title = 'Data Tracking of Employee Emails',
                xaxis= dict(title= 'Email Time Line',ticklen= 5,zeroline= False))
    fig = dict(data = data, layout = layout)
    return fig

@app.callback(
    dash.dependencies.Output('3d-pca', 'figure'),
    [dash.dependencies.Input('role_filter', 'value'),
     dash.dependencies.Input('color_filter', 'value')])
def update_3d_graph(role_name, color_f):
    global pca_d
    global dff
    color_name = None
    dff = df[df['role'] == role_name]
    if (isinstance(color_f, str)):
        color_name = color_f
    elif (isinstance(color_f, list)):
        if (len(color_f)==1):
            color_name = color_f[0]
        else:
            color_name = color_f[0]
            for i in range(len(color_f)-1):
                color_name += " x "
                color_name += color_f[i+1]
            dff[color_name] =  dff[color_f[0]]
            for i in range(len(color_f)-1):
                dff[color_name]=dff[color_name].astype(str) + " x "
                dff[color_name]=dff[color_name] + dff[color_f[i+1]].astype(str)
            
    fig = px.scatter_3d(
        dff, x="pca_1", y="pca_2", z="pca_3",color=color_name, 
        # title=f'PCA Total Explained Variance: {total_var:.2f}%',
        title=f'PCA visualization for "{role_name}" email entries',
        labels={'pca_1': 'PC 1', 'pca_2': 'PC 2', 'pca_3': 'PC 3'},
        hover_name = "role", hover_data = {"role":False, "pca_1":False, "pca_2":False, "pca_3":False}
    )
    return fig

@app.callback(
    dash.dependencies.Output('table', 'data'),
    [dash.dependencies.Input('3d-pca', 'hoverData'),]
)
def select_data(data):
    global dff
    if data:
        x = data['points'][0]['x']
        sub = dff[dff['pca_1'] == x]
        name = sub['mail_from'].to_list()[0]
        
    else:
        idd = 0
        name = dff.iloc[idd]['mail_from']
    return dff[dff['mail_from']==name].to_dict('records')


        
if __name__ == '__main__':
    app.run_server(debug=True)