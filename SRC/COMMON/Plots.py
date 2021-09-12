import sys, os
import matplotlib as mpl
from matplotlib.markers import MarkerStyle
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np
import warnings
import matplotlib.cbook

warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)

COLORS = ['b','r','c','m','y','g','k']
MARKERS = ['+','|','o','v','^','.','8','s','*','D']


def createFigure(PlotConf):
    try:
        fig, ax = plt.subplots(1, 1, figsize=PlotConf["FigSize"])

    except:
        fig, ax = plt.subplots(1, 1)

    return fig, ax


def saveFigure(fig, Path):
    Dir = os.path.dirname(Path)
    try:
        os.makedirs(Dir)
    except:
        pass
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


def prepareDoubleAxis(PlotConf, ax1, ax2):
    for key in PlotConf:
        if key == "Title":
            ax1.set_title(PlotConf["Title"])

        for axis in ["x", "y"]:
            if axis == "x":
                if key == axis + "Label":
                    ax1.set_xlabel(PlotConf[axis + "Label"])

                if key == axis + "Ticks":
                    ax1.set_xticks(PlotConf[axis + "Ticks"])

                if key == axis + "TicksLabels":
                    ax1.set_xticklabels(PlotConf[axis + "TicksLabels"])

                if key == axis + "Lim":
                    ax1.set_xlim(PlotConf[axis + "Lim"])

            if axis == "y":
                if key == axis + "1AxisLabel":
                    ax1.set_ylabel(PlotConf[axis + "1AxisLabel"])

                if key == axis + "2AxisLabel":
                    ax2.set_ylabel(PlotConf[axis + "2AxisLabel"])

                if key == axis + "1Ticks":
                    ax1.set_yticks(PlotConf[axis + "1Ticks"])

                if key == axis + "2Ticks":
                    ax2.set_yticks(PlotConf[axis + "2Ticks"])

                if key == axis + "1TicksLabels":
                    ax1.set_yticklabels(PlotConf[axis + "1TicksLabels"])

                if key == axis + "2TicksLabels":
                    ax2.set_yticklabels(PlotConf[axis + "2TicksLabels"])

                if key == axis + "1Lim":
                    ax1.set_ylim(PlotConf[axis + "1Lim"])

                if key == axis + "2Lim":
                    ax2.set_ylim(PlotConf[axis + "2Lim"])

        if key == "Grid" and PlotConf[key] == True:
            ax1.grid(linestyle='--', linewidth=0.5, which='both')


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

    normalize = mpl.cm.colors.Normalize(vmin=Min, vmax=Max)

    if "RejectFlag" in PlotConf:
        bounds = np.linspace(int(Min), int(Max), int(Max + 1))
        normalize = mpl.colors.BoundaryNorm(bounds, int(Max))

    divider = make_axes_locatable(ax)
    # size size% of the plot and gap of pad% from the plot
    color_ax = divider.append_axes("right", size="3%", pad="2%")
    cmap = mpl.cm.get_cmap(PlotConf["ColorBar"])
    cbar = mpl.colorbar.ColorbarBase(color_ax,
                                     cmap=cmap,
                                     norm=mpl.colors.Normalize(vmin=Min, vmax=Max),
                                     label=PlotConf["ColorBarLabel"])

    return normalize, cmap



