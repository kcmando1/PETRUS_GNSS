#!/usr/bin/env python

########################################################################
# PETRUS/SRC/PreprocessingPlots.py:
# This is the PreprocessingPlots Module of PETRUS tool
#
#  Project:        PETRUS
#  File:           PreprocessingPlots.py
#  Date(YY/MM/DD): 05/02/21
#
#   Author: GNSS Academy
#   Copyright 2021 GNSS Academy
#
# -----------------------------------------------------------------
# Date       | Author             | Action
# -----------------------------------------------------------------
#
########################################################################


import sys, os
from pandas import unique
from pandas import read_csv
from InputOutput import PreproIdx
from InputOutput import REJECTION_CAUSE_DESC

sys.path.append(os.getcwd() + '/' + \
                os.path.dirname(sys.argv[0]) + '/' + 'COMMON')
from COMMON import GnssConstants
from COMMON.Plots import generatePlot
import numpy as np


def initPlot(PreproObsFile, PlotConf, Title, Label):
    PreproObsFileName = os.path.basename(PreproObsFile)
    PreproObsFileNameSplit = PreproObsFileName.split('_')
    Rcvr = PreproObsFileNameSplit[2]
    DatepDat = PreproObsFileNameSplit[3]
    Date = DatepDat.split('.')[0]
    Year = Date[1:3]
    Doy = Date[4:]

    PlotConf["xLabel"] = "Hour of Day %s" % Doy
    PlotConf["xTicks"] = range(0, 25)
    PlotConf["xLim"] = [0, 24]

    PlotConf["Title"] = "%s from %s on Year %s" \
                        " DoY %s" % (Title, Rcvr, Year, Doy)

    PlotConf["Path"] = sys.argv[1] + '/OUT/PPVE/figures/%s/' % Label + \
                       '%s_%s_Y%sD%s.png' % (Label, Rcvr, Year, Doy)

def plotSatVisibility(PreproObsFile, PreproObsData):
    PlotConf = {}

    initPlot(PreproObsFile, PlotConf, "Satellite Visibility", "SAT_VISIBILITY")

    PlotConf["Type"] = "Lines"
    PlotConf["FigSize"] = (10, 7)
    PlotConf["yLabel"] = "GPS-PRN"
    PlotConf["yTicks"] = sorted(unique(PreproObsData[PreproIdx["PRN"]]))
    PlotConf["yTicksLabels"] = sorted(unique(PreproObsData[PreproIdx["PRN"]]))
    PlotConf["yLim"] = [0, max(unique(PreproObsData[PreproIdx["PRN"]]))]
    PlotConf["zLabel"] = "Elevation [deg]"
    PlotConf["Marker"] = 'o'
    PlotConf["MarkerSize"] = 5
    PlotConf["LineWidth"] = 5
    PlotConf["ColorBar"] = "gnuplot"
    PlotConf["ColorBarLabel"] = "Elevation [deg]"
    PlotConf["ColorBarMin"] = 0.
    PlotConf["ColorBarMax"] = 90.
    PlotConf["Grid"] = True
    PlotConf["Legend"] = False
    PlotConf["DoubleAxis"] = False
    PlotConf["NotConv"] = True
    #   filter the output x sat
    PlotConf["xData"] = {}
    PlotConf["yData"] = {}
    PlotConf["zData"] = {}
    PlotConf["xDataNotConv"] = {}
    PlotConf["yDataNotConv"] = {}
    PlotConf["zDataNotConv"] = {}
    Label = 0

    Filter = PreproObsData[PreproIdx["STATUS"]] == 1
    PlotConf["xData"][Label] = PreproObsData[PreproIdx["SOD"]][Filter] / GnssConstants.S_IN_H
    PlotConf["yData"][Label] = PreproObsData[PreproIdx["PRN"]][Filter]
    PlotConf["zData"][Label] = PreproObsData[PreproIdx["ELEV"]][Filter]
    Filter = PreproObsData[PreproIdx["STATUS"]] == 0
    PlotConf["xDataNotConv"][Label] = PreproObsData[PreproIdx["SOD"]][Filter] / GnssConstants.S_IN_H
    PlotConf["yDataNotConv"][Label] = PreproObsData[PreproIdx["PRN"]][Filter]
    PlotConf["zDataNotConv"][Label] = PreproObsData[PreproIdx["ELEV"]][Filter]

    generatePlot(PlotConf)

