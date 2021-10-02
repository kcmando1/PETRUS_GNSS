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
from COMMON.Iono import computeIonoMappingFunction
from InputOutput import RcvrIdx, SatIdx, LosIdx
from math import sin, sqrt, exp
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
                if SatInfo[SatLabel][SatIdx["UDREI"]] < 14:
                    if SatInfo[SatLabel][SatIdx["UDREI"]] < 12:
                        SatCorrInfo["Flag"] = 1
                    else:
                        SatCorrInfo["Flag"] = 2
                else:
                    SatCorrInfo["Flag"] = 0
                if SatCorrInfo["Flag"] == 1:
                    #Correction of XYZ POS of sats
                    SatCorrInfo["SatZ"] = SatInfo[SatLabel][SatIdx["SAT-Z"]]+SatInfo[SatLabel][SatIdx["LTC-Z"]]
                    SatCorrInfo["SatY"] = SatInfo[SatLabel][SatIdx["SAT-Y"]] + SatInfo[SatLabel][SatIdx["LTC-Y"]]
                    SatCorrInfo["SatX"] = SatInfo[SatLabel][SatIdx["SAT-X"]] + SatInfo[SatLabel][SatIdx["LTC-X"]]
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

                    if (SatInfo[SatLabel][SatIdx["RSS"]] == 0):
                        SatCorrInfo["SigmaFlt"] = ((SatInfo[SatLabel][SatIdx["SIGMAUDRE"]] *
                                                    SatInfo[SatLabel][SatIdx["DELTAUDRE"]]) +
                                                    SatInfo[SatLabel][SatIdx["EPS-FC"]] +
                                                    SatInfo[SatLabel][SatIdx["EPS-RRC"]] +
                                                    SatInfo[SatLabel][SatIdx["EPS-LTC"]] +
                                                    SatInfo[SatLabel][SatIdx["EPS-ER"]])

                    else:
                        # Compute root-sum-squared
                        SatCorrInfo["SigmaFlt"] = (np.sqrt(pow(
                            SatInfo[SatLabel][SatIdx["SIGMAUDRE"]] * SatInfo[SatLabel][SatIdx["DELTAUDRE"]],2)) +
                                                  pow(SatInfo[SatLabel][SatIdx["EPS-FC"]],2) +
                                                  pow(SatInfo[SatLabel][SatIdx["EPS-RRC"]],2) +
                                                  pow(SatInfo[SatLabel][SatIdx["EPS-LTC"]],2) +
                                                  pow(SatInfo[SatLabel][SatIdx["EPS-ER"]],2))
                    # --------------------#
                    # UISD and Sigma UIRE #
                    #                     #
                    #          N          #
                    #      v2-----v1      #
                    #      |       |      #
                    #    W |  IPP  | E    #
                    #      |       |      #
                    #      v3-----v4      #
                    #          S          #
                    # --------------------#
                    Lon1 = LosInfo[SatLabel][LosIdx["IGP_NE_LON"]]
                    Lat1 = LosInfo[SatLabel][LosIdx["IGP_NE_LAT"]]
                    Tau1 = LosInfo[SatLabel][LosIdx["GIVD_NE"]]
                    ETau1 = LosInfo[SatLabel][LosIdx["GIVE_NE"]]

                    Lon2 = LosInfo[SatLabel][LosIdx["IGP_NW_LON"]]
                    Lat2 = LosInfo[SatLabel][LosIdx["IGP_NW_LAT"]]
                    Tau2 = LosInfo[SatLabel][LosIdx["GIVD_NW"]]
                    ETau2 = LosInfo[SatLabel][LosIdx["GIVE_NW"]]

                    Lon3 = LosInfo[SatLabel][LosIdx["IGP_SW_LON"]]
                    Lat3 = LosInfo[SatLabel][LosIdx["IGP_SW_LAT"]]
                    Tau3 = LosInfo[SatLabel][LosIdx["GIVD_SW"]]
                    ETau3 = LosInfo[SatLabel][LosIdx["GIVE_SW"]]

                    Lon4 = LosInfo[SatLabel][LosIdx["IGP_SE_LON"]]
                    Lat4 = LosInfo[SatLabel][LosIdx["IGP_SE_LAT"]]
                    Tau4 = LosInfo[SatLabel][LosIdx["GIVD_SE"]]
                    ETau4 = LosInfo[SatLabel][LosIdx["GIVE_SE"]]

                    LatN = Lat1
                    LonW = Lon2
                    LatS = Lat3
                    LonE = Lon4

                    #SQ interpolation
                    if LosInfo[SatLabel][LosIdx["INTERP"]] == 0:
                        if abs(SatCorrInfo["IppLat"]) < 85:
                            Xpp = (SatCorrInfo["IppLon"] - LonW) / (LonE - LonW)
                            Ypp = (SatCorrInfo["IppLat"] - LatS) / (LatN - LatS)
                        else:
                            Ypp = (abs(SatCorrInfo["IppLat"]) - 85.0) / 10.0
                            Xpp = ((SatCorrInfo["IppLon"] - Lon3) / 90.0) * (1 - 2 * Ypp) + Ypp

                        R1 = Xpp * Ypp
                        R2 = (1 - Xpp) * Ypp
                        R3 = (1 - Xpp) * (1 - Ypp)
                        R4 = Xpp * (1 - Ypp)
                    # Tr interpolation no v1
                    else:
                        if abs(SatCorrInfo["IppLat"]) < 75:
                            Xpp = (SatCorrInfo["IppLon"] - LonW) / (LonE - LonW)
                            Ypp = (SatCorrInfo["IppLat"] - LatS) / (LatN - LatS)
                        else:
                            Ypp = (abs(SatCorrInfo["IppLat"]) - 85.0) / 10.0
                            Xpp = ((SatCorrInfo["IppLon"] - Lon3) / 90.0) * (1 - 2 * Ypp) + Ypp

                        R1 = Ypp
                        R2 = 1 - Xpp - Ypp
                        R3 = Xpp
                        R4 = 0
                        # Tr interpolation no v1
                        if LosInfo[SatLabel][LosIdx["INTERP"]] == 1:
                            Tau1 = Tau2
                            Tau2 = Tau3
                            Tau3 = Tau4

                            ETau1 = ETau2
                            ETau2 = ETau3
                            ETau3 = ETau4
                        # Tr interpolation no v2
                        elif LosInfo[SatLabel][LosIdx["INTERP"]] == 2:
                            Tau1 = Tau3
                            Tau2 = Tau4
                            Tau3 = Tau1

                            ETau1 = ETau3
                            ETau2 = ETau4
                            ETau3 = ETau1

                        # Tr interpolation no v3
                        elif LosInfo[SatLabel][LosIdx["INTERP"]] == 3:
                            Tau1 = Tau4
                            Tau2 = Tau1
                            Tau3 = Tau2

                            ETau1 = ETau4
                            ETau2 = ETau1
                            ETau3 = ETau2
                        # Tr interpolation no v4
                        elif LosInfo[SatLabel][LosIdx["INTERP"]] == 4:
                            pass
                        # No interpolate
                        else:
                            pass

                    Taupp = (R1 * Tau1) + (R2 * Tau2) + (R3 * Tau3) + (R4 * Tau4)
                    #UIVE
                    ETaupp = sqrt((R1 * pow(ETau1,2)) + (R2 * pow(ETau2,2)) + (R3 * pow(ETau3,2)) + (R4 * pow(ETau4,2)))
                    #Mapping function
                    Fpp = computeIonoMappingFunction(SatCorrInfo["Elevation"])
                    #UISD
                    SatCorrInfo["Uisd"] = round(Fpp * Taupp, 4)
                    #Sigma UIRE
                    SatCorrInfo["SigmaUire"] = round(Fpp * ETaupp, 4)
                    #Sigma tropo
                    STVE = 0.12
                    Mpp = 1.001 / sqrt(pow(0.002001 + sin(np.deg2rad(SatCorrInfo["Elevation"])), 2))
                    SatCorrInfo["SigmaTropo"] = STVE * Mpp
                    #sigma multipath
                    if SatCorrInfo["Elevation"] > 2:
                        SatCorrInfo["SigmaMultipath"] = 0.13 + 0.53 * exp(-SatCorrInfo["Elevation"] / 10.0)
                    else:
                        SatCorrInfo["SigmaMultipath"] = 0
                    #sigma noise
                    if SatCorrInfo["Elevation"] < float(Conf["ELEV_NOISE_TH"]):
                        SatCorrInfo["SigmaNoiseDiv"] = 0.36
                    else:
                        SatCorrInfo["SigmaNoiseDiv"] = 0.15
                    #sigma airborne
                    SatCorrInfo["SigmaAirborne"] = sqrt(pow(SatCorrInfo["SigmaMultipath"],2) + pow(SatCorrInfo["SigmaNoiseDiv"],2))

                    SatCorrInfo["SigmaUere"] = sqrt(
                        pow(SatCorrInfo["SigmaFlt"], 2) + pow(SatCorrInfo["SigmaUire"], 2) + pow(
                            SatCorrInfo["SigmaTropo"], 2) + pow(SatCorrInfo["SigmaAirborne"], 2))

                    # Corrected Measurements from previous information
                    SatCorrInfo["CorrPsr"] = SatCorrInfo["SatClk"] + SatPrepro["SmoothC1"] - SatCorrInfo["Std"] - \
                                             SatCorrInfo["Uisd"]
                    # Compute Geometrical Range
                    SatCoord = np.array([SatCorrInfo["SatZ"], SatCorrInfo["SatY"], SatCorrInfo["SatX"]])
                    RCVRCoord = np.array(Rcvr[RcvrIdx["XYZ"]])
                    GeoRangeXYZ = np.subtract(SatCoord, RCVRCoord)
                    SatCorrInfo["GeomRange"] = np.linalg.norm(GeoRangeXYZ)
                    # Compute Geometrical Range
                    SatCorrInfo["PsrResidual"] = SatCorrInfo["CorrPsr"] - SatCorrInfo["GeomRange"]

                    # Compute residuals sum
                    Weight = 1 / pow(SatCorrInfo["SigmaUere"], 2)
                    ResSum = ResSum + (Weight * SatCorrInfo["PsrResidual"])
                    ResN = ResN + Weight

                    # Compute ENT-GPS offset
                    LTCxyz = np.array([SatInfo[SatLabel][SatIdx["LTC-X"]], (SatInfo[SatLabel][SatIdx["LTC-Y"]]),
                                       (SatInfo[SatLabel][SatIdx["LTC-Z"]])])
                    UL = GeoRangeXYZ / SatCorrInfo["GeomRange"]
                    EntGpsSum += np.dot(LTCxyz, UL) - (
                                SatInfo[SatLabel][SatIdx["FC"]] + SatInfo[SatLabel][SatIdx["LTC-B"]])
                    EntGpsN = EntGpsN + 1
            # Prepare output for the satellite
            CorrInfo[SatLabel] = SatCorrInfo
        # End of if(SatPrepro["Status"] == 1):
    # End of for SatLabel, SatPrepro in PreproObsInfo.items():
    for SatLabel in CorrInfo:
        if EntGpsN > 0:
            # Receiver clock first guess
            CorrInfo[SatLabel]["RcvrClk"] = ResSum / ResN
            CorrInfo[SatLabel]["PsrResidual"] = CorrInfo[SatLabel]["PsrResidual"] - CorrInfo[SatLabel]["RcvrClk"]
            CorrInfo[SatLabel]["EntGps"] = EntGpsSum / EntGpsN

    return CorrInfo
#END CODE HERE

