import numpy as np
import pandas as pd
import geopandas as gpd
import folium
import panel as pn

from utils import getValues, DATASETS_DIRECTORY_PATH

#%% Data import

static = pd.read_csv(f'{DATASETS_DIRECTORY_PATH}static.csv', parse_dates=['timestamp'], low_memory=False)

dynamic = pd.read_csv(f'{DATASETS_DIRECTORY_PATH}dynamic.csv', parse_dates=['timestamp'])
dynamic['geometry'] = gpd.GeoSeries.from_wkt(dynamic['geometry'], crs='EPSG:4326')
dynamic = gpd.GeoDataFrame(dynamic)

gaps = pd.read_csv(f'{DATASETS_DIRECTORY_PATH}gaps.csv', parse_dates=['disappeartime', 'reappeartime'])
gaps['geometry'] = gpd.GeoSeries.from_wkt(gaps['geometry'], crs='EPSG:4326')
gaps = gpd.GeoDataFrame(gaps, geometry=gaps.geometry, crs='EPSG:4326')
gaps['disappearlocation'] = gpd.GeoSeries.from_wkt(gaps['disappearlocation'], crs='EPSG:4326')
gaps['reappearlocation'] = gpd.GeoSeries.from_wkt(gaps['reappearlocation'], crs='EPSG:4326')

edges = pd.read_csv(f'{DATASETS_DIRECTORY_PATH}edges.csv')
edges['geometry'] = gpd.GeoSeries.from_wkt(edges['geometry'], crs='EPSG:4326')
edges = gpd.GeoDataFrame(edges, geometry=edges.geometry, crs='EPSG:4326')

#%% Panel code

idSelector = pn.widgets.IntInput(name='Gap ID', value=0, step=1, start=0, end=len(gaps)-1)
previousSlider = pn.widgets.EditableIntSlider(name='Previous Positions', fixed_start=0, fixed_end=1000, value=200)
nextSlider = pn.widgets.EditableIntSlider(name='Next Positions', fixed_start=0, fixed_end=1000, value=200)

disappearIcon = folium.features.CustomIcon(icon_image='Markers/x.png', icon_size=(40,40), icon_anchor=(20,20))
reappearIcon = folium.features.CustomIcon(icon_image='Markers/v.png', icon_size=(40,40), icon_anchor=(20,20))

def plot(data):
    mapFeatures = []
    
    lineKwargs = {'color': 'black', 'opacity': 0.3, 'weight': 3}
    def normalLine(line):
        return folium.PolyLine([(point.y, point.x) for point in line], **lineKwargs)
    def gapLine(line):
        return folium.PolyLine([(point.y, point.x) for point in line], dash_array='8', **lineKwargs)
    def normalMarker(report):
        return folium.CircleMarker(location=(report.geometry.y, report.geometry.x), radius=2, stroke=False,
                                   fill_color='black', fill_opacity=1.0)
    popup = lambda report: report.timestamp.strftime('%d/%m/%Y\n%H:%M:%S')
    markerKwargs = lambda report: {'location': (report.geometry.y, report.geometry.x), 'popup': popup(report)}
    def disappearMarker(report): 
        return folium.Marker(icon=disappearIcon, **markerKwargs(report))
    def reappearMarker(report):
        return folium.Marker(icon=reappearIcon, **markerKwargs(report))
    
    currentLine = []
    for report in data['dynamic'].itertuples(index=False):
        if report.edge == 'none':
            currentLine.append(report.geometry)
            mapFeatures.append(normalMarker(report))
        elif report.edge == 'disappear':
            currentLine.append(report.geometry)
            mapFeatures.append(normalLine(currentLine))
            currentLine = []
            currentLine.append(report.geometry)
            if report.timestamp == data['gap'].disappeartime:
                mapFeatures.append(disappearMarker(report))
            else:
                mapFeatures.append(normalMarker(report))
        elif report.edge == 'lone':
            currentLine.append(report.geometry)
            if report.timestamp == data['gap'].disappeartime:
                mapFeatures.append(disappearMarker(report))
            elif report.timestamp == data['gap'].reappeartime:
                mapFeatures.append(reappearMarker(report))
            else:
                mapFeatures.append(normalMarker(report))
        else:
            currentLine.append(report.geometry)
            mapFeatures.append(gapLine(currentLine))
            currentLine = []
            currentLine.append(report.geometry)
            mapFeatures.append(normalMarker(report))
            if report.timestamp == data['gap'].reappeartime:
                mapFeatures.append(reappearMarker(report))
            else:
                mapFeatures.append(normalMarker(report))
    if data['dynamic'].iloc[-1].edge in ['none', 'disappear']:
        mapFeatures.append(normalLine(currentLine))
    else:
        mapFeatures.append(gapLine(currentLine))
    
    return mapFeatures

