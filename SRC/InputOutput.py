#!/usr/bin/env python

########################################################################
# PETRUS/SRC/Preprocessing.py:
# This is the Inputs (conf and input files) Module of PETRUS tool
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
from collections import OrderedDict
from COMMON.Dates import convertYearMonthDay2JulianDay
from COMMON import GnssConstants as Const
from COMMON.Coordinates import llh2xyz


# Input interfaces
#----------------------------------------------------------------------
# CONF
FLAG = 0
VALUE = 1
TH = 1
CSNEPOCHS = 2

# RCVR file columns
RcvrIdx = OrderedDict({})
RcvrIdx["ACR"]=0
RcvrIdx["FLAG"]=1
RcvrIdx["ID"]=2
RcvrIdx["LON"]=3
RcvrIdx["LAT"]=4
RcvrIdx["ALT"]=5
RcvrIdx["MASK"]=6
RcvrIdx["ACQ"]=7
RcvrIdx["XYZ"]=8

# OBS file columns
ObsIdx = OrderedDict({})
ObsIdx["SOD"]=0
ObsIdx["DOY"]=1
ObsIdx["YEAR"]=2
ObsIdx["CONST"]=3
ObsIdx["PRN"]=4
ObsIdx["ELEV"]=5
ObsIdx["AZIM"]=6
ObsIdx["C1"]=7
ObsIdx["L1"]=8
ObsIdx["P2"]=9
ObsIdx["L2"]=10
ObsIdx["S1"]=11
ObsIdx["S2"]=12

# Output interfaces
#----------------------------------------------------------------------
# PREPRO OBS 
# Header
PreproHdr = "\
# SOD DOY C PRN    ELEV     AZIM  VALID REJ  STATUS    C1          C1SMOOTHED          L1           S1     CODERATE   CODEACC    PHASERATE PHASEACC  GEOMFREE VTECRATE  iAATR\n"

# Line format
PreproFmt = "%05d %03d %s %02d %8.3f %8.3f %4d %4d %4d "\
    "%15.3f %15.3f %15.3f %8.3f %10.3f %10.3f %10.3f %10.3f "\
    "%8.3f %8.3f %8.3f".split()

# File columns
PreproIdx = OrderedDict({})
PreproIdx["SOD"]=0
PreproIdx["DOY"]=1
PreproIdx["CONST"]=2
PreproIdx["PRN"]=3
PreproIdx["ELEV"]=4
PreproIdx["AZIM"]=5
PreproIdx["VALID"]=6
PreproIdx["REJECT"]=7
PreproIdx["STATUS"]=8
PreproIdx["C1"]=9
PreproIdx["C1SMOOTHED"]=10
PreproIdx["L1"]=11
PreproIdx["S1"]=12
PreproIdx["CODE RATE"]=13
PreproIdx["CODE ACC"]=14
PreproIdx["PHASE RATE"]=15
PreproIdx["PHASE ACC"]=16
PreproIdx["GEOM FREE"]=17
PreproIdx["VTEC RATE"]=18
PreproIdx["iAATR"]=19

# Rejection causes flags
REJECTION_CAUSE = OrderedDict({})
REJECTION_CAUSE["NCHANNELS_GPS"]=1
REJECTION_CAUSE["MASKANGLE"]=2
REJECTION_CAUSE["MIN_CNR"]=3
REJECTION_CAUSE["MAX_PSR_OUTRNG"]=4
REJECTION_CAUSE["CYCLE_SLIP"]=5
REJECTION_CAUSE["DATA_GAP"]=6
REJECTION_CAUSE["MAX_PHASE_RATE"]=7
REJECTION_CAUSE["MAX_PHASE_RATE_STEP"]=8
REJECTION_CAUSE["MAX_CODE_RATE"]=9
REJECTION_CAUSE["MAX_CODE_RATE_STEP"]=10

