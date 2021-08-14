
import numpy as np

def computeIonoMappingFunction(ElevDeg):
    EARTH_RADIUS = 6378136.3
    IONO_HEIGHT = 350000.0

    ElevRad = ElevDeg * np.pi / 180.0

    Fpp = (1.0-((EARTH_RADIUS * np.cos(ElevRad))/\
                 (EARTH_RADIUS + IONO_HEIGHT))**2)**(-0.5)

    return Fpp