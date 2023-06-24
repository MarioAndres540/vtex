from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
import pandas as pd
import numpy as np
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from .models import Members,Ordendj
import json

# para Google Drive
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def priorapp(request):
    template = loader.get_template('priorapp.html')
    return HttpResponse(template.render())

def inicio(request):
    global cod_empresa,cod_vitirna
    cod_empresa='1'
    cod_vitirna='1'
    
    file1 = 'Esprit_inventario online + reserva Abril 21_2023.xlsx'
    context = {'archivo':file1}
    return render(request,'priorapp.html',context) 


def cargar(request):
    global cod_empresa,cod_vitirna,variables,orden,spreadsheetid
    #archivo = request.FILES['myfile']
    #print(archivo)

    #parametros

    # Leer archivos

    file2 = request.POST.get('myfile')
    print(file2)
    if file2[-4:]=='.csv':
        inventario = pd.read_csv(file2,sep=";",encoding = 'ISO-8859-1')
        print(inventario.shape)
    elif file2[-5:]=='.xlsx':
        inventario = pd.read_excel(file2)
        print(inventario.shape)
    else:
        print("Error tipo de archivo")
    
    # preparara columns para merges
    
    t0=time.time()
    #Leer datos de GGD
    #Variables
    #spreadsheetid = '1bVx_Mj0BVjKB6RLThoB23V60KBxARv3r_diUIclhdBw' #Producción
    spreadsheetid ='19hZ-iIsS5E8ABcGnCulmVUTtk9oXW7EhzD0KBrm2G4Y' # Test
    rangeid ='Vitrinas!A1:H'
    leeidoggd = lerGGD(spreadsheetid,rangeid)
    vitrinas=pd.DataFrame(leeidoggd[1:],columns=leeidoggd[0])
    #Variables
    rangeid ='Variables!A1:D'
    leeidoggd = lerGGD(spreadsheetid,rangeid)
    variables=pd.DataFrame(leeidoggd[1:],columns=leeidoggd[0])
    #Agrupamientos
    rangeid ='Agrupamiento!A1:F'
    leeidoggd = lerGGD(spreadsheetid,rangeid)
    agrupar=pd.DataFrame(leeidoggd[1:],columns=leeidoggd[0])
    #Orden
    rangeid ='Orden!A1:F'
    leeidoggd = lerGGD(spreadsheetid,rangeid)
    orden=pd.DataFrame(leeidoggd[1:],columns=leeidoggd[0])
    #Prioridades
    rangeid ='Prioridades!A1:F'
    leeidoggd = lerGGD(spreadsheetid,rangeid)
    prioridades=pd.DataFrame(leeidoggd[1:],columns=leeidoggd[0])
    #vitrinas
    #Datos vitrina
    vitr=vitrinas[vitrinas.Ejecutar=='1'] # tómar la primera vitrina
    cod_vitrina=vitr.id_vitrina.values[0]
    file=vitr.Nombre_archivo.values[0] # Archivo a abrir
    set_sup	=int(vitr.Set_sup.values[0])
    set_inf	=int(vitr.Set_inf.values[0])
    set_num	=int(vitr.Min_unidades.values[0])
    observ	=int(vitr.Observaciones.values[0])
    nombre	=vitr.nom_vitrina.values[0]
    #preguntar
    filename=np.datetime64('today').astype(str)+'_'+nombre+ '.xlsx'
    filevtex=np.datetime64('today').astype(str)+'_'+nombre+'_vtex.xls'
    file_descuentos='Observaciones_Dctos.xlsx'
    file_vtex='Esprit_Producto.xlsx'
    #file
    # Leer archivos
    file = 'Esprit_inventario online + reserva Mayo 08_2023.xlsx' ###
    #pren= 'prendas.xlsx
    #file = 'Datos/Inventario Inicial.xlsx'
    inventario = pd.read_excel(file)
    #inventario = pd.read_csv(file,sep=";",encoding = 'ISO-8859-1')
    #prendas=pd.read_excel(pren)
    #inventario.info()
    # Filtrar los deinventario cero y los que no tienen descuento si es vitrina con descuentos

    inventario1=inventario[inventario['Total Inventario']>0].reset_index(drop=True)
    #descuentos = pd.read_excel(file_descuentos)
    # if observ==-1: # Nuevos lanzamientos
    #     #inventario2=inventario3[~(inventario3.Desccuento>0)].reset_index(drop=True)
    #     fecha_ini = np.datetime64('today', 'D')
    #     inventario3 = pd.merge(inventario1,descuentos[['Referencia','Cód Color','Desccuento']],
    #             how="left",
    #             left_on=['Referencia','cod_color'],
    #             right_on=['Referencia','Cód Color'])
    #     inventario2=inventario3[inventario3.Desccuento.isnull()].reset_index(drop=True)

    # else: # Con descuentos
    #     if observ==1:
    #         #print("Descuentos")
    #         #inventario2=inventario3[inventario3.Desccuento>0].reset_index(drop=True)
    #         inventario2 = pd.merge(inventario1,descuentos[['Referencia','Cód Color','Desccuento']],
    #                 how="inner",
    #                 left_on=['Referencia','cod_color'],
    #                 right_on=['Referencia','Cód Color'])
    #         fecha_ini = np.datetime64('today', 'D') + np.timedelta64(-90, 'D')
    #     else:
    #         #Vitrinas Eseciales
    inventario2=inventario1.copy()
    #         fecha_ini = np.datetime64('today', 'D') + np.timedelta64(-90, 'D')


    # preparara columns para merges
    inventario2.rename(columns={'Total Inventario':'Total_Inventario'},inplace=True)
    inventario2['tip_talla']=inventario2.tip_talla.str.replace(' ','',regex=True)
    inventario2['Cod_linea']=inventario2.Referencia.str[0:1]
    inventario2['Cod_coleccion']=inventario2.Referencia.str[2:3]
    inventario2['Cod_prenda']=inventario2.Referencia.str[1:2]
    inventario2['Col']=inventario2.Referencia.str[2:4]
    inventario2['Cod_anno']=inventario2.Referencia.str[3:4]
    inventario2['Cod_origen']=inventario2.Referencia.str[4:5]
    inventario2['Nivel_talla']=np.core.defchararray.add(np.where(inventario2.Cod_prenda.isin(['3','4','5','7']),'Inf','Sup'),'_'+inventario2.tip_talla.replace(r'[^0-9a-zA-Z-/]', '', regex=True))
    prioridadesvit = prioridades[(prioridades.cod_vitrina==cod_vitrina)].reset_index(drop=True)
    ordenvit = orden[(orden.cod_vitrina==cod_vitrina)].reset_index(drop=True).sort_values('Orden')
    #ordenvit.sort_values('Orden',inplace=True)
    #ordenvit

    #Agrupamientos multiples
    #prioridadesemp = prioridades[(prioridades.cod_vitrina==cod_vitrina)].reset_index(drop=True)
    varagr = list(set(ordenvit.cod_var.astype(str).to_list()+['17','16'])) # 
    #varagr = list(ordenvit.cod_var.astype(str))+['17','16']+ordenvit['cod_var'].to_list()
    #agruparvit= agrupar[agrupar.var2.isin(varagr)].reset_index(drop=True)
    agruparvit= agrupar.reset_index(drop=True)
    grupos=agruparvit.groupby(['var1','var2']).val_var1.count()
    tablas_agrupo=[]
    for i in range(len(grupos)):
        cols=[variables[variables.cod_var==grupos.index[i][0]].nom_var.values[0],
          variables[variables.cod_var==grupos.index[i][1]].nom_var.values[0]]
        tabla_agrupo = agrupar[(agrupar.var1 ==grupos.index[i][0]) & (agrupar.var2 ==grupos.index[i][1])].reset_index(drop=True)
        tabla_agrupo.rename(columns={'val_var1':cols[0],'val_var2':cols[1] }, inplace=True)
        tablas_agrupo+=[tabla_agrupo]
        inventario2 = pd.merge(inventario2,tablas_agrupo[i][cols],
                        how="left",
                        left_on=cols[0],
                        right_on=cols[0])
        inventario2[cols[1]]=inventario2[cols[1]].fillna('Otros')# Llenar blancos
        print(i,grupos.index[i][0],grupos.index[i][1],cols,tabla_agrupo.shape,inventario2.shape)
    #inventario2.to_excel('inventario2.xlsx',index=False) 
    # Agrupar por referencia
    col_vit=['Referencia','cod_color','Col','Tipo_de_Prenda','Uso_de_prenda'] #Estructura inicial de la vitrina
    colgru = inventario2.columns[-len(grupos):].to_list() #Columnas diferentes de cada vitrina
    #col_vitt=col_vit+[colm for colm in colgru if colm not in col_vit]
    col_vitt= ['Referencia', 'cod_color', 'Uso_de_prenda']
    # estructura de la vitrina con columnas personalizadas
    # if  observ==1:
    #     col_vitt+=['Rebajas'] # Si es descuentos se agrega rebajas
    vitrina = inventario2.groupby(col_vitt).agg({'tip_talla':'count','Total_Inventario':'sum'}).reset_index()
    vitrina['Perfil'] = np.where(vitrina.Uso_de_prenda=='Superior',np.where(vitrina.tip_talla>=set_sup,'1','0'),np.where(vitrina.tip_talla>=set_inf,'1','0')) # Validar que al menos tenga 3 tallas
    vitrina['Perfil'] = np.where(vitrina.Total_Inventario < set_num,'0',vitrina.Perfil) # filtrar unidades mínimas por referencia

    #Perfil para inventario
    inventario2 = pd.merge(inventario2,vitrina[['Referencia','cod_color','Perfil']],
                    how="left",
                    left_on=['Referencia','cod_color'],
                    right_on=['Referencia','cod_color'])

    # #cols=prioridadesemp.cod_var.unique()
    # colss=ordenvit.cod_var.unique()

    # colp=[c for c in colss if c in prioridadesvit.cod_var.unique()] # que la columna este en prioridades
    # #colp=list(set(list(cols)+list(prioridadesvit.cod_var)))
    # dfpri = [prioridadesvit[prioridadesvit.cod_var== pr].reset_index(drop=True) for pr in colp] # Lista con contenido de las prioridades
    # # dfpri

    # # Traer prioridades del GGD
    # #vitrina2=vitrina[vitrina.Perfil=='1'].reset_index(drop=True) Quitar las que no cumplen el perfil
    # vitrina2=vitrina.copy()
    # nom_cols = [variables[variables.cod_var==c].nom_var.values[0] for c in colp] # traer los nombres
    # for i in range(len(dfpri)):
    #     dfpri[i].rename(columns={'variable':nom_cols[i]}, inplace=True)
    #     vitrina2 = pd.merge(vitrina2,dfpri[i][[nom_cols[i],'prioridad']],
    #                         how="left",
    #                         left_on=nom_cols[i],
    #                         right_on=nom_cols[i])
    #     vitrina2.rename(columns={'prioridad':'pri_'+nom_cols[i]}, inplace=True)


    # # Ordenar para calulo de Jerarquía
    # #columnas=nom_cols+['Total_Inventario']
    # columnas1=['pri_'+ col for col in nom_cols]+['Total_Inventario']
    # ascendente=[True]*len(nom_cols)+[False]
    # vitrina2.sort_values(columnas1,ascending = ascendente, inplace=True)
    # vitrina2.reset_index(drop=True,inplace=True)

    # #Exclir variables con prioridad 99
    # # for limp in columnas1[:-1]:
    # #     vitrina2[limp]=vitrina2[limp].astype(float)
    # #     vitrina2=vitrina2[vitrina2[limp]<99].reset_index(drop=True)
    # #     #print(limp)

    # # Crear column de Jerarquía1
    # prio=vitrina2.loc[0,'Tipo_de_Prenda']
    # rkg=[]
    # i=0
    # for row in vitrina2.iterrows():
    #     if prio != row[1].Tipo_de_Prenda:
    #         i=0
    #         prio= row[1].Tipo_de_Prenda
    #     i+=1
    #     rkg+=[i]
    #     #print(row[1].pri_Perfil,row[1].pri_Col,row[1].pri_Tipo_de_Prenda,row[1].Total_Inventario,i)
    # vitrina2['Ranking']= rkg   
    # # vitrina2
    # nom_cols = [variables[variables.cod_var==c].nom_var.values[0] for c in colp]

    # # Ordenar para calulo de Jerarquía2

    # columnas = ['Uso_de_prenda']+['pri_'+variables[variables.cod_var==c].nom_var.values[0] if 'pri_'+variables[variables.cod_var==c].nom_var.values[0] in vitrina2.columns else variables[variables.cod_var==c].nom_var.values[0] for c in ordenvit.cod_var]
    # #print(columnas)
    # ascendente=[True]+list(ordenvit.sentido=='Ascendente')
    # vitrina2.sort_values(columnas,ascending = ascendente, inplace=True)
    # vitrina2.reset_index(drop=True,inplace=True)
    # tmano_uso=vitrina2.Uso_de_prenda.value_counts() # Para distribuir los de bajo volumen inferiores
    # #print(tmano_uso)

    # # Crear column de Jerarquía
    # prio=vitrina2.loc[0,'Uso_de_prenda']
    # rkg=[]
    # i=0
    # if prio == 'Inferior':
    #     inc = int(max(tmano_uso)/tmano_uso[prio])
    # else:
    #     inc=1
    # for row in vitrina2.iterrows():
    #     if prio != row[1].Uso_de_prenda:
    #         i=0
    #         prio= row[1].Uso_de_prenda
    #         if prio == 'Inferior':
    #             inc = int(max(tmano_uso)/tmano_uso[prio])
    #         else:
    #             inc=1
    #     i+=inc
    #     rkg+=[i]
    #     #print(row[1].pri_Perfil,row[1].pri_Col,row[1].pri_Tipo_de_Prenda,row[1].Total_Inventario,i)
    # vitrina2['Ranking2']= rkg   
    # #vitrina2a=vitrina2.copy()
    # # Definir lineas y columnas
    # vitrina2.sort_values(['Ranking2',columnas[-1]],ascending = [True,False], inplace=True)
    # #vitrina2.sort_values(['Ranking2','pri_Tipo_de_Prenda'],ascending = [True,False], inplace=True)
    # if len(vitrina2)>80:
    #     vitrina2['Linea']=[int(i/4)+1 for i in range(80)]+[int(i/8)+11 for i in range(80,len(vitrina2))]
    #     vitrina2['Columna']=[4-i%4 for i in range(80)] + [i%8+1 for i in range(80,len(vitrina2))] # Columna# Columna
    # else:
    #     vitrina2['Linea']=[int(i/4)+1 for i in range(len(vitrina2))]
    #     vitrina2['Columna']=[4-i%4 for i in range(len(vitrina2))] # Columna

    # vitrina2['fecha'] = [fecha_ini + np.timedelta64(-min(lin,int(lin/2-0.5)+11,26), 'D') for lin in vitrina2.Linea.values]
    # #vitrina2['fecha'] = vitrina2.fecha.dt.date

    # vitrina2.rename(columns={'tip_talla':'# tallas','Total_Inventario':'Stock'},inplace=True)
    # #vitrina2.drop(['pri_Perfil','pri_Tipo_de_Prenda'],axis=1,inplace=True)
    # #vitrina2.to_excel("vitrina2.xlsx",index=False) ####
    # vitrina2.drop(columnas1[:-1]+['Ranking2'],axis=1,inplace=True)
    # vitrina2['Uso_de_prenda'] = vitrina2.Uso_de_prenda.str[:8]

    # # vitrina2['Uso_de_prenda'] = np.where(vitrina2.Uso_de_prenda=='SuperiorC','Superior',vitrina2.Uso_de_prenda)
    # # vitrina2['Uso_de_prenda'] = np.where(vitrina2.Uso_de_prenda=='SuperiorD','Superior',vitrina2.Uso_de_prenda)
    # # vitrina2['Uso_de_prenda'] = np.where(vitrina2.Uso_de_prenda=='InferiorC','Inferior',vitrina2.Uso_de_prenda)
    # # vitrina2['Uso_de_prenda'] = np.where(vitrina2.Uso_de_prenda=='InferiorD','Inferior',vitrina2.Uso_de_prenda)
    # vitrina2.sort_values(['Linea','Columna'],inplace=True)
    # #vitrina2['fecha'] = vitrina2.fecha.dt.strftime('%d/%m/%Y') # Fecha decreciente
    # #vitrina2.to_excel(filename,index=False)
    # col_res=['Linea']+list(vitrina2.columns[:-7]) # columnas para el resumen
    # col_res=[col_res[0],col_res[4],col_res[1],col_res[2],col_res[3]]+col_res[6:]
    # resumen=vitrina2.groupby(col_res).agg({'Referencia':'count','# tallas':'sum','Stock':'sum'})
    # #with pd.ExcelWriter(filename) as writer:
    # #    resumen.to_excel(writer, sheet_name='Resumen')
    # #    vitrina2.to_excel(writer, sheet_name='Vitrina',index=False)
    # vitrina3=vitrina2.Referencia+vitrina2.cod_color
    # vitrina4 = np.append(vitrina3.values,vitrina3.values[-(4-len(vitrina3)%4):]).reshape((-1,4))
    # vitrina_df = pd.DataFrame(vitrina4,columns=(['Col_1','col_2','col_3','col_4']))
    inventario2['Uso_de_prenda'] = inventario2.Uso_de_prenda.str[:8]  

    #cols=prioridadesemp.cod_var.unique()
    cols=ordenvit.cod_var.unique()
    #colp=cols
    colp=[c for c in cols if c in prioridadesvit.cod_var.unique()] # que la columna este en prioridades
    #colp=list(set(list(cols)+list(prioridadesvit.cod_var)))
    # dfpri

    colores = ['green','orchid','cyan','yellow','orange','purple','brown', 'olive', 'tan', 'lime','coral','blue','black','white','red','pink','magenta', 'gray']