def plotNumSats(PreproObsFile, PreproObsData):
    PlotConf = {}

    initPlot(PreproObsFile, PlotConf, "Number of Satellites", "SAT_NUM")

    PlotConf["Type"] = "Lines"
    PlotConf["FigSize"] = (10, 7)
    PlotConf["yLabel"] = "Number of Satellites"
    PlotConf["yTicks"] = range(0, 15, 2)
    PlotConf["yLim"] = [0, 14]
    PlotConf["Marker"] = '-'
    PlotConf["MarkerSize"] = 1
    PlotConf["LineWidth"] = 1
    # Generation of the sat numbers
    Sats = []
    SmSats = []

    for SOD in unique(PreproObsData[PreproIdx["SOD"]]):
        Filter = (PreproObsData[PreproIdx["SOD"]] == SOD)
        Sats.append(len(PreproObsData[PreproIdx["SOD"]][Filter]))

        Filter = ((PreproObsData[PreproIdx["SOD"]] == SOD) & (PreproObsData[PreproIdx["STATUS"]] == 1))
        SmSats.append(len(PreproObsData[PreproIdx["SOD"]][Filter]))

    PlotConf["xData"] = {}
    PlotConf["yData"] = {}
    PlotConf["Color"] = {}
    PlotConf["Label"] = {}
    Label = 0
    PlotConf["Label"][Label] = 'RAW'
    PlotConf["Color"][Label] = 'orange'
    PlotConf["xData"][Label] = unique(PreproObsData[PreproIdx["SOD"]]) / GnssConstants.S_IN_H
    PlotConf["yData"][Label] = Sats
    Label = 1
    PlotConf["Label"][Label] = 'SMOOTHED'
    PlotConf["Color"][Label] = 'green'
    PlotConf["xData"][Label] = unique(PreproObsData[PreproIdx["SOD"]]) / GnssConstants.S_IN_H
    PlotConf["yData"][Label] = SmSats
    PlotConf["Grid"] = True
    PlotConf["Legend"] = True
    PlotConf["DoubleAxis"] = False

    generatePlot(PlotConf)

def plotC1C1Smoothed(PreproObsFile, PreproObsData):
    PlotConf = {}

    initPlot(PreproObsFile, PlotConf, "C1 - C1Smoothed", "SAT_C1_C1SMOOTHED")

    PlotConf["Type"] = "Lines"
    PlotConf["FigSize"] = (10, 7)
    PlotConf["yLabel"] = "C1 - C1Smoothed [m]"
    PlotConf["yTicks"] = range(-3, 3)
    PlotConf["yLim"] = [-3, 2.25]
    PlotConf["Marker"] = 'P'
    PlotConf["MarkerSize"] = 0.5
    PlotConf["LineWidth"] = 1
    PlotConf["ColorBar"] = "gnuplot"
    PlotConf["ColorBarLabel"] = "C/N0 [deg]"
    PlotConf["ColorBarMin"] = 35.
    PlotConf["ColorBarMax"] = 51.
    # data prep
    PlotConf["xData"] = {}
    PlotConf["yData"] = {}
    PlotConf["zData"] = {}
    Label = 0

    Filter = PreproObsData[PreproIdx["STATUS"]] == 1
    PlotConf["xData"][Label] = PreproObsData[PreproIdx["SOD"]][Filter] / GnssConstants.S_IN_H
    PlotConf["yData"][Label] = PreproObsData[PreproIdx["C1"]][Filter] - PreproObsData[PreproIdx["C1SMOOTHED"]][
        Filter]
    PlotConf["zData"][Label] = PreproObsData[PreproIdx["S1"]][Filter]

    PlotConf["Grid"] = True
    PlotConf["Legend"] = False
    PlotConf["DoubleAxis"] = False

    generatePlot(PlotConf)

