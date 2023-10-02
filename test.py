import numpy as np
import pandas as pd
import geopandas as gpd
import folium
import panel as pn

mmsi = pn.widgets.IntInput()

a = [0, 1, 2]

markdown = pn.pane.Markdown(str(mmsi.value))

toggle = pn.widgets.Toggle(name='Toggle', button_type='success')

def sendLabel(event):
    print(markdown.object)

toggle.param.watch(sendLabel, 'value')
#text_input.link(markdown, value='object')


#--------------------------------------------------

class Labeler():
    
    template = pn.template.BootstrapTemplate(title='AIS Labeler').servable()
    template.main.append(pn.Row(markdown, toggle))
    
    def __init__(self):
        server = self.template.show(title='AIS Labeler', threaded=True)

l = Labeler()