def visualise(gap_id, previousSlider, nextSlider):
    #NB: both "previousSlider" and "nextSlider" values are unused but trigger map updates
    data = iData()
    m = folium.Map(tiles="cartodb positron", height='100%', 
                   location=(48, -5), zoom_start=7, control_scale=True, prefer_canvas=True)
    for mapFeature in plot(data):
        mapFeature.add_to(m)
    return m
iMap = pn.bind(visualise, idSelector, previousSlider, nextSlider)

def getData(gap_id, previousReports, nextReports):
    data = {}
    previousReports += 1
    nextReports += 1
    data['mmsi'] = gaps.loc[gap_id].mmsi
    data['gap'] = gaps.loc[gap_id]
    data['static'] = static.loc[static.sourcemmsi == data['mmsi']]
    reports = dynamic.loc[dynamic.sourcemmsi == data['mmsi']]
    prev = reports.loc[reports.timestamp <= data['gap'].disappeartime].iloc[-previousReports:]
    nex = reports.loc[reports.timestamp >= data['gap'].reappeartime].iloc[:nextReports]
    data['dynamic'] = pd.concat([prev, nex])
    return data
iData = pn.bind(getData, idSelector, previousSlider, nextSlider)

def getInfos(gap_id):
    
    def toMarkdown(infos):
        md = ''
        for info in infos:
            md += f'**{info}:** {infos[info]}\n\n'
        return md.rstrip('\n')
    
    data = iData()
    infos = {}
    infos['Vessel Name'] = list(getValues(data['static'].shipname).keys())[0]
    infos['MMSI'] = data['mmsi']
    md = '---\n' + toMarkdown(infos)
    
    def getDest():
        staticReport = data['static'].loc[data['static'].timestamp <= data['gap'].disappeartime].iloc[-1]
        dest = staticReport.destination
        if dest.strip() != '':
            age = data['gap'].disappeartime - staticReport.timestamp
            dest += f'({age})'
            return dest
        else:
            return 'unknown'
    
    infos = {}
    infos['Declared Destination'] = getDest()
    infos['Gap Duration'] = pd.to_timedelta(data['gap'].darkduration, unit='S')
    infos['Gap Distance'] = str(np.round(data['gap'].darkdistance, 1)) + ' NM'
    infos['Minimum Average Speed'] = str(np.round(data['gap'].darkspeed, 2)) + ' kts'
    md += '\n\n---\n' + toMarkdown(infos)
    return pn.pane.Markdown(md)

infos = pn.bind(getInfos, idSelector)

controls = pn.WidgetBox(idSelector, previousSlider, nextSlider, infos)

iPane = pn.bind(lambda iMap: pn.pane.plot.Folium(iMap, height=800), iMap)

main = pn.GridSpec(sizing_mode='stretch_both')
main[0, 0] = controls
main[0, 1:3] = iPane

template = pn.template.BootstrapTemplate(title='AIS Labeler').servable()
template.main.append(main)

#%% Server Handling

server = template.show(title='AIS Labeler', threaded=True)
#server.stop()