def plotC1C1SmoothedvsElev(PreproObsFile, PreproObsData):
    PlotConf = {}

    initPlot(PreproObsFile, PlotConf, "C1 - C1Smoothed vs Elevation", "SAT_C1_C1SMOOTHED_VS_ELEV")

    PlotConf["Type"] = "Lines"
    PlotConf["FigSize"] = (10, 7)
    PlotConf["yLabel"] = "C1 - C1Smoothed [m]"
    PlotConf["yTicks"] = range(-3, 3)
    PlotConf["yLim"] = [-3, 2.25]
    PlotConf["xLabel"] = "Elevation [deg]"
    PlotConf["xTicks"] = range(0, 100, 10)
    PlotConf["xLim"] = [0, 90]
    PlotConf["Marker"] = 'P'
    PlotConf["MarkerSize"] = 0.5
    PlotConf["LineWidth"] = 1
    PlotConf["ColorBar"] = "gnuplot"
    PlotConf["ColorBarLabel"] = "C/N0 [deg]"
    PlotConf["ColorBarMin"] = 35.
    PlotConf["ColorBarMax"] = 51.
    # data prep
    PlotConf["xData"] = {}
    PlotConf["yData"] = {}
    PlotConf["zData"] = {}
    Label = 0

    Filter = PreproObsData[PreproIdx["STATUS"]] == 1
    PlotConf["xData"][Label] = PreproObsData[PreproIdx["ELEV"]][Filter]
    PlotConf["yData"][Label] = PreproObsData[PreproIdx["C1"]][Filter] - PreproObsData[PreproIdx["C1SMOOTHED"]][Filter]
    PlotConf["zData"][Label] = PreproObsData[PreproIdx["S1"]][Filter]

    PlotConf["Grid"] = True
    PlotConf["Legend"] = False
    PlotConf["DoubleAxis"] = False

    generatePlot(PlotConf)

def plotRejectionFlags(PreproObsFile, PreproObsData):
    PlotConf = {}

    initPlot(PreproObsFile, PlotConf, "Rejection Flags", "REJ_FLAGS")

    PlotConf["Type"] = "Lines"
    PlotConf["FigSize"] = (10, 7)
    PlotConf["yLabel"] = "Rejection Flags"
    PlotConf["yTicks"] = range(1, 11)
    PlotConf["yTicksLabels"] = REJECTION_CAUSE_DESC.keys()
    PlotConf["yLim"] = [0, 11]
    PlotConf["ColorBar"] = "gist_ncar"
    PlotConf["ColorBarLabel"] = "GPS-PRN"
    PlotConf["ColorBarMin"] = 0.
    PlotConf["ColorBarMax"] = 32.
    # data prep
    PlotConf["xData"] = {}
    PlotConf["yData"] = {}
    PlotConf["zData"] = {}
    Label = 0

    Filter = PreproObsData[PreproIdx["REJECT"]] != 0
    PlotConf["xData"][Label] = PreproObsData[PreproIdx["SOD"]][Filter] / GnssConstants.S_IN_H
    PlotConf["yData"][Label] = PreproObsData[PreproIdx["REJECT"]][Filter]
    PlotConf["zData"][Label] = PreproObsData[PreproIdx["PRN"]][Filter]

    PlotConf["Grid"] = True
    PlotConf["Legend"] = False
    PlotConf["DoubleAxis"] = False
    PlotConf["RejectFlag"] = True

    generatePlot(PlotConf)

def plotCodeRate(PreproObsFile, PreproObsData):
    PlotConf = {}

    initPlot(PreproObsFile, PlotConf, "Code Rate", "CODE_RATE")

    PlotConf["Type"] = "Lines"
    PlotConf["FigSize"] = (10, 7)
    PlotConf["yLabel"] = "Code Rate [m/s]"
    PlotConf["yTicks"] = range(-800, 1000, 200)
    PlotConf["yLim"] = [-800, 800]
    PlotConf["Marker"] = 'P'
    PlotConf["MarkerSize"] = 0.5
    PlotConf["LineWidth"] = 1
    PlotConf["ColorBar"] = "gnuplot"
    PlotConf["ColorBarLabel"] = "Elevation [deg]"
    PlotConf["ColorBarMin"] = 0.
    PlotConf["ColorBarMax"] = 90.
    # data prep
    PlotConf["xData"] = {}
    PlotConf["yData"] = {}
    PlotConf["zData"] = {}
    Label = 0

    Filter = PreproObsData[PreproIdx["STATUS"]] == 1
    PlotConf["xData"][Label] = PreproObsData[PreproIdx["SOD"]][Filter] / GnssConstants.S_IN_H
    PlotConf["yData"][Label] = PreproObsData[PreproIdx["CODE RATE"]][Filter]
    PlotConf["zData"][Label] = PreproObsData[PreproIdx["ELEV"]][Filter]

    PlotConf["Grid"] = True
    PlotConf["Legend"] = False
    PlotConf["DoubleAxis"] = False

    generatePlot(PlotConf)

