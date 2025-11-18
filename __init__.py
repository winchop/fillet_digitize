def classFactory(iface):
    from .fillet_digitize import FilletDigitizePlugin
    return FilletDigitizePlugin(iface)