REJECTION_CAUSE_DESC = OrderedDict({})
REJECTION_CAUSE_DESC["1: Number of Channels for GPS"]=1
REJECTION_CAUSE_DESC["2: Mask Angle"]=2
REJECTION_CAUSE_DESC["3: Minimum C/N0"]=3
REJECTION_CAUSE_DESC["4: Maximum PR"]=4
REJECTION_CAUSE_DESC["5: Cycle Slip"]=5
REJECTION_CAUSE_DESC["6: Data Gap"]=6
REJECTION_CAUSE_DESC["7: Maximum Phase Rate"]=7
REJECTION_CAUSE_DESC["8: Maximum Phase Rate Step"]=8
REJECTION_CAUSE_DESC["9: Maximum Code Rate"]=9
REJECTION_CAUSE_DESC["10: Maximum Code Rate Step"]=10

# Input functions
#----------------------------------------------------------------------
def checkConfParam(Key, Fields, MinFields, MaxFields, LowLim, UppLim):
    
    # Purpose: check configuration parameter format, type and range

    # Parameters
    # ==========
    # Key: str
    #         Configuration parameter key
    # Fields: list
    #         Configuration parameter read from conf and split
    # MinFields: int
    #         Minimum number of fields expected
    # MaxFields: int
    #         Maximum number of fields expected
    # LowLim: list
    #         List containing lower limit allowed for each of the fields
    # UppLim: list
    #         List containing upper limit allowed for each of the fields

    # Returns
    # =======
    # Values: str, int, float or list
    #         Configuration parameter value or list of values
    
    # Prepare output list
    Values = []

    # Get Fields length
    LenFields = len(Fields) - 1

    # Check that number of fields is not less than the expected minimum
    if(LenFields < MinFields):
        # Display an error
        sys.stderr.write("ERROR: Too few fields (%d) for configuration parameter %s. "\
        "Minimum = %d\n" % (LenFields, Key, MinFields))
        sys.exit(-1)
    # End if(LenFields < MinFields)

    # Check that number of fields is not greater than the expected minimum
    if(LenFields > MaxFields):
        # Display an error
        sys.stderr.write("ERROR: Too many fields (%d) for configuration parameter %s. "\
        "Maximum = %d\n" % (LenFields, Key, MaxFields))
        sys.exit(-1)
    # End if(LenFields > MaxFields)

    # Loop over fields
    for i, Field in enumerate(Fields[1:]):
        # If float
        try:
            # Convert to float and append to the outputs
            Values.append(float(Field))

        except:
            # isnumeric check
            try:
                Check = unicode(Field).isnumeric()

            except:
                Check = (Field).isnumeric()

            # If it is integer
            if(Check):
                # Convert to int and append to the outputs
                Values.append(int(Field))

            else:
                # Append to the outputs
                Values.append(Field)

    # End of for i, Field in enumerate(Fields[1:]):

    # Loop over values to check the range
    for i, Field in enumerate(Values):
        # If range shall be checked
        if(isinstance(LowLim[i], int) or \
            isinstance(LowLim[i], float)):
            # Try to check the range
            try:
                if(Field<LowLim[i] or Field>UppLim[i]):
                    # Out of range
                    sys.stderr.write("ERROR: Configuration parameter %s "\
                        "%f is out of range [%f, %f]\n" % 
                    (Key, Field, LowLim[i], UppLim[i]))

            except:
                # Wrong format
                sys.stderr.write("ERROR: Wrong type for configuration parameter %s\n" %
                Key)
                sys.exit(-1)

    # End of for i, Field in enumerate(Values):

    # If only one element, return the value directly
    if len(Values) == 1:
        return Values[0]

    # Otherwise, return the list
    else:
        return Values

# End of checkConfParam()