#     Ordendj.objects.all().delete()
#     ordend = ordenemp[['cod_var','orden','nom_var','sentido']].sort_values('orden').to_dict('records')
#     for orde in ordend:
#         ored = Ordendj(ordenv=orde['orden'], nom_var=orde['nom_var'],sentido=orde['sentido'])
#         ored.save()
    
#     #Prioridades
#     rangeid ='Prioridades!A1:F'
#     leeidoggd = lerGGD(spreadsheetid,rangeid)
#     prioridades=pd.DataFrame(leeidoggd[1:],columns=leeidoggd[0])

#     #Agrupamientos multiples
#     agruparemp=agrupar[(agrupar.cod_empresa==cod_empresa) & (agrupar.cod_vitirna==cod_vitirna)].reset_index(drop=True)
#     grupos=agruparemp.groupby(['var1','var2']).val_var1.count()
#     tablas_agrupo=[]
#     for i in range(len(grupos)):
#         cols=[variables[variables.cod_var==grupos.index[i][0]].nom_var.values[0],
#           variables[variables.cod_var==grupos.index[i][1]].nom_var.values[0]]
#         tabla_agrupo = agruparemp[(agruparemp.var1 ==grupos.index[i][0]) & (agruparemp.var2 ==grupos.index[i][1])].reset_index(drop=True)
#         tabla_agrupo.rename(columns={'val_var1':cols[0],'val_var2':cols[1] }, inplace=True)
#         tablas_agrupo+=[tabla_agrupo]
#         inventario2 = pd.merge(inventario2,tablas_agrupo[i][cols],
#                         how="left",
#                         left_on=cols[0],
#                         right_on=cols[0])
#         print(i,grupos.index[i][0],grupos.index[i][1],cols,tabla_agrupo.shape,inventario2.shape)

    columnas = list(inventario2.columns)

    #Lista de tallas
    tallas=inventario2[['Uso_de_prenda','tip_talla']].value_counts()


    resumen_inv = inventario2.groupby(['Uso_de_prenda','Tipo_de_Prenda']).agg({'Referencia':'count','Total_Inventario':'sum'})
    resumen_inv.rename(columns={'Referencia':'Referencias'}, inplace=True) 
    resumen_inv.sort_values('Total_Inventario',ascending=False,inplace=True)
    plt.clf()
    fig = tallas.sort_values(ascending=True).plot(kind='barh',figsize=(11, 7),title='Cantidades por talla').get_figure()
    plt.tight_layout()
    #Pasara a Django
    buffer = BytesIO()
    plt.savefig(buffer, format='png',bbox_inches="tight")
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    graphic1 = base64.b64encode(image_png)
    graphic1 = graphic1.decode('utf-8')

    plt.clf()
    #Figura general
    resumen_inv.sort_values('Total_Inventario',ascending=True,inplace=True)
    fig2=resumen_inv.plot(kind='barh',figsize=(10, 4),title='Resumen por tipo de prenda').get_figure()
    plt.tight_layout()
    #Pasara a Django
    buffer = BytesIO()
    plt.savefig(buffer, format='png',bbox_inches="tight")
    buffer.seek(0)
    image_png2 = buffer.getvalue()
    buffer.close()
    graphic2 = base64.b64encode(image_png2)
    graphic2 = graphic2.decode('utf-8')
    #fig.savefig('test.png')

    # Grafica por uso y tipo de prenda
    resumen_inv.sort_values('Total_Inventario',ascending=False,inplace=True)
    textoeje=(resumen_inv.index.get_level_values(0)+','+resumen_inv.index.get_level_values(1)).values
    #print('clients.',col)
    #calid = clients[col].value_counts().head(15)
    #print(calid)
    #fig, ax = plt.subplots()
    plt.clf()
    fig = plt.figure(figsize=(10, 4))
    grid = plt.GridSpec(1, 3, wspace=2, hspace=0.3)
    ax = plt.subplot(grid[0,0])
    bars = ax.barh(textoeje,resumen_inv.Total_Inventario.values,color = 'green')
    ax.invert_yaxis()
    # To get data labels
    for y1,bar in enumerate(bars):
        width = bar.get_width()
        label_y = y1
        plt.text(width, label_y, s=f'{width}')
    plt.title('Cantidad de prendas')
    plt.ylabel('Uso de prenda, tipo de prenda')
    plt.xlabel('Total_inventario')

    ax = plt.subplot(grid[0,1])
    bars = ax.barh(textoeje,resumen_inv.Referencias.values,color = 'blue')
    ax.invert_yaxis()
    # To get data labels
    for y1,bar in enumerate(bars):
        width = bar.get_width()
        label_y = y1
        plt.text(width, label_y, s=f'{width}')
    plt.title('Cantidad de referencias')
    plt.xlabel('Total_referencias')

    ax = plt.subplot(grid[0,2])
    bars = ax.barh(textoeje,np.round(resumen_inv.Total_Inventario.values/resumen_inv.Referencias.values,2),color = 'orange')
    ax.invert_yaxis()
    # To get data labels
    for y1,bar in enumerate(bars):
        width = bar.get_width()
        label_y = y1
        plt.text(width, label_y, s=f'{width}')
    plt.title('Resumen por indice')
    plt.xlabel('Prendes / referencias')

    #Pasara a Django
    buffer = BytesIO()
    plt.savefig(buffer, format='png',bbox_inches="tight")
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')

    #Destallados
    prendas=inventario2.groupby(['Perfil']).agg({'Total_Inventario':'sum'}).sort_values(['Total_Inventario'],ascending=True)
    prendas=prendas.sort_values(['Total_Inventario'],ascending=False)
    y = ['']
    leftt=0
    largo=len(prendas)
    colors = ['orange','green']
    plt.figure(figsize=(15,4))
    for pr in range(largo):
        plt.barh(y, prendas.iloc[pr]['Total_Inventario'],left=leftt, height=0.5, color=colors[pr])
        leftt+=prendas.iloc[pr]['Total_Inventario']
    plt.title('Cantidades por Perfil')
    plt.xlabel('unidades')
    #plt.legend(labels=list(prendas.index))
    plt.legend(labels=['Destallados','Perfil completo'])
    buffer = BytesIO()
    plt.savefig(buffer, format='png',bbox_inches="tight")
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    graphic3 = base64.b64encode(image_png)
    graphic3 = graphic3.decode('utf-8')
    
    prendas=inventario2.groupby(['Tipo_de_Prenda','Perfil']).agg({'Total_Inventario':'sum'}).sort_values(['Total_Inventario'],ascending=True)
    destallados = prendas.unstack()
    plt.figure(figsize=(15,4))
    for des in destallados.iterrows():
        leftt=0
        plt.barh(des[0], des[1][0],left=leftt, height=0.8, color='orange')
        leftt+=des[1][0]
        plt.barh(des[0], des[1][1],left=leftt, height=0.8, color='green')
    plt.title('Cantidades por Perfil')
    plt.xlabel('unidades')
    plt.legend(labels=['Destallados','Perfil completo'])
    buffer = BytesIO()
    plt.savefig(buffer, format='png',bbox_inches="tight")
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    graphic4 = base64.b64encode(image_png)
    graphic4 = graphic4.decode('utf-8')
    
    
    
    context = { 'largo':len(inventario2),'columnas': columnas,'graphic':graphic,'graphic1':graphic1,'graphic2':graphic2,'graphic3':graphic3,'graphic4':graphic4 }
    return render(request,'analisis.html',context) 



