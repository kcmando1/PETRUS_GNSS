
import sys, os
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
import conda
from mpl_toolkits.axes_grid1 import make_axes_locatable
CondaFileDir = conda.__file__
CondaDir = CondaFileDir.split('lib')[0]
ProjLib = os.path.join(os.path.join(CondaDir, 'share'), 'proj')
os.environ["PROJ_LIB"] = ProjLib
from mpl_toolkits.basemap import Basemap

import warnings
import matplotlib.cbook
warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)

import PlotsConstants as Const

def createFigure(PlotConf):
    try:
        fig, ax = plt.subplots(1, 1, figsize = PlotConf["FigSize"])
    
    except:
        fig, ax = plt.subplots(1, 1)

    return fig, ax

def saveFigure(fig, Path):
    Dir = os.path.dirname(Path)
    try:
        os.makedirs(Dir)
    except: pass
    fig.savefig(Path, dpi=150., bbox_inches='tight')

def prepareAxis(PlotConf, ax):
    for key in PlotConf:
        if key == "Title":
            ax.set_title(PlotConf["Title"])

        for axis in ["x", "y"]:
            if axis == "x":
                if key == axis + "Label":
                    ax.set_xlabel(PlotConf[axis + "Label"])

                if key == axis + "Ticks":
                    ax.set_xticks(PlotConf[axis + "Ticks"])

                if key == axis + "TicksLabels":
                    ax.set_xticklabels(PlotConf[axis + "TicksLabels"])
                
                if key == axis + "Lim":
                    ax.set_xlim(PlotConf[axis + "Lim"])

            if axis == "y":
                if key == axis + "Label":
                    ax.set_ylabel(PlotConf[axis + "Label"])

                if key == axis + "Ticks":
                    ax.set_yticks(PlotConf[axis + "Ticks"])

                if key == axis + "TicksLabels":
                    ax.set_yticklabels(PlotConf[axis + "TicksLabels"])
                
                if key == axis + "Lim":
                    ax.set_ylim(PlotConf[axis + "Lim"])

        if key == "Grid" and PlotConf[key] == True:
            ax.grid(linestyle='--', linewidth=0.5, which='both')

def prepareColorBar(PlotConf, ax, Values):
    try:
        Min = PlotConf["ColorBarMin"]
    except:
        Mins = []
        for v in Values.values():
            Mins.append(min(v))
        Min = min(Mins)
    try:
        Max = PlotConf["ColorBarMax"]
    except:
        Maxs = []
        for v in Values.values():
            Maxs.append(max(v))
        Max = max(Maxs)
    print(Min)
    print(Max)
    
    normalize = mpl.cm.colors.Normalize(vmin=Min, vmax=Max)

    divider = make_axes_locatable(ax)
    # size size% of the plot and gap of pad% from the plot
    color_ax = divider.append_axes("right", size="3%", pad="2%")
    cmap = mpl.cm.get_cmap(PlotConf["ColorBar"])
    cbar = mpl.colorbar.ColorbarBase(color_ax, 
    cmap=cmap,
    norm=mpl.colors.Normalize(vmin=Min, vmax=Max),
    label=PlotConf["ColorBarLabel"])

    return normalize, cmap

def drawMap(PlotConf, ax,):
    Map = Basemap(projection = 'cyl',
    llcrnrlat  = PlotConf["LatMin"]-0,
    urcrnrlat  = PlotConf["LatMax"]+0,
    llcrnrlon  = PlotConf["LonMin"]-0,
    urcrnrlon  = PlotConf["LonMax"]+0,
    lat_ts     = 10,
    resolution = 'l',
    ax         = ax)

    # Draw map meridians
    Map.drawmeridians(
    np.arange(PlotConf["LonMin"],PlotConf["LonMax"]+1,PlotConf["LonStep"]),
    labels = [0,0,0,1],
    fontsize = 6,
    linewidth=0.2)
        
    # Draw map parallels
    Map.drawparallels(
    np.arange(PlotConf["LatMin"],PlotConf["LatMax"]+1,PlotConf["LatStep"]),
    labels = [1,0,0,0],
    fontsize = 6,
    linewidth=0.2)

    # Draw coastlines
    Map.drawcoastlines(linewidth=0.5)

    # Draw countries
    Map.drawcountries(linewidth=0.25)

