from flask import Flask, render_template, request
import pandas as pd
import json
import plotly
import plotly.express as px
import requests
from io import StringIO
import numpy as np
app = Flask(__name__)


@app.route('/landing_page')
def set_data():
    return render_template('input.html')
#設立起始頁面，用input.html渲染起始頁面

@app.route('/up_load_info', methods = ['GET', 'POST'])
def up_load():
    if request.method == 'POST':
        #接收來自前端的資料
        read_build = str(request.values['read_build'])
        list_name = str(request.values['list_name'])
        datestr = str(request.values['date'])
        r = requests.post('https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=' + datestr + '&type=ALL')
        df = pd.read_csv(StringIO(r.text.replace("=", "")),
            header=["證券代號" in l for l in r.text.split("\n")].index(True)-1).drop(['Unnamed: 16'],axis=1)
        #requests取得當天盤後的資料
        #匯入dataframe之後做整理

        if read_build == 'read_exist_list':
            #網頁上可以選取讀取已經有的txt檔
          with open(list_name,'r') as fp:
            mapping = json.load(fp)
        elif read_build == 'build_new_list':
            #或者建立一個新的txt檔
          datestr = str(request.values['date'])
          category_1 = str(request.values['category_1'])
          stocklist_1 = str(request.values['stocklist_1'])
          category_2 = str(request.values['category_2'])
          stocklist_2 = str(request.values['stocklist_2'])
          category_3 = str(request.values['category_3'])
          stocklist_3 = str(request.values['stocklist_3'])
          with open(list_name, 'w') as fp:
            categories=[]
            stocklists=[]
            categories.append(category_1)
            stocklists.append(stocklist_1)
            categories.append(category_2)
            stocklists.append(stocklist_2)
            categories.append(category_3)
            stocklists.append(stocklist_3)

            mapping={}

            for j in range(len(categories)):
                for i in range(len(categories[j].split(','))):
                    mapping[categories[j].split(',')[i]] = [stocklists[j].split(';')[i]]
                    #用mapping這個dict來儲存key(類股名稱):觀察list

            json.dump(mapping,fp)
            #以json的方式儲存觀察名單
        fig=run_fig(mapping,df)
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        #將run_fig得到的圖片資訊以json的方式傳導至前端網頁
        return render_template('fin.html', graphJSON=graphJSON)

    return render_template('input.html')

def run_fig(mapping,df):
    sum_list=[]
    for i in mapping.keys():
        sum_list=sum_list+mapping[i][0].split(',')
    sum_str_list = map(str,sum_list)
    sum_str_list = list(sum_str_list)
    observe_df=df[df.證券代號.isin(sum_str_list)]
    observe_df=observe_df.reset_index(drop=True)
    observe_df['類股']='預設' #創建類股的欄位
    #將觀察list裡面的數字逐一轉為字串，以利辨識(因為TWSE進來的證券代號是字串)
    #sum_str_list是全部加總的觀察list，用來比對抓取全部台股的資訊
    for i in mapping.keys():
        map_str_list = map(str,mapping[i][0].split(','))
        map_str_list = list(map_str_list)
        #將觀察list裡面的數字逐一轉為字串，以利辨識(因為TWSE進來的證券代號是字串)
        #map_str_list是整理後觀察list
        for j in observe_df.index:
            if observe_df.iloc[j]['證券代號'] in map_str_list:
                observe_df['類股'][j]=i
            else:
                pass
    observe_df = observe_df.replace(',','', regex=True)
    observe_df['價差']='0'
    for i in observe_df.index:
        if observe_df['漲跌(+/-)'][i] == '-' or observe_df['漲跌(+/-)'][i] =='+':
            observe_df['價差'][i]=observe_df['漲跌(+/-)'][i]+ str(observe_df['漲跌價差'][i])
    observe_df['台股']='台股'
    observe_df['漲跌價差%']=round((observe_df['價差'].astype(float)/observe_df['收盤價'].astype(float))*100,2)

    fig = px.treemap(observe_df, path=['台股','類股','證券名稱'],values='收盤價',
                                      color='漲跌價差%',hover_data=['成交股數'],
                                      color_continuous_scale='Tealrose',
                                      color_continuous_midpoint=0)
    return fig



if __name__ == '__main__':
   app.run(debug = True)