def priorizar(request):
    global cod_empresa,cod_vitirna,variables,orden
    #Orden
    mymembers = Members.objects.all().values()
    myordendj = Ordendj.objects.all().order_by('ordenv').values()
    variablesd = variables.sort_values('nom_var').to_dict('records')
    largo = len(myordendj)
    context = {'mymembers': mymembers,'largo':largo,'myordendj':myordendj,'variablesd':variablesd}
    return render(request,'priorizar.html',context) 


def add(request):
    template = loader.get_template('add.html')
    return HttpResponse(template.render({}, request))

def addrecord(request):
    x = request.POST['first']
    y = request.POST['last']
    member = Members(firstname=x, lastname=y)
    member.save()
    return HttpResponseRedirect(reverse('priorizar'))
def delete(request, id):
    member = Members.objects.get(id=id)
    member.delete()
    return HttpResponseRedirect(reverse('priorizar'))

def update(request, id):
    mymember = Members.objects.get(id=id)
    template = loader.get_template('update.html')
    context = {
        'mymember': mymember,
    }
    return HttpResponse(template.render(context, request))

def updaterecord(request, id):
    first = request.POST['first']
    last = request.POST['last']
    member = Members.objects.get(id=id)
    member.firstname = first
    member.lastname = last
    member.save()
    return HttpResponseRedirect(reverse('priorizar'))