def readConf(CfgFile):
    
    # Purpose: read the configuration file
       
    # Parameters
    # ==========
    # CfgFile: str
    #         Path to conf file

    # Returns
    # =======
    # Conf: Dict
    #         Conf loaded in a dictionary
    

    # Function to check the format of the dates
    def checkConfDate(Key, Fields):
        # Split Fields
        FieldsSplit=Fields[1].split('/')

        # Set expected number of characters
        ExpectedNChar = [2,2,4]

        # Check the number of characters in each field
        for i, Field in enumerate(FieldsSplit):
            # if number of characters is incorrect
            if len(Field) != ExpectedNChar[i]:
                sys.stderr.write("ERROR: wrong format in configured %s\n" % Key)
                sys.exit(-1)

    # End of checkConfDate()

    # Initialize the variable to store the conf
    Conf = OrderedDict({})

    # Initialize the configuration parameters counter
    NReadParams = 0
    
    # Open the file
    with open(CfgFile, 'r') as f:
        # Read file
        Lines = f.readlines()

        # Parse each Line of configuration file
        for Line in Lines:
            
            # Check if Line is not a comment
            if Line[0]!='#':
                
                # Split Line in a list of Fields
                Fields=Line.rstrip('\n').split(' ')
                
                # Check if line is blank
                if '' in Fields:
                    Fields = list(filter(None, Fields))

                if Fields != None :
                    # if some parameter with its value missing, warn the user
                    if len(Fields) == 1:
                        sys.stderr.write("ERROR: Configuration file contains a parameter" \
                            "with no value: " + Line)
                        sys.exit(-1)

                    # if the line contains a conf parameter
                    elif len(Fields)!=0:
                        # Get conf parameter key
                        Key=Fields[0]

                        # Fill in Conf appropriately according to the configuration file Key
                        
                        # Scenario Start and End Dates [GPS time in Calendar format]
                        #--------------------------------------------------------------------
                        # Date format DD/MM/YYYY (e.g: 01/09/2119)
                        #--------------------------------------------------------------------
                        if Key=='INI_DATE':
                            # Check date format
                            checkConfDate(Key, Fields)

                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, [None], [None])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        elif Key=='END_DATE':
                            # Check date format
                            checkConfDate(Key, Fields)

                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, [None], [None])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Scenario Sampling Rate [SECONDS]
                        #-------------------------------------------
                        elif Key=='SAMPLING_RATE':
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, [1], [Const.S_IN_D])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # SBAS MODE [SBASL1|SBASL5]
                        #--------------------------------------------------------------------
                        # SF: MOPS SBASL1 Applicable Standard for SF Users
                        # DF: DFMC SBASL5 Applicable Standard for DF Users
                        #--------------------------------------------------------------------
                        elif Key=='SBAS_MODE':
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, [None], [None])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # GEO PRN Selection
                        #--------------------------------------------------------------------
                        elif Key=='GEO':
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, 
                            [Const.MIN_GEO_PRN], [Const.MAX_GEO_PRN])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Navigation Solution Selection
                        #-----------------------------------------------
                        # Three Options:
                        #       GPS: SBAS GPS
                        #       GAL: SBAS Galileo
                        #       GPSGAL: SBAS GPS+Galileo
                        #-----------------------------------------------
                        elif Key=='NAV_SOLUTION':
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, [None], [None])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # GPS Dual-Frequency Selection
                        #-----------------------------------------------
                        # Two Options:
                        #       L1L2: L1C/A/L2P
                        #       L1L5: L1C/A+L5
                        #-----------------------------------------------
                        elif Key=='GPS_FREQ':
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, [None], [None])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # GALILEO Dual-Frequency Selection
                        #-----------------------------------------------
                        # Three Options:
                        #       E1E5A: E1+E5a
                        #       E1E5B: E1+E5b
                        #-----------------------------------------------
                        elif Key=='GAL_FREQ':
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, [None], [None])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Preprocessing outputs selection [0:OFF|1:ON]
                        #--------------------------------------------------------------------       
                        elif Key=='PREPRO_OUT':
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, [0], [1])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Corrected outputs selection [0:OFF|1:ON]
                        #--------------------------------------------------------------------       
                        elif Key=='CORR_OUT':
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, [0], [1])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Rx Position Information [STATIC|DYN]
                        #-----------------------------------------------
                        # STAT: RIMS static positions
                        # DYNA: RCVR dynamic positions
                        #-----------------------------------------------
                        elif Key=='RCVR_INFO':
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, [None], [None])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # RIMS positions file Name  (if RCVR_INFO=STATIC)
                        #-----------------------------------------------
                        elif Key=='RCVR_FILE':
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, [None], [None])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Number of Channels for each constellation
                        #-----------------------------------------------
                        elif Key=='NCHANNELS_GPS':
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, 
                            [1], [Const.MAX_NUM_SATS_CONSTEL])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1
                        
                        elif Key=='NCHANNELS_GAL':
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, 
                            [1], [Const.MAX_NUM_SATS_CONSTEL])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # RCVR mask Angle [DEG]
                        #-----------------------------------------------
                        elif Key== 'RCVR_MASK': 
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, 
                            [Const.MIN_MASK_ANGLE], [Const.MAX_MASK_ANGLE])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1
                            
                        # AIRBORNE Equipement Class [1|2|3|4]
                        #-----------------------------------------------
                        elif Key== 'EQUIPMENT_CLASS':  
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, [1], [4])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1
                            
                        # AIRBORNE Accuracy Designator MOPS [A|B]
                        #-----------------------------------------------
                        elif Key== 'AIR_ACC_DESIG':  
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, [None], [None])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Elevation Threshold for MOPS Sigma Noise [deg]
                        #--------------------------------------------------
                        elif Key== 'ELEV_NOISE_TH':  
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, 
                            [0], [90])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Sigma Noise for DF processing [m]
                        #--------------------------------------------------
                        elif Key== 'SIGMA_NOISE_DF':  
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, 
                            [0], [10])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Minimum Carrier To Noise Ratio
                        #------------------------------
                        # p1: Check C/No [0:OFF|1:ON]
                        # p2: C/No Threshold [dB-Hz]
                        #------------------------------
                        elif Key== 'MIN_CNR':  
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 2, 2, 
                            [0, 0], [1, 80])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Check Cycle Slips 
                        #----------------------------------------
                        # p1: Check CS [0:OFF|1:ON]
                        # p2: CS threshold [cycles]
                        # p3: CS Nepoch
                        #----------------------------------------
                        elif Key== 'MIN_NCS_TH':  
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 3, 3, 
                            [0, 0, 0], [1, 10, 3])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1
                        
                        # Check Pseudo-Range Measurement Out of Range
                        #-------------------------------------------
                        # p1: Check PSR Range [0:OFF|1:ON]
                        # p2: Max. Range [m]  (Default:330000000]
                        #-----------------------------------------------
                        elif Key== 'MAX_PSR_OUTRNG':  
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 2, 2, 
                            [0, 0], 
                            [1, 400000000])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1
                        
                        # Check Code Rate
						#-----------------------------------------------
						# p1: Check Code Rate [0:OFF|1:ON]
						# p2: Max. Code Rate [m/s]  (Default: 952)
						#-----------------------------------------------
                        elif Key== 'MAX_CODE_RATE':  
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 2, 2, 
                            [0, 0], 
                            [1, 2000])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Check Code Rate Step 
						#-----------------------------------------------
						# p1: Check Code Rate Step [0:OFF|1:ON]
						# p2: Max. Code Rate Step [m/s**2]  (Default: 10)
						#-----------------------------------------------
                        elif Key== 'MAX_CODE_RATE_STEP':  
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 2, 2, 
                            [0, 0], 
                            [1, 100])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Check Phase Measurement Rate 
						#-----------------------------------------------
						# p1: Check Phase Rate [0:OFF|1:ON]
						# p2: Max. Phase Rate [m/s]  (Default: 952)
						#-----------------------------------------------
                        elif Key== 'MAX_PHASE_RATE':  
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 2, 2, 
                            [0, 0], 
                            [1, 2000])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1
                            
                        # Check Phase Rate Step 
						#-----------------------------------------------
						# p1: Check Phase Rate Step [0:OFF|1:ON]
						# p2: Max. Phase Rate Step [m/s**2]  (Default: 10 m/s**2)
						#-----------------------------------------------
                        elif Key== 'MAX_PHASE_RATE_STEP':
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 2, 2, 
                            [0, 0], 
                            [1, 100])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Max. DATA GAP for PSR Propagation reset [s]
                        #------------------------------------------
                        elif Key== 'HATCH_GAP_TH':  
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, 
                            [0], [3600])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Hatch filter Smoothing time [s]
                        #----------------------------------
                        elif Key== 'HATCH_TIME':
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, 
                            [0], 
                            [3600])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Hatch filter Steady State factor
                        #----------------------------------
                        elif Key== 'HATCH_STATE_F':
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, 
                            [0], [10])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Hatch filter Divergence Threshold [m]
                        #---------------------------------------
                        elif Key== 'HATCH_DIV_TH': 
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, 
                            [0], [100])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Hatch filter Divergence Epochs to reset [s]
                        #---------------------------------------------
                        elif Key== 'HATCH_DIV_TIME':
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, 
                            [0], [10])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Max. Number of interations for Navigation Solution
                        #----------------------------------------------------
                        elif Key== 'MAX_LSQ_ITER': 
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, 
                            [0], [1e8])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # SBAS IONO for NPA [0:OFF|1:ON]
                        #-----------------------------------------------
                        elif Key== 'SBAS_IONO_NPA': 
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, 
                            [0], [1])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Maximum PDOP Threshold for Solution [m]
                        # Default Value: 10000.0
                        #-----------------------------------------------
                        elif Key== 'PDOP_MAX': 
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 1, 1, 
                            [0], [Const.MAX_PDOP_PVT])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        # Service Level Specific Parameters
                        #------------------------------------------------------------
                        # ON/OFF: Service Level Selection [0:OFF|1:ON]
                        #         -> OS:       Open Service
                        #         -> APVI:     APV-I Service
                        #         -> LPV200:   LPV-200 Service
                        #         -> CATI:     CAT-I Service 
                        #         -> NPA:      NPA - Non-Precission Approach
                        #         -> MARITIME: MARITIME Services
                        #         -> CUSTOM:   USER Customized Service
                        # HAL:      Horizontal Alarm Limit [m]
                        # VAL:      Vertical Alarm Limit [m]
                        # HPE95:    Horizontal Position Error at 95% Target [m]
                        # VPE95:    Vertical Position Error at 95% Target [m]
                        # VPE1E7:   Vertical Position Error at 1-1E-7/150s Target [m]
                        # AVAI:     Availability Target (Minimum Required Availability) [%]
                        # CONT:     Continuity Risk Target (Minimum Required Continuity Risk)
                        # CINT:     Continuity Risk sliding interval [seconds] (e.g 15s)
                        # Parameters for Open Service
                        elif Key== 'OS': 
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 10, 10, 
                            [0, -1,   -1,   -1,   -1,   -1,   0,   0, 0,            None], 
                            [1, 1000, 1000, 1000, 1000, 1000, 100, 1, Const.S_IN_D, None])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        elif Key== 'APVI': 
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 10, 10, 
                            [0, -1,   -1,   -1,   -1,   -1,   0,   0, 0,            None], 
                            [1, 1000, 1000, 1000, 1000, 1000, 100, 1, Const.S_IN_D, None])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        elif Key== 'LPV200': 
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 10, 10, 
                            [0, -1,   -1,   -1,   -1,   -1,   0,   0, 0,            None], 
                            [1, 1000, 1000, 1000, 1000, 1000, 100, 1, Const.S_IN_D, None])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        elif Key== 'CATI': 
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 10, 10, 
                            [0, -1,   -1,   -1,   -1,   -1,   0,   0, 0,            None], 
                            [1, 1000, 1000, 1000, 1000, 1000, 100, 1, Const.S_IN_D, None])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        elif Key== 'NPA': 
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 10, 10, 
                            [0, -1,   -1,   -1,   -1,   -1,   0,   0, 0,            None], 
                            [1, 1000, 1000, 1000, 1000, 1000, 100, 1, Const.S_IN_D, None])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        elif Key== 'MARITIME': 
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 10, 10, 
                            [0, -1,   -1,   -1,   -1,   -1,   0,   0, 0,            None], 
                            [1, 1000, 1000, 1000, 1000, 1000, 100, 1, Const.S_IN_D, None])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        elif Key== 'CUSTOM': 
                            # Check parameter and load it in Conf
                            Conf[Key] = checkConfParam(Key, Fields, 10, 10, 
                            [0, -1,   -1,   -1,   -1,   -1,   0,   0, 0,            None], 
                            [1, 1000, 1000, 1000, 1000, 1000, 100, 1, Const.S_IN_D, None])

                            # Increment number of read parameters
                            NReadParams = NReadParams + 1

                        else:
                            # Raise error
                            sys.stderr.write("ERROR: Incorrect conf file field " + Line)
                            sys.exit(-1)

                        # End of if Key=='INI_DATE':

    # # Check number of conf parameters
    # if (NReadParams != 39):
    #     # Raise error
    #     sys.stderr.write("ERROR: Wrong number of conf parameters\n")
    #     sys.exit(-1)

    return Conf