def plotCodeRateStep(PreproObsFile, PreproObsData):
    PlotConf = {}

    initPlot(PreproObsFile, PlotConf, "Code Rate Step", "CODE_RATE_STEP")

    PlotConf["Type"] = "Lines"
    PlotConf["FigSize"] = (10, 7)
    PlotConf["yLabel"] = "Code Rate Step [m/s^2]"
    PlotConf["yTicks"] = np.arange(-0.05, 0.25, 0.05)
    PlotConf["yLim"] = [-0.05, 0.20]
    PlotConf["Marker"] = 'P'
    PlotConf["MarkerSize"] = 0.5
    PlotConf["LineWidth"] = 1
    PlotConf["ColorBar"] = "gnuplot"
    PlotConf["ColorBarLabel"] = "Elevation [deg]"
    PlotConf["ColorBarMin"] = 0.
    PlotConf["ColorBarMax"] = 90.
    # data prep
    PlotConf["xData"] = {}
    PlotConf["yData"] = {}
    PlotConf["zData"] = {}
    Label = 0

    Filter = PreproObsData[PreproIdx["STATUS"]] == 1
    PlotConf["xData"][Label] = PreproObsData[PreproIdx["SOD"]][Filter] / GnssConstants.S_IN_H
    PlotConf["yData"][Label] = PreproObsData[PreproIdx["CODE ACC"]][Filter]
    PlotConf["zData"][Label] = PreproObsData[PreproIdx["ELEV"]][Filter]

    PlotConf["Grid"] = True
    PlotConf["Legend"] = False
    PlotConf["DoubleAxis"] = False

    generatePlot(PlotConf)

def plotPhaseRate(PreproObsFile, PreproObsData):
    PlotConf = {}

    initPlot(PreproObsFile, PlotConf, "Phase Rate", "PHASE_RATE")

    PlotConf["Type"] = "Lines"
    PlotConf["FigSize"] = (10, 7)
    PlotConf["yLabel"] = "Phase Rate [m/s]"
    PlotConf["yTicks"] = range(-800, 1000, 200)
    PlotConf["yLim"] = [-800, 800]
    PlotConf["Marker"] = '.'
    PlotConf["MarkerSize"] = 0.5
    PlotConf["LineWidth"] = 1
    PlotConf["ColorBar"] = "gnuplot"
    PlotConf["ColorBarLabel"] = "Elevation [deg]"
    PlotConf["ColorBarMin"] = 0.
    PlotConf["ColorBarMax"] = 90.
    # data prep
    PlotConf["xData"] = {}
    PlotConf["yData"] = {}
    PlotConf["zData"] = {}
    Label = 0

    Filter = PreproObsData[PreproIdx["STATUS"]] == 1
    PlotConf["xData"][Label] = PreproObsData[PreproIdx["SOD"]][Filter] / GnssConstants.S_IN_H
    PlotConf["yData"][Label] = PreproObsData[PreproIdx["PHASE RATE"]][Filter]
    PlotConf["zData"][Label] = PreproObsData[PreproIdx["ELEV"]][Filter]

    PlotConf["Grid"] = True
    PlotConf["Legend"] = False
    PlotConf["DoubleAxis"] = False

    generatePlot(PlotConf)