def deleteord(request, id):
    ordd = Ordendj.objects.get(id=id)
    ordd.delete()
    for i,ordd in enumerate(Ordendj.objects.all()):
        ordd.ordenv=i+1
        ordd.save()
    return HttpResponseRedirect(reverse('priorizar'))

def sentido(request, id):
    ordd = Ordendj.objects.get(id=id)
    if ordd.sentido == 'Ascendente':
        ordd.sentido='Descendente'
    else:
        ordd.sentido='Ascendente'
    ordd.save()
    return HttpResponseRedirect(reverse('priorizar'))
  
def nomvar(request, id1,id2):
    ordd = Ordendj.objects.get(id=id1)
    
    selop = request.POST.get('selnomvar')
    print('holaid.',id1,id2,selop)
    return HttpResponseRedirect(reverse('priorizar'))

def verop(request):
    selop = request.POST.get('drop1')
    if selop is None:
        selop=''
    box = request.POST.get('drop3')
    print('drop1.',selop,selop+"3",box)
    return HttpResponseRedirect(reverse('inicio'))
   
def verou(request,id1):
     
    box = request.POST.get('box3')
    print('box.',id1,box)
    return HttpResponseRedirect(reverse('inicio'))

def veroq(request):
    box = request.POST.get('drop4')
    id1,nomvar=box[:box.find('-')],box[box.find('-')+1:]
    ordd = Ordendj.objects.get(id=id1)
    ordd.nom_var=nomvar
    ordd.save()
    print('Cambio:',id1,nomvar)
    return HttpResponseRedirect(reverse('priorizar'))