def generateLinesPlot(PlotConf):
    LineWidth = 1.5
    fig, ax = createFigure(PlotConf)

    if PlotConf["DoubleAxis"] == True:
        ax1 = ax
        ax2 = ax1.twinx()
        prepareDoubleAxis(PlotConf, ax1, ax2)

        for Label in PlotConf["y1Data"].keys():
            ax1.plot(PlotConf["xData"][Label], PlotConf["y1Data"][Label],
                     PlotConf["Marker"],
                     color=PlotConf["y1Color"][Label],
                     label=PlotConf["y1Label"][Label],
                     linewidth=LineWidth)

        for Label in PlotConf["y2Data"].keys():
            ax2.plot(PlotConf["xData"][Label], PlotConf["y2Data"][Label],
                     PlotConf["Marker"],
                     color=PlotConf["y2Color"][Label],
                     label=PlotConf["y2Label"][Label],
                     linewidth=LineWidth)

        if PlotConf["Legend"]:
            handles_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
            handles, labels = [sum(lol, []) for lol in zip(*handles_labels)]
            ax1.legend(handles, labels, loc='upper right', prop={'size': 8})

    else:
        prepareAxis(PlotConf, ax)

        for key in PlotConf:
            if key == "LineWidth":
                LineWidth = PlotConf["LineWidth"]
            if key == "ColorBar" and not "RejectFlag" in PlotConf:
                normalize, cmap = prepareColorBar(PlotConf, ax, PlotConf["zData"])


        for Label in PlotConf["yData"].keys():
            if "ColorBar" in PlotConf:
                if "RejectFlag" in PlotConf and PlotConf["RejectFlag"] == True:
                    cmap = mpl.cm.get_cmap(PlotConf["ColorBar"])

                    im = ax.scatter(PlotConf["xData"][Label], PlotConf["yData"][Label],
                                    marker='o',
                                    s=2,
                                    linewidth=8,
                                    c=PlotConf["zData"][Label],
                                    cmap=cmap)
                else:
                    if "NotConv" in PlotConf and PlotConf["NotConv"] == True:
                        ax.scatter(PlotConf["xDataNotConv"][Label], PlotConf["yDataNotConv"][Label],
                                   marker=PlotConf["Marker"],
                                   s=PlotConf["MarkerSize"],
                                   linewidth=LineWidth,
                                   c='grey')

                    ax.scatter(PlotConf["xData"][Label], PlotConf["yData"][Label],
                               marker=PlotConf["Marker"],
                               s=PlotConf["MarkerSize"],
                               linewidth=LineWidth,
                               c=cmap(normalize(np.array(PlotConf["zData"][Label]))))
            else:
                ax.plot(PlotConf["xData"][Label], PlotConf["yData"][Label],
                        PlotConf["Marker"],
                        markersize=PlotConf["MarkerSize"],
                        color=PlotConf["Color"][Label],
                        label=PlotConf["Label"][Label],
                        linewidth=LineWidth)

        if PlotConf["Legend"]:
            ax.legend(loc='upper right')

        if "RejectFlag" in PlotConf and PlotConf["RejectFlag"] == True:
            plt.colorbar(im, ticks=range(0, 33), boundaries=range(0, 33), label=PlotConf["ColorBarLabel"])

    saveFigure(fig, PlotConf["Path"])


def generatePlot(PlotConf):
    if (PlotConf["Type"] == "Lines"):
        generateLinesPlot(PlotConf)


def generateChallengePlot(PlotConf):
    fig, ax = plt.subplots(1, 1, figsize=PlotConf["FigSize"], subplot_kw={'projection': 'polar'})
    rticks = np.arange(0, 100, 10)

    # ax.plot(PlotConf["tData"], PlotConf["rData"])
    ax.set_rmax(90)
    ax.set_rmin(0)
    ax.set_rticks(rticks)
    ax.set_rlim(bottom=90, top=0)
    ax.set_rlabel_position(22.5)
    ax.set_theta_zero_location("N", offset=0.0)
    ax.set_xticks(np.deg2rad(np.arange(0, 361, 22.5)))
    ax.set_xticklabels(['N', '', '', '', 'E', '', '', '', 'S', '', '', '', 'W', '', '', ''])
    ax.set_yticklabels([str(rtick) + '°' for rtick in rticks])
    ax.set_theta_direction(-1)

    for key in PlotConf:
        if key == "Title":
            ax.set_title(PlotConf["Title"])
        if key == "Grid" and PlotConf[key] == True:
            ax.grid(linestyle='--', linewidth=0.5, which='both')
        if key == "LineWidth":
            LineWidth = PlotConf["LineWidth"]

    cmap = mpl.cm.get_cmap(PlotConf["ColorBar"])

    im = ax.scatter(PlotConf["tData"], PlotConf["rData"],
                    marker=PlotConf["Marker"],
                    s=PlotConf["MarkerSize"],
                    linewidth=LineWidth,
                    c=PlotConf["zData"],
                    cmap=cmap)

    plt.colorbar(im, ticks=range(0, 33), label=PlotConf["zLabel"])

    saveFigure(fig, PlotConf["Path"])