#!/usr/bin/env python

########################################################################
# Petrus.py:
# This is the Main Module of PETRUS tool
#
#  Project:        PETRUS
#  File:           Petrus.py
#  Date(YY/MM/DD): 01/02/21
#
#   Author: GNSS Academy
#   Copyright 2021 GNSS Academy
#
# -----------------------------------------------------------------
# Date       | Author             | Action
# -----------------------------------------------------------------
#
# Usage:
#   Petrus.py $SCEN_PATH
########################################################################

import sys, os

# Update Path to reach COMMON
Common = os.path.dirname(
    os.path.abspath(sys.argv[0])) + '/COMMON'
sys.path.insert(0, Common)

# Import External and Internal functions and Libraries
#----------------------------------------------------------------------
from collections import OrderedDict
from yaml import dump
from COMMON import GnssConstants as Const
from InputOutput import readConf
from InputOutput import processConf
from InputOutput import readRcvr
from InputOutput import createOutputFile
from InputOutput import openInputFile
from InputOutput import readObsEpoch
from InputOutput import readCorrectInputs
from InputOutput import generatePreproFile
# from InputOutput import generateCorrFile
from InputOutput import PreproHdr, CorrHdr
from InputOutput import CSNEPOCHS
from InputOutput import ObsIdx
from Preprocessing import runPreProcMeas
# from PreprocessingPlots import generatePreproPlots
# from CorrectionsPlots import generateCorrPlots
from Corrections import runCorrectMeas
from COMMON.Dates import convertJulianDay2YearMonthDay
from COMMON.Dates import convertYearMonthDay2Doy

#----------------------------------------------------------------------
# INTERNAL FUNCTIONS
#----------------------------------------------------------------------

def displayUsage():
    sys.stderr.write("ERROR: Please provide path to SCENARIO as a unique argument\n")

#######################################################
# MAIN BODY
#######################################################

# Check InputOutput Arguments
if len(sys.argv) != 2:
    displayUsage()
    sys.exit()

# Extract the arguments
Scen = sys.argv[1]

# Select the Configuratiun file name
CfgFile = Scen + '/CFG/petrus.cfg'

# Read conf file
Conf = readConf(CfgFile)
# print(dump(Conf))

# Process Configuration Parameters
Conf = processConf(Conf)

# Select the RCVR Positions file name
RcvrFile = Scen + '/INP/RCVR/' + Conf["RCVR_FILE"]

# Read RCVR Positions file
RcvrInfo = readRcvr(RcvrFile)

# Print header
print( '------------------------------------')
print( '--> RUNNING PETRUS:')
print( '------------------------------------')