def verop2(request):
    #selop = request.POST.get('drop1')
    #if selop is None:
    #  selop=''
    box = request.POST.get('dropnom')
    print('dropnom:',box)
    return HttpResponseRedirect(reverse('priorizar'))


def addord(request):
    nn=len(Ordendj.objects.all().values())
    ordd = Ordendj(ordenv=nn+1, sentido='Ascendente')
    ordd.save()
    return HttpResponseRedirect(reverse('priorizar'))

def ordup(request, id):
    ordd = Ordendj.objects.get(id=id)
    nn = int(ordd.ordenv)
    if nn > 1:
        ordu = Ordendj.objects.filter(ordenv=str(nn-1))[0]
        ordu.ordenv = str(nn)
        ordd.ordenv = str(nn-1)
        ordd.save()
        ordu.save()
    return HttpResponseRedirect(reverse('priorizar'))
  
def orddn(request, id):
    ordd = Ordendj.objects.get(id=id)
    nn = int(ordd.ordenv)
    ordn = Ordendj.objects.filter(ordenv=str(nn+1)).values()
    if len(ordn)>0:
        ordn = Ordendj.objects.filter(ordenv=str(nn+1))[0]
        ordn.ordenv = str(nn)
        ordd.ordenv = str(nn+1)
        ordd.save()
        ordn.save()
    return HttpResponseRedirect(reverse('priorizar'))

