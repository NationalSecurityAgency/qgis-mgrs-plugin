def classFactory(iface):
    from .mgrsCapture import MGRSCapture
    return MGRSCapture(iface)
