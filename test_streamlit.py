import streamlit as st
import requests
import pandas as pd
from io import BytesIO
import datetime
import ssl
from bs4 import BeautifulSoup
import urllib.request, urllib.parse, urllib.error, os

color_gap_up = 'rgb(105,190,40)'
color_gap_down = 'rgb(255, 0, 0)'
icon_up = '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-caret-up-fill" viewBox="0 0 16 16">
            <path d="m7.247 4.86-4.796 5.481c-.566.647-.106 1.659.753 1.659h9.592a1 1 0 0 0 .753-1.659l-4.796-5.48a1 1 0 0 0-1.506 0z"/>
            </svg>'''
icon_down = '''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-caret-down-fill" viewBox="0 0 16 16">
          <path d="M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z"/>
          </svg>'''
def metrica_360(text_size = '18px', color_text = "#00264e",
                  text = '', text_size_val = '2.25rem', color_val = "#00264e", 
                  value='', color_delta1='', delta1='', color_delta2='', delta2=''):
    metrica = '''
    <style>
    .custom-metric {
        font-size: %s;
        font-family: "Source Sans Pro", sans-serif;
        /*font-weight: 400;*/
        text-align: center;
        color: %s;
        padding: 10px 10px 10px 10px;
        /*border: 1px solid rgba(0, 32, 78, 0.2);*/
        border-radius: 5px;
        /*border-left: 0.5rem solid #00204e !important;*/
        /*box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important;*/
    }
    </style>
    <div class="custom-metric">
        <div>%s</div>
        <div style="font-size: %s; color:%s">%s</div>
        <div style="color: %s; font-size: 20px;">%s</div>
        <div style="color: %s; font-size: 20px">%s</div>
    </div>
    ''' % (text_size, color_text, text, text_size_val, color_val, value, color_delta1, delta1, color_delta2, delta2)
    st.markdown(metrica, unsafe_allow_html=True)

excel_url = "https://www.bcv.org.ve/sites/default/files/EstadisticasGeneral/1_1_4.xls"

# Obtener el contenido del archivo
response = requests.get(excel_url, verify=False)

xls = pd.ExcelFile(BytesIO(response.content))

sheets = xls.sheet_names
df = pd.read_excel(xls, sheet_name=sheets[0])

# day = datetime.datetime.now().date()
# yesterday = day - datetime.timedelta(1)
# last_month = day - datetime.timedelta(day.day)
resultados = {'reserva_hoy':0,'reserva_ayer':0,'reserva_mes':0,'daily_var':0,'month_var':0}
data = {'fecha':[], 'monto':[]}
for i in range(len(df)):
  try:
    row=df.iloc[i,0].date()
    data['fecha'].append(row)
    data['monto'].append(df.iloc[i,1])
  except:
    continue
data = pd.DataFrame(data)
resultados['reserva_hoy'] = data.iloc[0:1,].monto.iloc[0]
fecha_hoy = data.iloc[0:1,].fecha.iloc[0].strftime('%d-%m-%Y')
resultados['reserva_ayer'] = data.iloc[1:2,].monto.iloc[0]
fecha_ayer = data.iloc[1:2,].fecha.iloc[0].strftime('%d-%m-%Y')
resultados['reserva_mes'] = data.loc[data.fecha.map(lambda x: x.month == data.fecha.max().month - 1)].iloc[0:1,].monto.iloc[0]
fecha_mes = data.loc[data.fecha.map(lambda x: x.month == data.fecha.max().month - 1)].iloc[0:1,].fecha.iloc[0].strftime('%d-%m-%Y')

if resultados['reserva_ayer'] > 0:
  resultados['daily_var'] = (resultados['reserva_hoy']-resultados['reserva_ayer'])/resultados['reserva_ayer']
  resultados['daily_var'] *= 100
if resultados['reserva_mes'] > 0:
  resultados['month_var'] = (resultados['reserva_hoy']-resultados['reserva_mes'])/resultados['reserva_mes']
  resultados['month_var'] *= 100
resultados['abs_var'] = resultados['reserva_hoy']-resultados['reserva_ayer']

resultados_str = {k: ','.join([n.replace(',','.') for n in f"{round(v,2):,}".split('.')]) for k,v in resultados.items()}

# estadisticas IDI
url = 'https://www.bcv.org.ve/estadisticas/indice-de-inversion'
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
html = urllib.request.urlopen(url, context=ctx, timeout=10).read()
soup = BeautifulSoup(html, 'html.parser')
# fechas
fechas = soup.find_all(class_='date-display-single')
fechas = [f.get('content')[:10] for f in fechas]
# tasa de cambio
tasa_cambio = soup.find_all(class_='views-field views-field-views-conditional')
tasa_cambio = [tc.get_text().strip() for tc in tasa_cambio]
tasa_cambio = [tc.split(',')[0]+','+tc.split(',')[1][:2] for tc in tasa_cambio if (len(tc.split(',')) == 2) and (tc.split(',')[0].isdigit() and tc.split(',')[1].isdigit())]
# idi
idi = soup.find_all(class_='views-field views-field-nothing')
idi = [i.get_text().strip() for i in idi]
idi = [i.split(',')[0]+','+i.split(',')[1][:4] for i in idi if (len(i.split(',')) == 2) and (i.split(',')[0].isdigit() and i.split(',')[1].isdigit())]
# minimo numero de filas
rows = min([len(fechas),len(tasa_cambio), len(idi)])
data = pd.DataFrame({'fecha':fechas[:rows], 'tc': tasa_cambio[:rows], 'idi': idi[:rows]})
data['fecha2'] = data.fecha.map(lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').date())
data['tc_num'] = data.tc.map(lambda x: float(x.replace(',','.')))
data['idi_num'] = data.idi.map(lambda x: float(x.replace(',','.')))
# dia actual
fecha_tc_hoy = data.fecha.iloc[0]
tc_hoy = data.tc.iloc[0]
tc_hoy_num = data.tc_num.iloc[0]
idi_hoy = data.idi.iloc[0]
idi_hoy_num = data.idi_num.iloc[0]
# dia t-1
fecha_tc_ayer = data.fecha.iloc[1]
tc_ayer = data.tc.iloc[1]
tc_ayer_num = data.tc_num.iloc[1]
idi_ayer = data.idi.iloc[1]
idi_ayer_num = data.idi_num.iloc[1]
# mes anterior
df = data.loc[data.fecha2.map(lambda x: x.month == data.fecha2.max().month - 1)].iloc[0:1,]
fecha_tc_mes = df.fecha.iloc[0]
tc_mes = df.tc.iloc[0]
tc_mes_num = df.tc_num.iloc[0]
idi_mes = df.idi.iloc[0]
idi_mes_num = df.idi_num.iloc[0]
# variaciones tasa cambio
if tc_ayer_num > 0:
  var_tc_dia = (tc_hoy_num-tc_ayer_num)/tc_ayer_num
  var_tc_dia *= 100
  var_tc_dia_str = f'{round(var_tc_dia,2):,}%'.replace('.',',')
else:
  var_tc_dia = 0
  var_tc_dia_str = '-'

if tc_mes_num > 0:
  var_tc_mes = (tc_hoy_num-tc_mes_num)/tc_mes_num
  var_tc_mes *= 100
  var_tc_mes_str = f'{round(var_tc_mes,2):,}%'.replace('.',',')
else:
  var_tc_mes = 0
  var_tc_mes_str = '-'
var_abs_tc_dia = tc_hoy_num - tc_ayer_num
var_abs_tc_dia_str = f'{round(var_abs_tc_dia,2):,}'.replace('.',',')
# variaciones tasa idi
if idi_ayer_num > 0:
  var_idi_dia = (idi_hoy_num-idi_ayer_num)/idi_ayer_num
  var_idi_dia *= 100
  var_idi_mes_str = f'{round(var_idi_dia,2):,}%'.replace('.',',')
else:
  var_idi_dia = 0
  var_idi_dia_str = '-'

if idi_mes_num > 0:
  var_idi_mes = (idi_hoy_num-idi_mes_num)/idi_mes_num
  var_idi_mes *= 100
  var_idi_mes_str = f'{round(var_idi_mes,2):,}%'.replace('.',',')
else:
  var_idi_mes = 0
  var_idi_mes_str = '-'
var_abs_idi_dia = idi_hoy_num - idi_ayer_num
var_abs_idi_dia_str = f'{round(var_abs_idi_dia,2):,}'.replace('.',',')

with st.container(border=True):
  st.subheader('Reservas Bancarias Excedentarias')
  c1, c2 = st.columns([.5,.5], vertical_alignment='top')
  with c1:
    metrica_360(text_size = '16px', text = fecha_hoy, value='Bs '+resultados_str['reserva_hoy'], text_size_val = '22px')
    metrica_360(text_size = '16px', text = fecha_ayer, value='Bs '+resultados_str['reserva_ayer'], text_size_val = '22px')
    metrica_360(text_size = '16px', text = fecha_mes, value='Bs '+resultados_str['reserva_mes'], text_size_val = '22px')
  with c2:
    color_val_diario = color_gap_up
    color_val_mes = color_gap_up
    icon_val_diario = icon_up
    icon_val_mes = icon_up
    if resultados['abs_var'] < 0:
      color_val_diario = color_gap_down
      color_val_mes = color_gap_down
      icon_val_diario = icon_down
      icon_val_mes = icon_down
    metrica_360(text_size = '16px', text = 'Var. Absoluta Diaria',text_size_val = '22px',
                value=icon_val_diario+' '+resultados_str['abs_var'], color_val = color_val_diario)
    metrica_360(text_size = '16px', text = '% Variación Diaria',text_size_val = '22px',
                value=icon_val_diario+' '+resultados_str['daily_var']+'%', color_val =  color_val_diario)
    metrica_360(text_size = '16px', text = '% Variación Mensual',text_size_val = '22px',
                value=icon_val_mes+' '+resultados_str['month_var']+'%', color_val = color_val_mes)

  
  

  









