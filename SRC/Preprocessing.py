#!/usr/bin/env python

########################################################################
# PETRUS/SRC/Preprocessing.py:
# This is the Preprocessing Module of PETRUS tool
#
#  Project:        PETRUS
#  File:           Preprocessing.py
#  Date(YY/MM/DD): 01/02/21
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
from InputOutput import RcvrIdx, ObsIdx, REJECTION_CAUSE
from InputOutput import FLAG, VALUE, TH, CSNEPOCHS
import numpy as np
from COMMON.Iono import computeIonoMappingFunction

# Preprocessing internal functions
#-----------------------------------------------------------------------


def runPreProcMeas(Conf, Rcvr, ObsInfo, PrevPreproObsInfo):
    
    # Purpose: preprocess GNSS raw measurements from OBS file
    #          and generate PREPRO OBS file with the cleaned,
    #          smoothed measurements

    #          More in detail, this function handles:
             
    #          * Measurements cleaning and validation and exclusion due to different 
    #          criteria as follows:
    #             - Minimum Masking angle
    #             - Maximum Number of channels
    #             - Minimum Carrier-To-Noise Ratio (CN0)
    #             - Pseudo-Range Output of Range 
    #             - Maximum Pseudo-Range Step
    #             - Maximum Pseudo-Range Rate
    #             - Maximum Carrier Phase Increase
    #             - Maximum Carrier Phase Increase Rate
    #             - Data Gaps checks and handling 
    #             - Cycle Slips detection

    #         * Filtering/Smoothing of Code-Phase Measurements with a Hatch filter 

    # Parameters
    # ==========
    # Conf: dict
    #         Configuration dictionary
    # Rcvr: list
    #         Receiver information: position, masking angle...
    # ObsInfo: list
    #         OBS info for current epoch
    #         ObsInfo[1][1] is the second field of the 
    #         second satellite
    # PrevPreproObsInfo: dict
    #         Preprocessed observations for previous epoch per sat
    #         PrevPreproObsInfo["G01"]["C1"]

    # Returns
    # =======
    # PreproObsInfo: dict
    #         Preprocessed observations for current epoch per sat
    #         PreproObsInfo["G01"]["C1"]
    

    # Initialize output
    PreproObsInfo = OrderedDict({})

    # Loop over satellites
    for SatObs in ObsInfo:
        # Initialize output info
        SatPreproObsInfo = {
            "Sod": 0.0,             # Second of day
            "Doy": 0,               # Day of year
            "Elevation": 0.0,       # Elevation
            "Azimuth": 0.0,         # Azimuth
            "C1": 0.0,              # GPS L1C/A pseudorange
            "P1": 0.0,              # GPS L1P pseudorange
            "L1": 0.0,              # GPS L1 carrier phase (in cycles)
            "L1Meters": 0.0,        # GPS L1 carrier phase (in m)
            "S1": 0.0,              # GPS L1C/A C/No
            "P2": 0.0,              # GPS L2P pseudorange
            "L2": 0.0,              # GPS L2 carrier phase 
            "S2": 0.0,              # GPS L2 C/No
            "SmoothC1": 0.0,        # Smoothed L1CA 
            "GeomFree": 0.0,        # Geom-free in Phases
            "GeomFreePrev": 0.0,    # t-1 Geom-free in Phases
            "ValidL1": 1,          # L1 Measurement Status
            "RejectionCause": 0,    # Cause of rejection flag
            "StatusL2": 0,          # L2 Measurement Status
            "Status": 0,            # L1 Smoothing status
            "RangeRateL1": 0.0,     # L1 Code Rate
            "RangeRateStepL1": 0.0, # L1 Code Rate Step
            "PhaseRateL1": 0.0,     # L1 Phase Rate
            "PhaseRateStepL1": 0.0, # L1 Phase Rate Step
            "VtecRate": 0.0,        # VTEC Rate
            "iAATR": 0.0,           # Instantaneous AATR
            "Mpp": 0.0,             # Iono Mapping

        } # End of SatPreproObsInfo

        # Get satellite label
        SatLabel = SatObs[ObsIdx["CONST"]] + "%02d" % int(SatObs[ObsIdx["PRN"]])

        # Prepare outputs
        # Get SoD
        SatPreproObsInfo["Sod"] = float(SatObs[ObsIdx["SOD"]])
        # Get DoY
        SatPreproObsInfo["Doy"] = int(SatObs[ObsIdx["DOY"]])
        # Get Elevation
        SatPreproObsInfo["Elevation"] = float(SatObs[ObsIdx["ELEV"]])
        # Get Azimuth
        SatPreproObsInfo["Azimuth"] = float(SatObs[ObsIdx["AZIM"]])
        # Get C1
        SatPreproObsInfo["C1"] = float(SatObs[ObsIdx["C1"]])
        # Get L1 in cycles and in m
        SatPreproObsInfo["L1"] = float(SatObs[ObsIdx["L1"]])
        SatPreproObsInfo["L1Meters"] = float(SatObs[ObsIdx["L1"]]) * Const.GPS_L1_WAVE
        # Get S1
        SatPreproObsInfo["S1"] = float(SatObs[ObsIdx["S1"]])
        # Get L2
        SatPreproObsInfo["L2"] = float(SatObs[ObsIdx["L2"]])

        # Prepare output for the satellite
        PreproObsInfo[SatLabel] = SatPreproObsInfo

    # Limit the satellites to the Number of Channels
    # ----------------------------------------------------------
    # Initialize Elevation cut due to number of channels limitation
    ChannelsElevation = 0.0

    # Get difference between number of satellites and number of channels
    NChannelsRejections = len(PreproObsInfo) - int(Conf["NCHANNELS_GPS"])

    # If some satellites shall be rejected
    if NChannelsRejections > 0:
        # Initialize Elevation list for number of channels limitation
        ElevationList = []

        # Loop over satellites to build elevation list
        for SatLabel, PreproObs in PreproObsInfo.items():
            ElevationList.append(PreproObs["Elevation"])

        # Sort elevation list
        ElevationList = sorted(ElevationList)

        # Get Elevation cut
        ChannelsElevation = ElevationList[NChannelsRejections]

    # Loop over satellites
    for SatLabel, PreproObs in PreproObsInfo.items():
        # If satellite shall be rejected due to number of channels limitation
        # --------------------------------------------------------------------------------------------------------------------
        if PreproObs["Elevation"] < ChannelsElevation:
            # Lower status and indicate the rejection cause
            PreproObs["ValidL1"] = 0
            PreproObs["RejectionCause"] = REJECTION_CAUSE["NCHANNELS_GPS"]
            
            continue

        # If satellite shall be rejected due to mask angle
        # ----------------------------------------------------------
        if PreproObs["Elevation"] < Rcvr[RcvrIdx["MASK"]]:
            # Lower status and indicate the rejection cause
            PreproObs["ValidL1"] = 0
            PreproObs["RejectionCause"] = REJECTION_CAUSE["MASKANGLE"]

            # Store previous Rejection flag
            PrevPreproObsInfo[SatLabel]["PrevRej"] = REJECTION_CAUSE["MASKANGLE"]

            continue

        # If satellite shall be rejected due to C/N0 (only if activated in conf)
        # --------------------------------------------------------------------------------------------------------------------
        if (Conf["MIN_CNR"][FLAG] == 1) and (PreproObs["S1"] < float(Conf["MIN_CNR"][VALUE])):
            # Lower status and indicate the rejection cause
            PreproObs["ValidL1"] = 0
            PreproObs["RejectionCause"] = REJECTION_CAUSE["MIN_CNR"]

            # Store previous Rejection flag
            PrevPreproObsInfo[SatLabel]["PrevRej"] = REJECTION_CAUSE["MIN_CNR"]

            continue

        # If satellite shall be rejected due to Pseudorange Out-of-range (only if activated in conf)
        # --------------------------------------------------------------------------------------------------------------------
        if (Conf["MAX_PSR_OUTRNG"][FLAG] == 1) and (PreproObs["C1"] > float(Conf["MAX_PSR_OUTRNG"][VALUE])):
            # Lower status and indicate the rejection cause
            PreproObs["ValidL1"] = 0
            PreproObs["RejectionCause"] = REJECTION_CAUSE["MAX_PSR_OUTRNG"]
            
            continue

        # Get epoch
        Epoch = PreproObs["Sod"]

        # Check data gaps
        # ----------------------------------------------------------
        # Compute gap between previous and current observation
        DeltaT = Epoch - PrevPreproObsInfo[SatLabel]["PrevEpoch"]
        # If there is a gap
        if (DeltaT > Conf["SAMPLING_RATE"]):
            # Increment gap counter
            PrevPreproObsInfo[SatLabel]["GapCounter"] = DeltaT

            # If the length of the gap is larger than the allowed value
            if PrevPreproObsInfo[SatLabel]["GapCounter"] > \
                Conf["HATCH_GAP_TH"]:
                # Raise Smoothing filter reset flag
                PrevPreproObsInfo[SatLabel]["ResetHatchFilter"] = 1

                # Reset gap counter
                PrevPreproObsInfo[SatLabel]["GapCounter"] = 0
                
                # Indicate the rejection cause
                # PreproObs["ValidL1"] = 0
                if(PrevPreproObsInfo[SatLabel]["PrevRej"] == 0):
                    PreproObs["RejectionCause"] = REJECTION_CAUSE["DATA_GAP"]

        else:
            # Reset gap counter
            PrevPreproObsInfo[SatLabel]["GapCounter"] = 0

        # Cycle Slips (CS) detection
        # ----------------------------------------------------------
        # If CS detection is activated
        if (not PrevPreproObsInfo[SatLabel]["ResetHatchFilter"]) and \
            (Conf["MIN_NCS_TH"][FLAG] == 1):
            # Get current and previous phase measurements 
            CP_n = PreproObs["L1"]
            CP_n_1 = PrevPreproObsInfo[SatLabel]["L1_n_1"]
            CP_n_2 = PrevPreproObsInfo[SatLabel]["L1_n_2"]
            CP_n_3 = PrevPreproObsInfo[SatLabel]["L1_n_3"]

            # Get Previous measurements' epochs deltas
            dt1 = Epoch - PrevPreproObsInfo[SatLabel]["t_n_1"]
            dt2 = PrevPreproObsInfo[SatLabel]["t_n_1"] - PrevPreproObsInfo[SatLabel]["t_n_2"]
            dt3 = PrevPreproObsInfo[SatLabel]["t_n_2"] - PrevPreproObsInfo[SatLabel]["t_n_3"]

            # If t-3 is available
            if PrevPreproObsInfo[SatLabel]["t_n_3"] > 0:
                # Compute residual coefficients
                l1 = float((dt1+dt2)*(dt1+dt2+dt3))/(dt2*(dt2+dt3))
                l2 = float(-dt1*(dt1+dt2+dt3))/(dt2*dt3)
                l3 = float(dt1*(dt1+dt2))/((dt2+dt3)*dt3)

                # Compute propagated L1
                CP_prop = l1*CP_n_1 + l2*CP_n_2 + l3*CP_n_3
                
                # Compute residuals
                CsResidual = abs(CP_n-CP_prop)

                # print("CSRESIDUAL %5d %5s %15.3f %15.3f %10.4lf " % (Epoch, SatLabel, CP_n, CP_prop, CsResidual))

                # Compute CS flag
                CsFlag = CsResidual > float(Conf["MIN_NCS_TH"][TH])
                
                # Update CS detector buffer
                PrevPreproObsInfo[SatLabel]["CsBuff"][PrevPreproObsInfo[SatLabel]["CsIdx"]] = CsFlag

                # If residual is above the threshold
                if CsFlag == True:
                    # Update L1
                    # PreproObs["L1"] = CP_prop
                    # CP_n = CP_prop

                    # Invalid measurement
                    PreproObs["ValidL1"] = 0

                    # A CS is declared if it was detected Conf["MIN_NCS_TH"][CSNEPOCHS]
                    # consecutive times (recommended value is 3)
                    if np.sum(PrevPreproObsInfo[SatLabel]["CsBuff"]) == Conf["MIN_NCS_TH"][CSNEPOCHS]:
                        # Indicate the rejection cause
                        PreproObs["RejectionCause"] = REJECTION_CAUSE["CYCLE_SLIP"]

                        # Upper reset smoothing flag
                        PrevPreproObsInfo[SatLabel]["ResetHatchFilter"] = 1

                    else:
                        # Update index of CS detector buffer
                        PrevPreproObsInfo[SatLabel]["CsIdx"] = \
                            (PrevPreproObsInfo[SatLabel]["CsIdx"] + 1) % \
                                int(Conf["MIN_NCS_TH"][CSNEPOCHS])

                        continue

                    # End of if np.sum(PrevPreproObsInfo[SatLabel]["CsBuff"]) == Conf["MIN_NCS_TH"][CSNEPOCHS]:

                # End of if CsFlag == True:

            # End of if PrevPreproObsInfo[SatLabel]["t_n_3"] > 0:

            # Update index of CS detector buffer
            PrevPreproObsInfo[SatLabel]["CsIdx"] = \
                (PrevPreproObsInfo[SatLabel]["CsIdx"] + 1) % \
                    int(Conf["MIN_NCS_TH"][CSNEPOCHS])

            # If CS flag was not True in the Conf["MIN_NCS_TH"][CSNEPOCHS] previous epochs
            if np.sum(PrevPreproObsInfo[SatLabel]["CsBuff"]) == 0:
                # Update previous values for next temporal iteration
                PrevPreproObsInfo[SatLabel]["L1_n_1"] = CP_n
                PrevPreproObsInfo[SatLabel]["L1_n_2"] = CP_n_1
                PrevPreproObsInfo[SatLabel]["L1_n_3"] = CP_n_2
                PrevPreproObsInfo[SatLabel]["t_n_3"] = PrevPreproObsInfo[SatLabel]["t_n_2"]
                PrevPreproObsInfo[SatLabel]["t_n_2"] = PrevPreproObsInfo[SatLabel]["t_n_1"]
                PrevPreproObsInfo[SatLabel]["t_n_1"] = Epoch

        # End of if (Conf["MIN_NCS_TH"][FLAG] == 1):

        # Hatch filter (re)initialization
        # ----------------------------------------------------------
        # If Hatch filter shall be reset
        if PrevPreproObsInfo[SatLabel]["ResetHatchFilter"] == 1:
            # Reset gap counter
            PrevPreproObsInfo[SatLabel]["GapCounter"] = 0

            # Ksmooth: Time index -> is equal to 1 at the beginning and is increasing linearly up
            PrevPreproObsInfo[SatLabel]["Ksmooth"] = 1

            # Initialize smoothed values
            PreproObs["SmoothC1"] = PreproObs["C1"]
            PrevPreproObsInfo[SatLabel]["PrevSmoothC1"] = \
                PreproObs["SmoothC1"]

            # Update previous Phase measurement
            PrevPreproObsInfo[SatLabel]["PrevL1"] = PreproObs["L1"]

            # Update previous epoch
            PrevPreproObsInfo[SatLabel]["PrevEpoch"] = Epoch

            # Update previous range rate 
            PrevPreproObsInfo[SatLabel]["PrevRangeRateL1"] = -9999.9

            # Update previous phase rate 
            PrevPreproObsInfo[SatLabel]["PrevPhaseRateL1"] = -9999.9

            # Lower Smoothing filter reset flag
            PrevPreproObsInfo[SatLabel]["ResetHatchFilter"] = 0

            # Update Smoothing status
            PreproObs["Status"] = 0

            # Reinitialize CS detection
            PrevPreproObsInfo[SatLabel]["L1_n_1"] = 0.0
            PrevPreproObsInfo[SatLabel]["L1_n_2"] = 0.0
            PrevPreproObsInfo[SatLabel]["L1_n_3"] = 0.0
            PrevPreproObsInfo[SatLabel]["t_n_1"] = 0.0
            PrevPreproObsInfo[SatLabel]["t_n_2"] = 0.0
            PrevPreproObsInfo[SatLabel]["t_n_3"] = 0.0
            PrevPreproObsInfo[SatLabel]["CsBuff"] = [0] * int(Conf["MIN_NCS_TH"][CSNEPOCHS])

            continue

        # End of if PrevPreproObsInfo[SatLabel]["ResetHatchFilter"] == 1:

        # Code Carrier Smoothing with a Hatch Filter
        # ----------------------------------------------------------
        # Update Smoothing iterator
        PrevPreproObsInfo[SatLabel]["Ksmooth"] = \
                PrevPreproObsInfo[SatLabel]["Ksmooth"] + DeltaT

        # Smoothing Time computation
        # Smoothing Time is equal to the time index if the time index 
        # is lower than the Hatch filter and equal to the Hatch filter 
        # time constant otherwise
        SmoothingTime = \
        (PrevPreproObsInfo[SatLabel]["Ksmooth"] <= Conf["HATCH_TIME"]) * \
                        PrevPreproObsInfo[SatLabel]["Ksmooth"] + \
        (PrevPreproObsInfo[SatLabel]["Ksmooth"] > Conf["HATCH_TIME"]) * \
                        Conf["HATCH_TIME"]

        # Weighting factor of the Smoothing filter
        Alpha = float(DeltaT) / \
                 SmoothingTime

        # Compute Smoothed C1
        PreproObs["SmoothC1"] = \
            Alpha * PreproObs["C1"] + \
            (1-Alpha) * \
                (PrevPreproObsInfo[SatLabel]["PrevSmoothC1"] + \
                    (PreproObs["L1"] - PrevPreproObsInfo[SatLabel]["PrevL1"]) * \
                        Const.GPS_L1_WAVE)

        # Check Phase Rate (only if activated in conf)
        # --------------------------------------------------------------------------------------------------------------------
        # Compute Phase Rate in meters/second
        PreproObs["PhaseRateL1"] = \
            (PreproObs["L1"] - PrevPreproObsInfo[SatLabel]["PrevL1"]) / \
                DeltaT * Const.GPS_L1_WAVE

        # Check Phase Rate
        if (Conf["MAX_PHASE_RATE"][FLAG] == 1) and \
            (abs(PreproObs["PhaseRateL1"]) > Conf["MAX_PHASE_RATE"][VALUE]):
            # Lower status and indicate the rejection cause
            PreproObs["ValidL1"] = 0
            PreproObs["RejectionCause"] = REJECTION_CAUSE["MAX_PHASE_RATE"]
            # Raise Smoothing filter reset flag
            PrevPreproObsInfo[SatLabel]["ResetHatchFilter"] = 1
            continue

        # If there are enough samples
        if (PrevPreproObsInfo[SatLabel]["PrevPhaseRateL1"] != -9999.9):
            # Check Phase Rate Step (only if activated in conf)
            # ----------------------------------------------------------
            # Compute Phase Rate Step in meters/second^2
            PreproObs["PhaseRateStepL1"] = \
                (PreproObs["PhaseRateL1"] - \
                        PrevPreproObsInfo[SatLabel]["PrevPhaseRateL1"]) / DeltaT

            if (Conf["MAX_PHASE_RATE_STEP"][FLAG] == 1) and \
                    (abs(PreproObs["PhaseRateStepL1"]) > \
                            Conf["MAX_PHASE_RATE_STEP"][VALUE]):
                # Lower status and indicate the rejection cause
                PreproObs["ValidL1"] = 0
                PreproObs["RejectionCause"] = REJECTION_CAUSE["MAX_PHASE_RATE_STEP"]
                # Raise Smoothing filter reset flag
                PrevPreproObsInfo[SatLabel]["ResetHatchFilter"] = 1
                continue

        # Check Code Step (only if activated in conf)
        # --------------------------------------------------------------------------------------------------------------------
        # Compute Code Rate in meters/second
        PreproObs["RangeRateL1"] = \
            (PreproObs["SmoothC1"] - \
                PrevPreproObsInfo[SatLabel]["PrevSmoothC1"]) / DeltaT

        # Check Code Rate
        if (Conf["MAX_CODE_RATE"][FLAG] == 1) and \
            (abs(PreproObs["RangeRateL1"]) > Conf["MAX_CODE_RATE"][VALUE]):
            # Lower status and indicate the rejection cause
            PreproObs["ValidL1"] = 0
            PreproObs["RejectionCause"] = REJECTION_CAUSE["MAX_CODE_RATE"]
            # Raise Smoothing filter reset flag
            PrevPreproObsInfo[SatLabel]["ResetHatchFilter"] = 1
            continue
        
        # If there are enough samples
        if (PrevPreproObsInfo[SatLabel]["PrevRangeRateL1"] != -9999.9):
            # Compute Code Rate Step in meters/second^2
            PreproObs["RangeRateStepL1"] = \
                (PreproObs["RangeRateL1"] - \
                        PrevPreproObsInfo[SatLabel]["PrevRangeRateL1"]) / DeltaT

            # Check Code Rate Step (only if activated in conf)
            # ----------------------------------------------------------
            if (Conf["MAX_CODE_RATE_STEP"][FLAG] == 1) and \
                    (abs(PreproObs["RangeRateStepL1"]) > \
                            Conf["MAX_CODE_RATE_STEP"][VALUE]):
                # Lower status and indicate the rejection cause
                PreproObs["ValidL1"] = 0
                PreproObs["RejectionCause"] = REJECTION_CAUSE["MAX_CODE_RATE_STEP"]
                # Raise Smoothing filter reset flag
                PrevPreproObsInfo[SatLabel]["ResetHatchFilter"] = 1
                continue

        # Set Status flag
        # ----------------------------------------------------------
        # 1 if convergence was reached, 0 otherwise
        if(PrevPreproObsInfo[SatLabel]["Ksmooth"] > \
            Conf["HATCH_STATE_F"] * Conf["HATCH_TIME"]) and \
              (PreproObs["ValidL1"] != 0) :
            PreproObs["Status"] = 1
        else: 
            PreproObs["Status"] = 0

        # Update previous values
        # ----------------------------------------------------------
        PrevPreproObsInfo[SatLabel]["PrevSmoothC1"] = PreproObs["SmoothC1"]
        PrevPreproObsInfo[SatLabel]["PrevL1"] = PreproObs["L1"]
        PrevPreproObsInfo[SatLabel]["PrevEpoch"] = Epoch
        PrevPreproObsInfo[SatLabel]["PrevRangeRateL1"] = PreproObs["RangeRateL1"]
        PrevPreproObsInfo[SatLabel]["PrevPhaseRateL1"] = PreproObs["PhaseRateL1"]
        PrevPreproObsInfo[SatLabel]["PrevRej"] = PreproObs["RejectionCause"]

    # End of for SatLabel, PreproObs in PreproObsInfo.items():

    # Loop over satellites
    for SatLabel, PreproObs in PreproObsInfo.items():
        # Compute Iono Mapping Function
        PreproObs["Mpp"] = computeIonoMappingFunction(PreproObs["Elevation"])

        # Build Geometry-Free combination of Phases
        # ----------------------------------------------------------
        # Check if L1 and L2 are OK
        if (PreproObs["ValidL1"] > 0) and (PreproObs["L2"] > 0):
            # Compute the Geometry-Free Observable
            PreproObs["GeomFree"] = Const.GPS_L1_WAVE * PreproObs["L1"] - \
                Const.GPS_L2_WAVE * PreproObs["L2"]

            # Obtain the final Geometry-Free (dividing by 1-GAMMA)
            PreproObs["GeomFree"] =  PreproObs["GeomFree"] / (1 - Const.GPS_GAMMA_L1L2)

            # If valid Previous Geometry-Free Observable
            if PrevPreproObsInfo[SatLabel]["PrevGeomFree"] > 0:
                # Compute the VTEC Rate
                # ----------------------------------------------------------
                # Compute the STEC Gradient
                DeltaStec =  \
                    (PreproObs["GeomFree"] - PrevPreproObsInfo[SatLabel]["PrevGeomFree"]) /\
                        (PreproObs["Sod"] - PrevPreproObsInfo[SatLabel]["PrevGeomFreeEpoch"])

                # Compute VTEC Gradient
                DeltaVtec =  DeltaStec / PreproObs["Mpp"]

                # Store DeltaVtec in mm/s
                PreproObs["VtecRate"] = DeltaVtec * 1000

                # Compute Instantaneous Along-Arc-TEC-Rate (AATR)
                # AATR is the delta VTEC weighted with the mapping function
                # ----------------------------------------------------------
                # Compute AATR
                PreproObs["iAATR"] =  PreproObs["VtecRate"] / PreproObs["Mpp"]

            # Update previous Geometry-Free Observable
            PrevPreproObsInfo[SatLabel]["PrevGeomFree"] = PreproObs["GeomFree"]
            PrevPreproObsInfo[SatLabel]["PrevGeomFreeEpoch"] = PreproObs["Sod"]

    return PreproObsInfo

# End of function runPreProcMeas()

########################################################################
# END OF PREPROCESSING FUNCTIONS MODULE
########################################################################
