#!/usr/bin/env python

########################################################################
# PETRUS/SRC/Corrections.py:
# This is the Corrections Module of PETRUS tool
#
#  Project:        PETRUS
#  File:           Corrections.py
#  Date(YY/MM/DD): 16/02/21
#
#   Author: GNSS Academy
#   Copyright 2021 GNSS Academy
#
# -----------------------------------------------------------------
# Date       | Author             | Action
# -----------------------------------------------------------------
#
########################################################################

# Import External and Internal functions and Libraries
#----------------------------------------------------------------------
import sys, os
# Add path to find all modules
Common = os.path.dirname(os.path.dirname(
    os.path.abspath(sys.argv[0]))) + '/COMMON'
sys.path.insert(0, Common)
from collections import OrderedDict
from COMMON import GnssConstants as Const
from InputOutput import RcvrIdx, SatIdx, LosIdx
from math import sqrt
import numpy as np


def ammendator(raw):
    flag = 0
    fAmmendment = {}

    for i in raw:
        fAmmendment[i] = []
        for j in raw[i]:
            try:
                if flag == 1:
                    a = j
                    flag = 0
                a = float(j)
            except:
                a = j
                flag = 1
            fAmmendment[i].append(a)
    return fAmmendment


def runCorrectMeas(Conf, Rcvr, PreproObsInfo, SatInfo, LosInfo):

    # Purpose: correct GNSS preprocessed measurements and compute
    #          pseudo range residuals

    #          More in detail, this function handles the following:
    #          tasks:

    #             *  Correct the satellite navigation position and clock using EGNOS Fast-Long-Term (FLT) corrections: FC and LTC.
    #             *  Estimate the Slant Ionospheric Delay (UISD) using MOPS guidelines interpolation criteria for IGP Selection
    #             *  Estimate the Slant Troposphere delay (STD) using MOPS model (ZTD) and its mapping function. 
    #             *  Correct the Pre-processed measurements from Geometrical Range, Satellite clock, ionosphere and troposphere. 
    #             *  Build the Corrected Measurements and Measurement Residuals
    #             *  Estimate all Range level Sigmas to build the Sigma UERE:
    #                   -  Estimate the SigmaUIRE from MT26 information
    #                   -  Estimate the SigmaFLT from UDRE and MT28 
    #                   -  Estimate the SigmaTRO budget in line with MOPS.
    #                   -  Estimate the SigmaAirborne budget in line with MOPS 

    #             *  Estimate the Sigma UERE budget in line with MOPS


    # Parameters
    # ==========
    # Conf: dict
    #         Configuration dictionary
    # Rcvr: list
    #         Receiver information: position, masking angle...
    # PreproObsInfo: dict
    #         Preprocessed observations for current epoch per sat
    #         PreproObsInfo["G01"]["C1"]
    # SatInfo: dict
    #         dictionary containing the split lines of the SAT file
    #         SatInfo["G01"][1] is the second field of the line
    #         containing G01 info
    # LosInfo: dict
    #         dictionary containing the split lines of the LOS file
    #         SatInfo["G01"][1] is the second field of the line
    #         containing G01 info

    # Returns
    # =======
    # CorrInfo: dict
    #         Corrected measurements for current epoch per sat
    #         CorrInfo["G01"]["CorrectedPsr"]

    # Initialize output
    CorrInfo = OrderedDict({})
    #ammendmentator, convert to float all fields of SAT and LOS except text to float not write every damn field to float

    SatInfo=ammendator(SatInfo)
    LosInfo=ammendator(LosInfo)

    # Initialize some values
    ResSum = 0.0
    ResN = 0
    EntGpsSum = 0.0
    EntGpsN = 0

    # Loop over satellites
    for SatLabel, SatPrepro in PreproObsInfo.items():
        # If satellite is in convergence
        if(SatPrepro["Status"] == 1):
            # Initialize output info
            SatCorrInfo = {
                "Sod": 0.0,             # Second of day
                "Doy": 0,               # Day of year
                "Elevation": 0.0,       # Elevation
                "Azimuth": 0.0,         # Azimuth
                "IppLon": 0.0,          # IPP Longitude
                "IppLat": 0.0,          # IPP Latitude
                "Flag": 1,              # 0: Not Used 1: Used for PA 2: Used for NPA
                "SatX": 0.0,            # X-Component of the Satellite Position 
                                        # corrected with SBAS LTC
                "SatY": 0.0,            # Y-Component of the Satellite Position 
                                        # corrected with SBAS LTC
                "SatZ": 0.0,            # Z-Component of the Satellite Position 
                                        # corrected with SBAS LTC
                "SatClk": 0.0,          # Satellite Clock corrected with SBAS FLT
                "Uisd": 0.0,            # User Ionospheric Slant Delay
                "Std": 0.0,             # Slant Tropospheric Delay
                "CorrPsr": 0.0,         # Pseudo Range corrected from delays
                "GeomRange": 0.0,       # Geometrical Range (distance between Satellite 
                                        # Position and Receiver Reference Position)
                "PsrResidual": 0.0,     # Pseudo Range Residual
                "RcvrClk": 0.0,         # Receiver Clock estimation
                "SigmaFlt": 0,          # Sigma of the residual error associated to the 
                                        # fast and long-term correction (FLT)
                "SigmaUire": 0,         # User Ionospheric Range Error Sigma
                "SigmaTropo": 0,        # Sigma of the Tropospheric error 
                "SigmaAirborne": 0.0,   # Sigma Airborne Error
                "SigmaNoiseDiv": 0.0,   # Sigma of the receiver noise + divergence
                "SigmaMultipath": 0.0,  # Sigma of the receiver multipath
                "SigmaUere": 0.0,       # Sigma User Equivalent Range Error (Sigma of 
                                        # the total residual error associated to the 
                                        # satellite)
                "EntGps": 0.0,          # ENT to GPS Offset

            } # End of SatCorrInfo

            # Prepare outputs
            # Get SoD
            SatCorrInfo["Sod"] = SatPrepro["Sod"]
            # Get DoY
            SatCorrInfo["Doy"] = SatPrepro["Doy"]
            # Get Elevation
            SatCorrInfo["Elevation"] = SatPrepro["Elevation"]
            # Get Azimuth
            SatCorrInfo["Azimuth"] = SatPrepro["Azimuth"]

            # If SBAS information is available for current satellite
            if (SatLabel in SatInfo) and (SatLabel in LosInfo):
                # Get IPP Longitude
                SatCorrInfo["IppLon"] = float(LosInfo[SatLabel][LosIdx["IPPLON"]])
                # Get IPP Latitude
                SatCorrInfo["IppLat"] = float(LosInfo[SatLabel][LosIdx["IPPLAT"]])
            #CODE HERE
            #REQ 010
            if (SatLabel in SatInfo):#Don't ask needs to be here for the code to work
                if (SatInfo[SatLabel][SatIdx["UDREI"]] < 12):
                    #Correction of XYZ POS of sats
                    SatCorrInfo["SatZ"] = SatInfo[SatLabel][SatIdx["SAT-Z"]]+SatInfo[SatLabel][SatIdx["LTC-Z"]]
                    SatCorrInfo["SatZ"] = SatInfo[SatLabel][SatIdx["SAT-Y"]] + SatInfo[SatLabel][SatIdx["LTC-Y"]]
                    SatCorrInfo["SatZ"] = SatInfo[SatLabel][SatIdx["SAT-X"]] + SatInfo[SatLabel][SatIdx["LTC-X"]]
                    #DTR corr
                    dtr = -2 * sqrt(pow(SatInfo[SatLabel][SatIdx["SAT-X"]],2) +
                                    pow(SatInfo[SatLabel][SatIdx["SAT-Y"]],2) +
                                    pow(SatInfo[SatLabel][SatIdx["SAT-Z"]],2)) * \
                               sqrt(pow(SatInfo[SatLabel][SatIdx["VEL-X"]],2) +
                                    pow(SatInfo[SatLabel][SatIdx["VEL-Y"]],2) +
                                    pow(SatInfo[SatLabel][SatIdx["VEL-Z"]],2)) / Const.SPEED_OF_LIGHT
                    #CLK corr
                    SatCorrInfo["SatClk"] = (SatInfo[SatLabel][SatIdx["SAT-CLK"]] + dtr
                                            - SatInfo[SatLabel][SatIdx["TGD"]]
                                            + SatInfo[SatLabel][SatIdx["FC"]]
                                            + SatInfo[SatLabel][SatIdx["LTC-B"]])


            #END CODE HERE

            # Prepare output for the satellite
            CorrInfo[SatLabel] = SatCorrInfo

        # End of if(SatPrepro["Status"] == 1):

    # End of for SatLabel, SatPrepro in PreproObsInfo.items():

    return CorrInfo
