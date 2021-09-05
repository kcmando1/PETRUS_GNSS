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
from InputOutput import rejectSatsMinElevation
from numpy import *
from COMMON.Iono import computeIonoMappingFunction

# Preprocessing internal functions
#-----------------------------------------------------------------------


def runPreProcMeas(Conf, Rcvr, ObsInfo, PrevPreproObsInfo, ObsData):
    
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

    dT = 0

    satTags=[]
    zeroes=[0]*(Const.MAX_NUM_SATS_CONSTEL + 1)
    printflag=0



    for x in range(Const.MAX_NUM_SATS_CONSTEL + 1):
        satTags.append("G" + "%02d" % int(x))
    gapCounter = dict(zip(satTags,zeroes))
    ResetHF = dict(zip(satTags, zeroes))
    MaxNoise = Conf["MIN_CNR"][1]
    MinElevation = Conf["RCVR_MASK"]
    MaxPSR=Conf["MAX_PSR_OUTRNG"][1]

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
        SatPreproObsInfo["Doy"] = float(SatObs[ObsIdx["DOY"]])
        # Get PRN
        SatPreproObsInfo["PRN"] = float(SatObs[ObsIdx["PRN"]])
        # Get Elevation
        SatPreproObsInfo["Elevation"] = float(SatObs[ObsIdx["ELEV"]])
        #Get Azimuth
        SatPreproObsInfo["Azimuth"] = float(SatObs[ObsIdx["AZIM"]])
        #Get C1
        SatPreproObsInfo["C1"] = float(SatObs[ObsIdx["C1"]])
        # Get L1
        SatPreproObsInfo["L1"] = float(SatObs[ObsIdx["L1"]])
        SatPreproObsInfo["L1Meters"] = float(SatObs[ObsIdx["L1"]]) * Const.GPS_L1_WAVE
        #Get S1
        SatPreproObsInfo["S1"] = float(SatObs[ObsIdx["S1"]])
        # Get L2
        SatPreproObsInfo["L2"] = float(SatObs[ObsIdx["L2"]])

        # Prepare output for the satellite
        PreproObsInfo[SatLabel] = SatPreproObsInfo
    # ----------------------------------------------------------
    # CODE HERE
    # Limit the satellites to the Number of Channels
    #Implementation only for gps
    NVisSats = len(unique(ObsInfo[ObsIdx["PRN"]]))


    if NVisSats>Conf["NCHANNELS_GPS"]:
        # REQ-010
        rejectSatsMinElevation(PreproObsInfo,NVisSats,Conf["NCHANNELS_GPS"])
    for x in range(1, Const.MAX_NUM_SATS_CONSTEL + 1):
        SatLabel = "G" + "%02d" % int(x)
        # Check if the satellite is in view
        # ------------------------------------------------------------------------
        if not SatLabel in PreproObsInfo:
            continue
        # Check if the satellite is valid
        # ------------------------------------------------------------------------
        if PreproObsInfo[SatLabel]["ValidL1"] == 0:
            continue

        # reject for bad elevation REQ-NO
        if (PreproObsInfo[SatLabel]["Elevation"] < MinElevation):
            PreproObsInfo[SatLabel]["RejectionCause"] = REJECTION_CAUSE["MASKANGLE"]
            PreproObsInfo[SatLabel]["ValidL1"] = 0
            PrevPreproObsInfo["PrevRej"] = REJECTION_CAUSE["MASKANGLE"]
            continue


        # rejects if noise ratio  REQ-020
        if PreproObsInfo[SatLabel]["S1"] < MaxNoise and Conf["MIN_CNR"][0]:
            PreproObsInfo[SatLabel]["RejectionCause"] = REJECTION_CAUSE["MIN_CNR"]
            PreproObsInfo[SatLabel]["ValidL1"] = 0
            PrevPreproObsInfo["PrevRej"] = REJECTION_CAUSE["MIN_CNR"]
            continue


        # rejects if psr  REQ-030
        if PreproObsInfo[SatLabel]["C1"] > MaxPSR and Conf["MAX_PSR_OUTRNG"][0]:
            PreproObsInfo[SatLabel]["RejectionCause"] = REJECTION_CAUSE["MAX_PSR_OUTRNG"]
            PreproObsInfo[SatLabel]["ValidL1"] = 0
            continue

        #rejects if data gap REQ-040

        validEpoch = PreproObsInfo[SatLabel]["RejectionCause"] != REJECTION_CAUSE['MASKANGLE']
        previousValidEpoch = PrevPreproObsInfo[SatLabel]["PrevRej"] != REJECTION_CAUSE['MASKANGLE']

        if validEpoch and previousValidEpoch:
            dT=PreproObsInfo[SatLabel]['Sod'] - PrevPreproObsInfo[SatLabel]['PrevEpoch']
            if dT > Conf["SAMPLING_RATE"]:
                gapCounter[SatLabel]=dT
                # if T2 == 1:
                #     print(gapCounter[SatLabel])
                #     T2=0
            else:
                gapCounter[SatLabel] = 0
            if gapCounter[SatLabel] > Conf["HATCH_GAP_TH"] and PreproObsInfo[SatLabel]["Elevation"] > MinElevation:
                # print("Satlabel="+str(SatLabel))
                # print("SOD="+str(PreproObsInfo[SatLabel]["Sod"]))
                # print("gapsize="+str(gapCounter[SatLabel]))
                # print("---------")
                ResetHF[x]=1 #REQ-90
                PreproObsInfo[SatLabel]["RejectionCause"] = REJECTION_CAUSE["DATA_GAP"]
                PreproObsInfo[SatLabel]["ValidL1"] = 0

        # cycle slip implementation

        if ResetHF[SatLabel] != 1 and Conf["MIN_NCS_TH"][0]:
            if PreproObsInfo[SatLabel]["Sod"] == 14066 and SatLabel == "G10":
                dev=4
            # phase meas
            CS = PreproObsInfo[SatLabel]["L1"]
            CS_1 = PrevPreproObsInfo[SatLabel]["L1_n_1"]
            CS_2 = PrevPreproObsInfo[SatLabel]["L1_n_2"]
            CS_3 = PrevPreproObsInfo[SatLabel]["L1_n_3"]


            # time meas
            t1 = PreproObsInfo[SatLabel]["Sod"] - PrevPreproObsInfo[SatLabel]["t_n_1"]
            t2 = PrevPreproObsInfo[SatLabel]["t_n_1"] - PrevPreproObsInfo[SatLabel]["t_n_2"]
            t3 = PrevPreproObsInfo[SatLabel]["t_n_2"] - PrevPreproObsInfo[SatLabel]["t_n_3"]

            if PrevPreproObsInfo[SatLabel]["t_n_3"] > 0:
                R1=R2=R3=0
                try:
                    R1 = float((t1 + t2) * (t1 + t2 + t3)) / (t2 * (t2 + t3))
                    R2 = float(-t1 * (t1 + t2 + t3)) / (t2 * t3)
                    R3 = float(t1 * (t1 + t2)) / ((t2 + t3) * t3)
                except ZeroDivisionError:
                    # First iterations, may end up with t1, t2, t3 == 0
                    None
                # Residuals meas
                CsResidual = abs(CS - R1 * CS_1 - R2 * CS_2 - R3 * CS_3)

                if round(CsResidual,2) >= float(Conf["MIN_NCS_TH"][1]) :
                    FLAG = True
                else:
                    FLAG = False
                PrevPreproObsInfo[SatLabel]["CsBuff"][PrevPreproObsInfo[SatLabel]["CsIdx"]] =FLAG
                if PreproObsInfo[SatLabel]["Sod"] == 39172 and SatLabel == "G28" or\
                        PreproObsInfo[SatLabel]["Sod"] == 51292 and SatLabel == "G19"or\
                        PreproObsInfo[SatLabel]["Sod"] == 79282 and SatLabel == "G20":
                    printflag=1
                    print("-----")
                    print("")
                    print("SOD=" + str(PreproObsInfo[SatLabel]["Sod"]))
                    print(CsResidual)
                    print(FLAG)


                if FLAG:
                    PreproObsInfo[SatLabel]["ValidL1"] = 0
                    #print('[TESTING][runPreProcMeas]' + ' epoch' + ObsInfo[0][0] + ' Satellite ' + SatLabel + ' HF reset (CS)')
                    if printflag==1:
                        print("CSBUF")
                        print((PrevPreproObsInfo[SatLabel]["CsBuff"][0]))
                        print((PrevPreproObsInfo[SatLabel]["CsBuff"][1]))
                        print((PrevPreproObsInfo[SatLabel]["CsBuff"][2]))
                        printflag=0
                    if sum(PrevPreproObsInfo[SatLabel]["CsBuff"]) >= Conf["MIN_NCS_TH"][2]:
                        PreproObsInfo[SatLabel]["RejectionCause"] = REJECTION_CAUSE["CYCLE_SLIP"]
                        ResetHF[SatLabel]=1
                        print('[TESTING][runPreProcMeas]' + ' epoch' + ObsInfo[0][0] + ' Satellite ' + SatLabel + ' HF reset (CS)')
                    else:
                        PrevPreproObsInfo[SatLabel]["CsIdx"]=(PrevPreproObsInfo[SatLabel]["CsIdx"]+1)% int(Conf["MIN_NCS_TH"][2])

            PrevPreproObsInfo[SatLabel]["CsIdx"] = (PrevPreproObsInfo[SatLabel]["CsIdx"] + 1) % int(Conf["MIN_NCS_TH"][2])

            if sum(PrevPreproObsInfo[SatLabel]["CsBuff"]==0):
                PrevPreproObsInfo[SatLabel]["L1_n_1"]=CS
                PrevPreproObsInfo[SatLabel]["L1_n_2"]=CS_1
                PrevPreproObsInfo[SatLabel]["L1_n_3"]=CS_2
                PrevPreproObsInfo[SatLabel]["t_n_3"]=PrevPreproObsInfo[SatLabel]["t_n_2"]
                PrevPreproObsInfo[SatLabel]["t_n_2"]=PrevPreproObsInfo[SatLabel]["t_n_1"]
                PrevPreproObsInfo[SatLabel]["t_n_1"]=PreproObsInfo[SatLabel]["Sod"]


        #reset hatch filter
        if ResetHF[SatLabel]==1:
            gapCounter[SatLabel]=0
            PreproObsInfo[SatLabel]["ksmooth"] = 1
            PrevPreproObsInfo[SatLabel]["SmoothC1"]=PreproObsInfo[SatLabel]["C1"]
            PrevPreproObsInfo[SatLabel]["SmoothC1"]=PreproObsInfo[SatLabel]["SmoothC1"]
            PrevPreproObsInfo[SatLabel]["PrevL1"]=PreproObsInfo[SatLabel]["L1"]
            PrevPreproObsInfo[SatLabel]['PrevEpoch']=PreproObsInfo[SatLabel]["Sod"]
            PrevPreproObsInfo[SatLabel]["PrevRangeRateL1"]= -1000
            PrevPreproObsInfo[SatLabel]["PrevPhaseRateL1"]= -1000
            ResetHF[SatLabel]=0
            PreproObsInfo[SatLabel]["Status"]=0
            PrevPreproObsInfo[SatLabel]["L1_n_1"] = 0.0
            PrevPreproObsInfo[SatLabel]["L1_n_2"] = 0.0
            PrevPreproObsInfo[SatLabel]["L1_n_3"] = 0.0
            PrevPreproObsInfo[SatLabel]["t_n_3"] = 0.0
            PrevPreproObsInfo[SatLabel]["t_n_2"] = 0.0
            PrevPreproObsInfo[SatLabel]["t_n_1"] = 0.0
            PrevPreproObsInfo[SatLabel]["CsBuff"]= [0]*int(Conf["MIN_NCS_TH"][2])
            continue

            # code smooothing REQ-100

        PrevPreproObsInfo[SatLabel]["ksmooth"]=+ dT

        if PrevPreproObsInfo[SatLabel]["ksmooth"]<=Conf["HATCH_TIME"]:
            SmoothT=PrevPreproObsInfo[SatLabel]["ksmooth"]
        if PrevPreproObsInfo[SatLabel]["ksmooth"]>Conf["HATCH_TIME"]:
            SmoothT=Conf["HATCH_TIME"]
        try:
            Alpha=dT/SmoothT
        except ZeroDivisionError:
            Alpha=1#No smooth from previous meas if invalid as 1-alpha results in an avoidance of that effect
        PreproObsInfo[SatLabel]["SmoothC1"]=Alpha*PreproObsInfo[SatLabel]["C1"]+(1-Alpha)* \
            PrevPreproObsInfo[SatLabel]["PrevSmoothC1"]+\
            (PreproObsInfo[SatLabel]["L1"]-PrevPreproObsInfo[SatLabel]["PrevL1"])*Const.GPS_L1_WAVE

        #phase rate check REQ-50
        try:
            PreproObsInfo[SatLabel]["PhaseRateL1"]=(PreproObsInfo[SatLabel]["L1"]- \
                PrevPreproObsInfo[SatLabel]["PrevL1"]) / dT * Const.GPS_L1_WAVE
        except ZeroDivisionError:
            PreproObsInfo[SatLabel]["PhaseRateL1"]=0

        if Conf["MAX_PHASE_RATE"][0]==1 and abs(PreproObsInfo[SatLabel]["PhaseRateL1"])>Conf["MAX_PHASE_RATE"][1]:
            PreproObsInfo[SatLabel]["RejectionCause"] = REJECTION_CAUSE["MAX_PHASE_RATE"]
            PreproObsInfo[SatLabel]["ValidL1"] = 0
            ResetHF[SatLabel]=1
            continue

        # phase rate step check REQ-60
        if PrevPreproObsInfo[SatLabel]["PrevPhaseRateL1"] is not -1000:
            try:
                PreproObsInfo[SatLabel]["PhaseRateStepL1"] = PreproObsInfo[SatLabel]["L1"]- \
                PrevPreproObsInfo[SatLabel]["PrevPhaseRateL1"] / dT
            except ZeroDivisionError:
                PreproObsInfo[SatLabel]["PhaseRateStepL1"] = 0
            if Conf["MAX_PHASE_RATE_STEP"][0] == 1 and abs(PreproObsInfo[SatLabel]["PhaseRateStepL1"]) > \
                    Conf["MAX_PHASE_RATE_STEP"][1]:
                PreproObsInfo[SatLabel]["RejectionCause"] = REJECTION_CAUSE["MAX_PHASE_RATE_STEP"]
                PreproObsInfo[SatLabel]["ValidL1"] = 0
                ResetHF[SatLabel] = 1
                continue

        #code rate detector REQ-80
        try:
            PreproObsInfo[SatLabel]["RangeRateL1"]=PreproObsInfo[SatLabel]["SmoothC1"]-\
                                               PrevPreproObsInfo[SatLabel]["PrevSmoothC1"] / dT
        except ZeroDivisionError:
            # PreproObsInfo[SatLabel]["RangeRateL1"] = 0
            None
        if Conf["MAX_CODE_RATE"][0] == 1 and abs(PreproObsInfo[SatLabel]["RangeRateL1"]) > Conf["MAX_CODE_RATE"][1]:
            PreproObsInfo[SatLabel]["RejectionCause"] = REJECTION_CAUSE["MAX_CODE_RATE"]
            PreproObsInfo[SatLabel]["ValidL1"] = 0
            ResetHF[SatLabel] = 1
            continue
        #code rate step detector REQ-70

        if PrevPreproObsInfo[SatLabel]["PrevRangeRateL1"] is not -1000:
            try:
                PreproObsInfo[SatLabel]["RangeRateStepL1"] = PreproObsInfo[SatLabel]["RangeRateStepL1"]- \
                PrevPreproObsInfo[SatLabel]["PrevRangeRateL1"] / dT
            except ZeroDivisionError:
                # PreproObsInfo[SatLabel]["PhaseRateStepL1"] = 0
                None
            if Conf["MAX_CODE_RATE_STEP"][0] == 1 and abs(PreproObsInfo[SatLabel]["RangeRateStepL1"]) > \
                    Conf["MAX_CODE_RATE_STEP"][1]:
                PreproObsInfo[SatLabel]["RejectionCause"] = REJECTION_CAUSE["MAX_CODE_RATE_STEP"]
                PreproObsInfo[SatLabel]["ValidL1"] = 0
                ResetHF[SatLabel] = 1
                continue


        #update meas smoothing status and hf convergence
        if PrevPreproObsInfo[SatLabel]["ksmooth"]> Conf["HATCH_STATE_F"]*Conf["HATCH_TIME"] and\
                PreproObsInfo[SatLabel]["ValidL1"] != 0:
            PreproObsInfo[SatLabel]["Status"] = 1
        else:
            PreproObsInfo[SatLabel]["Status"] = 0
        #loop updater if not rejected measures so you mantain last "valid" one




    #REQ-110 AATR WTF?


        # update prev status for functions

    for y in PreproObsInfo:
        # Update carrier phase in L1
        PrevPreproObsInfo[y]['L1_n_3'] = PrevPreproObsInfo[y]['L1_n_2']
        PrevPreproObsInfo[y]['L1_n_2'] = PrevPreproObsInfo[y]['L1_n_1']
        PrevPreproObsInfo[y]['L1_n_1'] = PreproObsInfo[y]['L1']

        # Update epoch
        PrevPreproObsInfo[y]['t_n_3'] = PrevPreproObsInfo[y]['t_n_2']
        PrevPreproObsInfo[y]['t_n_2'] = PrevPreproObsInfo[y]['t_n_1']
        PrevPreproObsInfo[y]['t_n_1'] = PreproObsInfo[y]['Sod']


        PrevPreproObsInfo[y]['PrevEpoch'] = PreproObsInfo[y]['Sod']
        PrevPreproObsInfo[y]['PrevL1'] = PreproObsInfo[y]['L1']
        PrevPreproObsInfo[y]['PrevRej'] = PreproObsInfo[y]['RejectionCause']
        PrevPreproObsInfo[y]["PrevSmoothC1"] = PreproObsInfo[y]["SmoothC1"]
        PrevPreproObsInfo[y]["PrevL1"] = PreproObsInfo[y]["L1"]
        PrevPreproObsInfo[y]["PrevRangeRateL1"] = PreproObsInfo[y]["RangeRateL1"]
        PrevPreproObsInfo[y]["PrevPhaseRateL1"] = PreproObsInfo[y]["PhaseRateL1"]




    # END of PPVE LOOP
    # ----------------------------------------------------------

    return PreproObsInfo

# End of function runPreProcMeas()

########################################################################
# END OF PREPROCESSING FUNCTIONS MODULE
########################################################################