def generateLinesPlot(PlotConf):
    LineWidth = 1.5
    twinax=0
    leg=0
    fig, ax = createFigure(PlotConf)

    prepareAxis(PlotConf, ax)
    
    PlotConf["twinx"]=-1
    for key in PlotConf:
        if key == "LineWidth":
            LineWidth = PlotConf["LineWidth"]
        if key == "ColorBar":
            normalize, cmap = prepareColorBar(PlotConf, ax, PlotConf["zData"])
        if key == "Map" and PlotConf[key] == True:
            drawMap(PlotConf, ax)
        if key == "twinx":
            twinax=1

            
        if key == "legend":
            leg=1
                
    if leg==1:
        for Label in PlotConf["yData"].keys():
            print(Label)
            if "ColorBar" in PlotConf:
                ax.scatter(PlotConf["xData"][Label], PlotConf["yData"][Label], 
                marker = PlotConf["Marker"],
                linewidth = LineWidth,
                c = cmap(normalize(np.array(PlotConf["zData"][Label]))))

            else:
                
                
                if PlotConf["twinx"]==Label and twinax==1:
                    ax2=ax.twinx()    
                    ax2.plot(PlotConf["xData"][Label], PlotConf["yData"][Label],
                    PlotConf["Marker"],
                    linewidth = LineWidth,
                    label=PlotConf["yLegend"][Label])
                    twinax=0
                else:
                    ax.plot(PlotConf["xData"][Label], PlotConf["yData"][Label],
                    PlotConf["Marker"],
                    linewidth = LineWidth,
                    label=PlotConf["yLegend"][Label])
        fig.legend(loc="upper right", bbox_to_anchor=(1,1), bbox_transform=ax.transAxes)
        ax.set_ylabel(PlotConf["yLabel"])
    else:
        for Label in PlotConf["yData"].keys():

            if "ColorBar" in PlotConf:
                ax.scatter(PlotConf["xData"][Label], PlotConf["yData"][Label], 
                marker = PlotConf["Marker"],
                linewidth = LineWidth,
                c = cmap(normalize(np.array(PlotConf["zData"][Label]))))

            else:
                if twinax==1:
                    if PlotConf["twinx"]==Label:
                        ax2=ax.twinx()    
                        ax2.plot(PlotConf["xData"][Label], PlotConf["yData"][Label],
                        PlotConf["Marker"],
                        linewidth = LineWidth,)
                        twinax=0
                else:
                    ax.plot(PlotConf["xData"][Label], PlotConf["yData"][Label],
                    PlotConf["Marker"],
                    linewidth = LineWidth,
                    label=PlotConf["yLabel"][Label])
    
    
    saveFigure(fig, PlotConf["Path"])


def generatePlot(PlotConf):
    if(PlotConf["Type"] == "Lines"):
        generateLinesPlot(PlotConf)
    if(PlotConf["Type"] == "Polar"):
        
        fig, ax = plt.subplots(1,1,figsize=(10,10),subplot_kw={'projection':'polar'})      
        ax.set_title(PlotConf["Title"])
        ax.set_rmax(90)
        ax.set_rlim(bottom=90, top=0)
        ax.grid(True)
        ax.set_xticklabels(['N', '', 'E', '', 'S', '', 'W', ''])
        ax.set_theta_zero_location("N", offset=0.0)
        ax.set_theta_direction(-1)
        for key in PlotConf:
            if key == "LineWidth":
                LineWidth = PlotConf["LineWidth"]
    
        ex=ax.scatter(PlotConf["rData"], PlotConf["tData"],
        c=PlotConf["zData"],
        cmap="plasma",
        marker = PlotConf["Marker"],
        linewidth = LineWidth)
        plt.colorbar(ex)
        
        saveFigure(fig, PlotConf["Path"])

             