def plotPhaseRateStep(PreproObsFile, PreproObsData):
    PlotConf = {}

    initPlot(PreproObsFile, PlotConf, "Phase Rate Step", "PHASE_RATE_STEP")

    PlotConf["Type"] = "Lines"
    PlotConf["FigSize"] = (10, 7)
    PlotConf["yLabel"] = "Phase Rate Step [m/s^2]"
    PlotConf["yTicks"] = np.arange(-0.05, 0.25, 0.05)
    PlotConf["yLim"] = [-0.05, 0.20]
    PlotConf["Marker"] = 'P'
    PlotConf["MarkerSize"] = 0.5
    PlotConf["LineWidth"] = 1
    PlotConf["ColorBar"] = "gnuplot"
    PlotConf["ColorBarLabel"] = "Elevation [deg]"
    PlotConf["ColorBarMin"] = 0.
    PlotConf["ColorBarMax"] = 90.
    # data prep
    PlotConf["xData"] = {}
    PlotConf["yData"] = {}
    PlotConf["zData"] = {}
    Label = 0

    Filter = PreproObsData[PreproIdx["STATUS"]] == 1
    PlotConf["xData"][Label] = PreproObsData[PreproIdx["SOD"]][Filter] / GnssConstants.S_IN_H
    PlotConf["yData"][Label] = PreproObsData[PreproIdx["PHASE ACC"]][Filter]
    PlotConf["zData"][Label] = PreproObsData[PreproIdx["ELEV"]][Filter]

    PlotConf["Grid"] = True
    PlotConf["Legend"] = False
    PlotConf["DoubleAxis"] = False

    generatePlot(PlotConf)

def plotVtecGradient(PreproObsFile, PreproObsData):
    PlotConf = {}

    initPlot(PreproObsFile, PlotConf, "VTEC Gradient", "VTEC_RATE")

    PlotConf["Type"] = "Lines"
    PlotConf["FigSize"] = (10, 7)
    PlotConf["yLabel"] = "VTEC Gradient [mm/s]"
    PlotConf["yTicks"] = range(-4, 5)
    PlotConf["yLim"] = [-4, 4]
    PlotConf["Marker"] = 'P'
    PlotConf["MarkerSize"] = 0.5
    PlotConf["LineWidth"] = 1
    PlotConf["ColorBar"] = "gnuplot"
    PlotConf["ColorBarLabel"] = "Elevation [deg]"
    PlotConf["ColorBarMin"] = 0.
    PlotConf["ColorBarMax"] = 90.
    # data prep
    PlotConf["xData"] = {}
    PlotConf["yData"] = {}
    PlotConf["zData"] = {}
    Label = 0

    Filter = PreproObsData[PreproIdx["STATUS"]] == 1
    PlotConf["xData"][Label] = PreproObsData[PreproIdx["SOD"]][Filter] / GnssConstants.S_IN_H
    PlotConf["yData"][Label] = PreproObsData[PreproIdx["VTEC RATE"]][Filter]
    PlotConf["zData"][Label] = PreproObsData[PreproIdx["ELEV"]][Filter]

    PlotConf["Grid"] = True
    PlotConf["Legend"] = False
    PlotConf["DoubleAxis"] = False

    generatePlot(PlotConf)

def plotAatr(PreproObsFile, PreproObsData):
    PlotConf = {}

    initPlot(PreproObsFile, PlotConf, "AATR", "AATR")

    PlotConf["Type"] = "Lines"
    PlotConf["FigSize"] = (10, 7)
    PlotConf["yLabel"] = "AATR [mm/s]"
    PlotConf["yTicks"] = range(-4, 5)
    PlotConf["yLim"] = [-4, 4]
    PlotConf["Marker"] = 'P'
    PlotConf["MarkerSize"] = 0.5
    PlotConf["LineWidth"] = 1
    PlotConf["ColorBar"] = "gnuplot"
    PlotConf["ColorBarLabel"] = "Elevation [deg]"
    PlotConf["ColorBarMin"] = 0.
    PlotConf["ColorBarMax"] = 90.
    # data prep
    PlotConf["xData"] = {}
    PlotConf["yData"] = {}
    PlotConf["zData"] = {}
    Label = 0

    Filter = PreproObsData[PreproIdx["STATUS"]] == 1
    PlotConf["xData"][Label] = PreproObsData[PreproIdx["SOD"]][Filter] / GnssConstants.S_IN_H
    PlotConf["yData"][Label] = PreproObsData[PreproIdx["iAATR"]][Filter]
    PlotConf["zData"][Label] = PreproObsData[PreproIdx["ELEV"]][Filter]

    PlotConf["Grid"] = True
    PlotConf["Legend"] = False
    PlotConf["DoubleAxis"] = False

    generatePlot(PlotConf)