def genvit(request):
    global cod_empresa,cod_vitirna,variables,orden,spreadsheetid
    nn=len(Ordendj.objects.all().values())
    rangeid = rangeid ='Orden!A2:F'
    metodo = "insert"
    datosini = orden[~((orden.cod_empresa==cod_empresa) & (orden.cod_vitirna==cod_vitirna))].reset_index(drop=True)
    datos0 = pd.DataFrame(Ordendj.objects.all().values())
    datos = pd.merge(datos0,variables[['nom_var','cod_var']],
                        how="left",
                        left_on='nom_var',
                        right_on='nom_var')
    datos['cod_empresa']=cod_empresa
    datos['cod_vitirna']=cod_vitirna
    datos.rename(columns={'ordenv':'orden'},inplace=True)
    datos=datos[orden.columns].sort_values('orden').reset_index(drop=True)
    nn=max(0,len(orden)-len(datosini)-len(datos))
    datosend = pd.DataFrame( [['','','','','','']]*nn,columns=orden.columns )
    datos1=pd.concat([datosini,datos,datosend],axis=0).reset_index(drop=True)
    res= escribeggd(spreadsheetid,datos1,rangeid,metodo)
    return HttpResponseRedirect(reverse('priorizar'))


  
# Leer una parte (rango) de na Google Sheet
def lerGGD(spreadsheetid,rangeid):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('sheets', 'v4', credentials=creds)

        # Call the Sheets API
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheetid,
                                    range=rangeid).execute()
        values = result.get('values', [])
    except HttpError as err:
        print(err)
    return values

# Escribir una parte (rango) de na Google Sheet
def escribeggd(spreadsheetid,datos,rangeid,metodo):
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    resource ={
            "values": json.loads(datos.to_json(orient='values', date_format='iso'))
        }
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('sheets', 'v4', credentials=creds)
    # Call the Sheets API
    sheet = service.spreadsheets()
    if metodo == "append":
        respuesta = service.spreadsheets().values().append(
            spreadsheetId=spreadsheetid,
            valueInputOption='RAW',
            range=rangeid,
            body=resource
        ).execute()
    else:
        respuesta = service.spreadsheets().values().update(
            spreadsheetId=spreadsheetid,
            valueInputOption='RAW',
            range=rangeid,
            body=resource
        ).execute()
    return respuesta    


