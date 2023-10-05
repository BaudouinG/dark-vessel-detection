import numpy as np
import pandas as pd
import geopandas as gpd
import folium
import panel as pn
from utils import getValues, DATASETS_DIRECTORY_PATH
from time import sleep

#%% Ressources Importation ( /!\ long execution time /!\ )

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

disappearIcon = folium.features.CustomIcon(icon_image='Markers/x.png', icon_size=(40,40), icon_anchor=(20,20))
reappearIcon = folium.features.CustomIcon(icon_image='Markers/v.png', icon_size=(40,40), icon_anchor=(20,20))

#%% Labeler Class Definition

class Labeler():
    
    def __init__(self, batchSize=None):
        
        # "Backend" params
        self.preventLabeling = pn.widgets.Toggle(value=True)
        self.preventIDChange = pn.widgets.Toggle(value=False)
        self.currentLabel = pn.widgets.IntInput(value=None)
        
        self.preventLabeling.param.watch(self.toggleLabeling, 'value')
        self.preventIDChange.param.watch(self.toggleIDChange, 'value')
        
        # "Frontend" params
        self.IDSelector = pn.widgets.IntInput(name='Gap ID', value=0, step=1, start=0, end=len(gaps)-1,
                                         disabled=self.preventIDChange.value)
        self.previousSlider = pn.widgets.EditableIntSlider(name='Previous Positions', fixed_start=0, fixed_end=1000,
                                                           value=200)
        self.nextSlider = pn.widgets.EditableIntSlider(name='Next Positions', fixed_start=0, fixed_end=1000, value=200)
        self.OOSButton = pn.widgets.Button(name='On-Off Switch', button_type='danger', icon='alert-triangle-filled',
                                      disabled=self.preventLabeling.value)
        self.otherButton = pn.widgets.Button(name='Other', button_type='warning', icon='question-mark',
                                        disabled=self.preventLabeling.value)
        self.OOSButton.on_click(self.labelAsOOS)
        self.otherButton.on_click(self.labelAsOther)
        
        self.data = pn.bind(self.getData, self.IDSelector, self.previousSlider, self.nextSlider)
        self.infos = pn.bind(self.getInfos, self.IDSelector, self.previousSlider, self.nextSlider)
        self.foliumMap = pn.bind(self.getFoliumMap, self.IDSelector, self.previousSlider, self.nextSlider)
        
        # "Active Learning" params
        self.batchSize = batchSize
        self.batch = None
        self.batchProgress = None
        self.defaultStatus = 'Not currently labeling'
        styles = {'border': '1px solid white', 'border-radius': '5px', 'color': 'white', 'padding': '10px'}
        self.status = pn.pane.HTML(self.defaultStatus, styles=styles)
        self.preventLabeling.param.watch(self.setStatus, 'value')
        
        # Layout organisation and server start
        self.buttons = pn.Row(self.OOSButton, self.otherButton)
        self.controls = pn.WidgetBox(self.IDSelector, self.previousSlider, self.nextSlider, self.infos, self.buttons)
        self.main = pn.Row(self.controls, self.foliumMap)
        
        self.template = pn.template.BootstrapTemplate(title='AIS Labeler').servable()
        self.template.main.append(self.main)
        self.template.header.append(self.status)
        
        self.server = self.template.show(title='AIS Labeler', threaded=True)
    
    # Active Learning" Methods
    def setStatus(self, event):
        
        if event.new == True:
            html = self.defaultStatus
        else:
            html = f"Batch {self.batch}, labeling {self.batchProgress}/{self.batchSize}"
        self.status.object = html
    
    # "Backend" Methods
    def toggleLabeling(self, event):
        self.OOSButton.disabled = event.new
        self.otherButton.disabled = event.new

    def toggleIDChange(self, event): self.IDSelector.disabled = event.new
    
    def labelAsOOS(self, event):
        self.confirmLabel(1)
        
    def labelAsOther(self, event):
        self.confirmLabel(0)
            
    def confirmOOS(self, event):
        self.currentLabel.value = 1
        
    def confirmOther(self, event):
        self.currentLabel.value = 0
    
    def back(self, event):
        self.currentLabel.value = -1
    
    def confirmLabel(self, label):
        self.buttons.clear()
        self.isConfirmed = pn.widgets.Toggle(value=False)
        self.escape = pn.widgets.Toggle(value=False)
        self.confirmButton = pn.widgets.Button(name='confirm', button_type='primary')
        self.backButton = pn.widgets.Button(name='return')
        if label == 1:
            self.confirmButton.on_click(self.confirmOOS)
        else:
            self.confirmButton.on_click(self.confirmOther)
        self.backButton.on_click(self.back)
        self.buttons.append(pn.Row(self.confirmButton, self.backButton))
    
    def askLabel(self, gapID, batch=None, batchProgress=None):
        self.batch = batch
        self.batchProgress = batchProgress
        self.preventIDChange.value = True
        self.preventLabeling.value = False
        self.currentLabel.value = None
        previousID = self.IDSelector.value
        self.IDSelector.value = int(gapID)
        
        while self.currentLabel.value is None:
            sleep(0.05)
            
        self.buttons.clear()
        self.buttons.append(pn.Row(self.OOSButton, self.otherButton))
        if self.currentLabel.value == -1:
            return self.askLabel(gapID, batch=batch, batchProgress=batchProgress)
        else:
            self.preventIDChange.value = False
            self.preventLabeling.value = True
            label = self.currentLabel.value
            ID = self.IDSelector.value
            self.currentLabel.value = None
            self.IDSelector.value = previousID
            return {ID: label}
    
    # "Frontend" Methods
    def getData(self, gapID, previousReports, nextReports):
        
        data = {}
        previousReports += 1
        nextReports += 1
        data['mmsi'] = gaps.loc[gapID].mmsi
        data['gap'] = gaps.loc[gapID]
        data['static'] = static.loc[static.sourcemmsi == data['mmsi']]
        reports = dynamic.loc[dynamic.sourcemmsi == data['mmsi']]
        prev = reports.loc[reports.timestamp <= data['gap'].disappeartime].iloc[-previousReports:]
        nex = reports.loc[reports.timestamp >= data['gap'].reappeartime].iloc[:nextReports]
        data['dynamic'] = pd.concat([prev, nex])
        
        return data
    
    
    def getInfos(self, gapID, previousReports, nextReports):
        
        def toMarkdown(infos):
            md = ''
            for info in infos:
                md += f'**{info}:** {infos[info]}\n\n'
            return md.rstrip('\n')
        
        data = self.data()
        infos = {}
        infos['Vessel Name'] = list(getValues(data['static'].shipname).keys())[0]
        infos['MMSI'] = data['mmsi']
        md = '---\n' + toMarkdown(infos)
        
        def getDest():
            staticReport = data['static'].loc[data['static'].timestamp <= data['gap'].disappeartime].iloc[-1]
            dest = str(staticReport.destination)
            if dest.strip() != '' and dest != 'nan':
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
        md += '\n\n---\n' + toMarkdown(infos) + '\n\n---\n'
        
        return pn.pane.Markdown(md)
    
    
    def plot(self, data):
        
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
    
    
    def getFoliumMap(self, gapID, previousReports, nextReports):
        #NB: both "previousSlider" and "nextSlider" values are unused but trigger map updates
        
        m = folium.Map(tiles="cartodb positron", height='100%', 
                       location=(48, -5), zoom_start=7, control_scale=True, prefer_canvas=True)
        for mapFeature in self.plot(self.data()):
            mapFeature.add_to(m)
            
        return pn.pane.plot.Folium(m, sizing_mode='stretch_both')