# End of readConf()

def processConf(Conf):
    
    # Purpose: process the configuration
       
    # Parameters
    # ==========
    # Conf: dict
    #         Dictionary containing configuration

    # Returns
    # =======
    # Conf: dict
    #         Dictionary containing configuration with
    #         Julian Days
    
    ConfCopy = Conf.copy()
    for Key in ConfCopy:
        Value = ConfCopy[Key]
        if Key == "INI_DATE" or Key == "END_DATE":
            ParamSplit = Value.split('/')

            # Compute Julian Day
            Conf[Key + "_JD"] = \
                int(round(
                    convertYearMonthDay2JulianDay(
                        int(ParamSplit[2]),
                        int(ParamSplit[1]),
                        int(ParamSplit[0]))
                    )
                )

    return Conf

def readRcvr(RcvrFile):
    
    # Purpose: read the RCVR Positions file
       
    # Parameters
    # ==========
    # RcvrFile: str
    #         Path to RCVR Positions file

    # Returns
    # =======
    # RcvrInfo: Dict
    #         RCVR Positions loaded in a dictionary
    
    # Initialize the variable to store the RCVR Positions
    RcvrInfo = OrderedDict({})

    # Open the file
    with open(RcvrFile, 'r') as f:
        # Read file
        Lines = f.readlines()

        # Parse each Line of configuration file
        for Line in Lines:
            # Check if Line is not a comment
            if Line[0]!='#':
                # Split Line in a list of Fields
                Fields=Line.rstrip('\n').split(' ')
                
                # Check if line is blank
                if '' in Fields:
                    Fields = list(filter(None, Fields))

                if Fields != None :
                    # if some parameter with its value missing, warn the user
                    if len(Fields) == 1:
                        sys.stderr.write("ERROR: Configuration file contains a parameter" \
                            "with no value: " + Line)
                        sys.exit(-1)

                    # if the line contains a conf parameter
                    elif len(Fields)!=0:
                        # Get RIMS acronym
                        Acr=Fields[0]

                        # Check if it is a valid acronym
                        if isinstance(Acr, str) and (len(Acr) <= 4):
                            # Extract receiver position
                            Rcvr = checkConfParam("RCVR " + Acr, Fields, 7, 7, 
                            [0, 0,                  Const.MIN_LON, Const.MIN_LAT, 0,   Const.MIN_MASK_ANGLE, 0], 
                            [1, Const.MAX_NUM_RCVR, Const.MAX_LON, Const.MAX_LAT, 1e4, Const.MAX_MASK_ANGLE, 100])
                            Rcvr.insert(0, Acr)
                            # If receiver is activated
                            if Rcvr[RcvrIdx["FLAG"]] == 1.0:
                                # Get ECEF coordinates
                                Rcvr.append(
                                    llh2xyz(\
                                        float(Rcvr[RcvrIdx["LON"]]),
                                        float(Rcvr[RcvrIdx["LAT"]]),
                                        float(Rcvr[RcvrIdx["ALT"]]),
                                    )
                                )

                                # Store receiver info
                                RcvrInfo[Acr] = Rcvr
                        
                        else:
                            # Bad acronym
                            sys.stderr.write("ERROR: Bad acronym in RCVR file: " + Acr + "\n")
                            sys.exit(-1)

        # End of for Line in Lines:

    # End of with open(RcvrFile, 'r') as f:

    # Check receivers to process
    if len(RcvrInfo) > 0:
        return RcvrInfo

    else:
        # ERROR, any receiver to process
        sys.stderr.write("ERROR: Any of the receiver is activated in RCVR file" + "\n")
        sys.exit(-1)