# Loop over RCVRs
#-----------------------------------------------------------------------
for Rcvr in RcvrInfo.keys():
    # Display Message
    print( '\n***-----------------------------***')
    print( '*** Processing receiver: ' + Rcvr + '   ***')
    print( '***-----------------------------***')

    # Loop over Julian Days in simulation
    #-----------------------------------------------------------------------
    for Jd in range(Conf["INI_DATE_JD"], Conf["END_DATE_JD"] + 1):
        # Compute Year, Month and Day in order to build input file name
        Year, Month, Day = convertJulianDay2YearMonthDay(Jd)
        
        # Compute the Day of Year (DoY)
        Doy = convertYearMonthDay2Doy(Year, Month, Day)

        # Display Message
        print( '\n*** Processing Day of Year: ' + str(Doy) + ' ... ***')

        # Define the full path and name to the OBS INFO file to read
        ObsFile = Scen + \
            '/INP/OBS/' + "OBS_%s_Y%02dD%03d.dat" % \
                (Rcvr, Year % 100, Doy)

        # Display Message
        print("INFO: Reading file: %s..." %
        ObsFile)

        # If Preprocessing outputs are activated
        if Conf["PREPRO_OUT"] == 1:
            # Define the full path and name to the output PREPRO OBS file
            PreproObsFile = Scen + \
                '/OUT/PPVE/' + "PREPRO_OBS_%s_Y%02dD%03d.dat" % \
                    (Rcvr, Year % 100, Doy)

            # Create output file
            fpreprobs = createOutputFile(PreproObsFile, PreproHdr)

        # If Corrected outputs are activated
        if Conf["CORR_OUT"] == 1:
            # Define the full path and name to the output CORR file
            CorrFile = Scen + \
                '/OUT/CORR/' + "CORR_%s_Y%02dD%03d.dat" % \
                    (Rcvr, Year % 100, Doy)

            # Create output file
            fcorr = createOutputFile(CorrFile, CorrHdr)

        # Define the full path and name to the SAT file to read and open the file
        SatFile = Scen + \
            '/OUT/SAT/' + "SAT_%s_Y%02dD%03d.dat" % \
                (Rcvr, Year % 100, Doy)
        fsat = openInputFile(SatFile)

        # Define the full path and name to the LOS file to read
        LosFile = Scen + \
            '/OUT/LOS/' + "LOS_%s_Y%02dD%03d.dat" % \
                (Rcvr, Year % 100, Doy)
        flos = openInputFile(LosFile)

        # Initialize Variables
        EndOfFile = False
        ObsInfo = [None]
        PrevPreproObsInfo = {}
        for prn in range(1, Const.MAX_NUM_SATS_CONSTEL + 1):
            PrevPreproObsInfo["G%02d" % prn] = {
            "L1_n_1": 0.0,           # t-1 Carrier Phase in L1
            "L1_n_2": 0.0,           # t-2 Carrier Phase in L1
            "L1_n_3": 0.0,           # t-3 Carrier Phase in L1
            "t_n_1": 0.0,            # t-1 epoch
            "t_n_2": 0.0,            # t-2 epoch
            "t_n_3": 0.0,            # t-3 epoch
            "CsBuff": [0] * \
int(Conf["MIN_NCS_TH"][CSNEPOCHS]),  # Number of consecutive epochs for CS
            "CsIdx": 0,              # Index of CS detector buffer
            "ResetHatchFilter": 1,   # Flag to reset Hatch filter
            "Ksmooth": 0,            # Hatch filter K
            "PrevEpoch": 86400,      # Previous SoD
            "PrevL1": 0.0,           # Previous L1
            "PrevSmoothC1": 0.0,     # Previous Smoothed C1
            "PrevRangeRateL1": 0.0,  # Previous Code Rate
            "PrevPhaseRateL1": 0.0,  # Previous Phase Rate
            "PrevGeomFree": 0.0,     # Previous Geometry-Free Observable
            "PrevGeomFreeEpoch": 0.0,# Previous Geometry-Free Observable
            "PrevRej": 0,            # Previous Rejection flag
                                     # ...
        } # End of SatPreproObsInfo
        SodInputs = -1

        # Open OBS file
        with open(ObsFile, 'r') as fobs:
            # Read header line of OBS file
            fobs.readline()

            # LOOP over all Epochs of UPOS file
            # ----------------------------------------------------------
            while not EndOfFile:

                # If ObsInfo is not empty
                if ObsInfo != []:

                    # Read Only One Epoch
                    ObsInfo = readObsEpoch(fobs)

                    # If ObsInfo is empty, exit loop
                    if ObsInfo == []:
                        break

                    # Preprocess OBS measurements
                    # ----------------------------------------------------------
                    PreproObsInfo = runPreProcMeas(Conf, RcvrInfo[Rcvr], ObsInfo, PrevPreproObsInfo)

                    # If PREPRO outputs are requested
                    if Conf["PREPRO_OUT"] == 1:
                        # Generate output file
                        generatePreproFile(fpreprobs, PreproObsInfo)

                    # Get SoD
                    Sod = int(float(ObsInfo[0][ObsIdx["SOD"]]))

                    # The rest of te analyses are executed every configured sampling rate
                    if(Sod % Conf["SAMPLING_RATE"] == 0):
                        # Check if SoD have not already been read
                        if(SodInputs < Sod):
                            # Read SAT and LOS info
                            SatInfo, LosInfo, SodInputs = readCorrectInputs(fsat, flos, Sod)

                        # If data is not available, continue to next epoch
                        if(SatInfo == [] or LosInfo == []):
                            continue

                        # Correct measurements and estimate the variances with SBAS information
                        # ----------------------------------------------------------
                        CorrInfo = runCorrectMeas(Conf, RcvrInfo[Rcvr], PreproObsInfo, SatInfo, LosInfo)

                        # If CORR outputs are requested
                        # if Conf["CORR_OUT"] == 1:
                            # Generate output file
                            # generateCorrFile(fcorr, CorrInfo)

                # end if ObsInfo != []:
                else:
                    EndOfFile = True

                #End of if ObsInfo != []:
                
            # End of while not EndOfFile:
    
        # End of with open(ObsFile, 'r') as f:

        # If PREPRO outputs are requested
        if Conf["PREPRO_OUT"] == 1:
            # Close PREPRO output file
            fpreprobs.close()

            # Display Message
            print("INFO: Reading file: %s and generating PREPRO figures..." %
            PreproObsFile)

            # Generate Preprocessing plots
            generatePreproPlots(PreproObsFile)

        # If CORR outputs are requested
        if Conf["CORR_OUT"] == 1:
            # Close CORR output file
            fcorr.close()

            # # Display Message
            # print("INFO: Reading file: %s and generating CORR figures..." %
            # CorrFile)

            # # Generate CORR plots
            # generateCorrPlots(CorrFile, SatFile, RcvrInfo[Rcvr])

        # Close input files
        fsat.close()
        flos.close()

    # End of JD loop

# End of RCVR loop

print( '\n------------------------------------')
print( '--> END OF PETRUS ANALYSIS')
print( '------------------------------------')

#######################################################
# End of Petrus.py
#######################################################