def generatePreproPlots(PreproObsFile):

    # Satellite Visibility
    PreproObsData = read_csv(PreproObsFile, delim_whitespace=True, skiprows=1, header=None, usecols=[PreproIdx["SOD"], PreproIdx["PRN"], PreproIdx["ELEV"], PreproIdx["STATUS"]])
    print("Satellite Visibility")
    plotSatVisibility(PreproObsFile, PreproObsData)

    # Number of Satellites
    PreproObsData = read_csv(PreproObsFile, delim_whitespace=True, skiprows=1, header=None, usecols=[PreproIdx["SOD"], PreproIdx["STATUS"]])
    print("Number of Satellites")
    plotNumSats(PreproObsFile, PreproObsData)


    # Satellite C1 - C1Smoothed
    PreproObsData = read_csv(PreproObsFile, delim_whitespace=True, skiprows=1, header=None, usecols=[PreproIdx["SOD"], PreproIdx["STATUS"], PreproIdx["C1"], PreproIdx["C1SMOOTHED"],
                                      PreproIdx["S1"]])
    print("Satellite C1 - C1Smoothed")
    plotC1C1Smoothed(PreproObsFile, PreproObsData)

    # Satellite C1 - C1Smoothed vs Elevation
    PreproObsData = read_csv(PreproObsFile, delim_whitespace=True, skiprows=1, header=None, usecols=[PreproIdx["ELEV"], PreproIdx["STATUS"], PreproIdx["C1"], PreproIdx["C1SMOOTHED"],
                                      PreproIdx["S1"]])
    print("Satellite C1 - C1Smoothed vs Elevation")
    plotC1C1SmoothedvsElev(PreproObsFile, PreproObsData)

    # Satellite Rejection Flag
    PreproObsData = read_csv(PreproObsFile, delim_whitespace=True, skiprows=1, header=None, usecols=[PreproIdx["SOD"], PreproIdx["PRN"], PreproIdx["REJECT"]])
    print("Satellite Rejection Flag")
    plotRejectionFlags(PreproObsFile, PreproObsData)

    # Satellite Code Rate
    PreproObsData = read_csv(PreproObsFile, delim_whitespace=True, skiprows=1, header=None, usecols=[PreproIdx["SOD"], PreproIdx["STATUS"], PreproIdx["CODE RATE"], PreproIdx["ELEV"]])
    print("Satellite Code Rate")
    plotCodeRate(PreproObsFile, PreproObsData)

    # Satellite Code Rate Step
    PreproObsData = read_csv(PreproObsFile, delim_whitespace=True, skiprows=1, header=None, usecols=[PreproIdx["SOD"], PreproIdx["STATUS"], PreproIdx["CODE ACC"], PreproIdx["ELEV"]])
    print("Satellite Code Rate Step")
    plotCodeRateStep(PreproObsFile, PreproObsData)

    # Satellite Phase Rate
    PreproObsData = read_csv(PreproObsFile, delim_whitespace=True, skiprows=1, header=None, usecols=[PreproIdx["SOD"], PreproIdx["STATUS"], PreproIdx["PHASE RATE"],
                                      PreproIdx["ELEV"]])
    print("Satellite Phase Rate")
    plotPhaseRate(PreproObsFile, PreproObsData)

    # Satellite Phase Rate Step
    PreproObsData = read_csv(PreproObsFile, delim_whitespace=True, skiprows=1, header=None, usecols=[PreproIdx["SOD"], PreproIdx["STATUS"], PreproIdx["PHASE ACC"], PreproIdx["ELEV"]])
    print("Satellite Phase Rate Step")
    plotPhaseRateStep(PreproObsFile, PreproObsData)

    # Satellite VTEC Gradient
    PreproObsData = read_csv(PreproObsFile, delim_whitespace=True, skiprows=1, header=None, usecols=[PreproIdx["SOD"], PreproIdx["STATUS"], PreproIdx["VTEC RATE"], PreproIdx["ELEV"]])
    print("Satellite VTEC Gradient")
    plotVtecGradient(PreproObsFile, PreproObsData)

    # Satellite Instantaneus AATR
    PreproObsData = read_csv(PreproObsFile, delim_whitespace=True, skiprows=1, header=None, usecols=[PreproIdx["SOD"], PreproIdx["STATUS"], PreproIdx["iAATR"], PreproIdx["ELEV"]])
    print("Satellite Instantaneus AATR")
    plotAatr(PreproObsFile, PreproObsData)