# End of readRcvr()


def splitLine(Line):
    
    # Purpose: split line
       
    # Parameters
    # ==========
    # Line: str
    #         string containing line read from file

    # Returns
    # =======
    # CfgFile: list
    #         line split using spaces as delimiter
    
    
    LineSplit = Line.split()

    return LineSplit

# End of splitLine()


def readObsEpoch(f):
    
    # Purpose: read one epoch of OBS file (all the LoS)
       
    # Parameters
    # ==========
    # f: file descriptor
    #         OBS file

    # Returns
    # =======
    # EpochInfo: list
    #         list of the split lines
    #         EpochInfo[1][1] is the second field of the 
    #         second line
    

    EpochInfo = []
    
    # Read one line
    Line = f.readline()
    if(not Line):
        return []
    LineSplit = splitLine(Line)
    Sod = LineSplit[ObsIdx["SOD"]]
    SodNext = Sod

    while SodNext == Sod:
        EpochInfo.append(LineSplit)
        Pointer = f.tell()
        Line = f.readline()
        LineSplit = splitLine(Line)
        try: 
            SodNext = LineSplit[ObsIdx["SOD"]]

        except:
            return EpochInfo

    f.seek(Pointer)

    return EpochInfo

# End of readObsEpoch()


def createOutputFile(Path, Hdr):
    
    # Purpose: open output file and write its header
       
    # Parameters
    # ==========
    # Path: str
    #         Path to file
    # Hdr: str
    #         File header

    # Returns
    # =======
    # f: File descriptor
    #         Descriptor of output file
    
    # Display Message
    print("INFO: Creating file: %s..." % Path)

    # Create output directory, if needed
    if not os.path.exists(os.path.dirname(Path)):
        os.makedirs(os.path.dirname(Path))

    # Open PREPRO OBS file
    f = open(Path, 'w')

    # Write header
    f.write(Hdr)

    return f

# End of createOutputFile()


def generatePreproFile(fpreprobs, PreproObsInfo):

    # Purpose: generate output file with Preprocessing results

    # Parameters
    # ==========
    # fpreprobs: file descriptor
    #         Descriptor for PREPRO OBS output file
    # PreproObsInfo: dict
    #         Dictionary containing Preprocessing info for the 
    #         current epoch

    # Returns
    # =======
    # Nothing

    # Loop over satellites
    for SatLabel, SatPreproObs in PreproObsInfo.items():
        # Prepare outputs
        Outputs = OrderedDict({})
        Outputs["SOD"] = SatPreproObs["Sod"]
        Outputs["DOY"] = SatPreproObs["Doy"]
        Outputs["CONST"] = SatLabel[0]
        Outputs["PRN"] = int(SatLabel[1:])
        Outputs["ELEV"] = SatPreproObs["Elevation"]
        Outputs["AZIM"] = SatPreproObs["Azimuth"]
        Outputs["VALID"] = SatPreproObs["ValidL1"]
        Outputs["REJECT"] = SatPreproObs["RejectionCause"]
        Outputs["STATUS"] = SatPreproObs["Status"]
        Outputs["C1"] = SatPreproObs["C1"]
        Outputs["C1SMOOTHED"] = SatPreproObs["SmoothC1"]
        Outputs["L1"] = SatPreproObs["L1Meters"]
        Outputs["S1"] = SatPreproObs["S1"]
        Outputs["CODE RATE"] = SatPreproObs["RangeRateL1"]
        Outputs["CODE ACC"] = SatPreproObs["RangeRateStepL1"]
        Outputs["PHASE RATE"] = SatPreproObs["PhaseRateL1"]
        Outputs["PHASE ACC"] = SatPreproObs["PhaseRateStepL1"]
        Outputs["GEOM FREE"] = SatPreproObs["GeomFree"]
        Outputs["VTEC RATE"] = SatPreproObs["VtecRate"]
        Outputs["iAATR"] = SatPreproObs["iAATR"]

        # Write line
        for i, result in enumerate(Outputs):
            fpreprobs.write(((PreproFmt[i] + " ") % Outputs[result]))

        fpreprobs.write("\n")

# End of generatePreproFile
