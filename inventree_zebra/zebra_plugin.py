"""
Label printing plugin for InvenTree.
Supports direct printing of labels on label printers
"""
# translation
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator
from django.core.validators import MaxValueValidator

# InvenTree plugin libs
from plugin import InvenTreePlugin
from plugin.mixins import LabelPrintingMixin, SettingsMixin

# Zebra printer support
import zpl
import socket

from inventree_zebra.version import ZEBRA_PLUGIN_VERSION

class ZebraLabelPlugin(LabelPrintingMixin, SettingsMixin, InvenTreePlugin):


    AUTHOR = "Michael Buchmann"
    DESCRIPTION = "Label printing plugin for Zebra printers"
    VERSION = ZEBRA_PLUGIN_VERSION
    NAME = "Zebra"
    SLUG = "zebra"
    TITLE = "Zebra Label Printer"

    SETTINGS = {
        'CONNECTION': {
            'name': _('Printer Interface'),
            'description': _('Select local or network printer'),
            'choices': [('local', 'Local printer e.g. USB'), ('network', 'Network printer with IP address')],
            'default': 'local',
        },
        'IP_ADDRESS': {
            'name': _('IP Address'),
            'description': _('IP address in case of network printer'),
            'default': '',
        },
        'PORT': {
            'name': _('Port'),
            'description': _('Network port in case of network printer'),
            'default': '9100',
        },
        'LOCAL_IF': {
            'name': _('Local Device'),
            'description': _('Interface of local printer'),
            'default': '/dev/usb/lp0',
        },
        'THRESHOLD': {
            'name': _('Threshold'),
            'description': _('Threshold for converting grayscale to BW (0-255)'),
            'validator': [int, MinValueValidator(0), MaxValueValidator(255)],
            'default': 200,
        },
        'DARKNESS': {
            'name': _('Darkness'),
            'description': _('Darkness of the print out. 0-30'),
            'validator': [int, MinValueValidator(0), MaxValueValidator(30)],
            'default': 20,
        },
        'DPMM': {
            'name': _('Dots per mm'),
            'description': _('The resolution of the printer'),
            'choices': [(8,'8 dots per mm'),(12,'12 dots per mm'),(24,'24 dots per mm')],
            'default': 8,
        },
        'PRINTER_INIT': {
            'name': _('Printer Init'),
            'description': _('Additional ZPL commands sent to the printer. Use carefully!'),
            'default': '~TA000~JSN^LT0^MNW^MTT^PMN^PON^PR2,2^LRN',
        },
    }

    def print_label(self, **kwargs):

        # Read settings
        ip_address = self.get_setting('IP_ADDRESS')
        connection = self.get_setting('CONNECTION')
        interface = self.get_setting('LOCAL_IF')
        port = int(self.get_setting('PORT'))
        threshold = self.get_setting('THRESHOLD')
        darkness = self.get_setting('DARKNESS')
        dpmm = int(self.get_setting('DPMM'))
        printer_init = self.get_setting('PRINTER_INIT')
        label_image = kwargs['png_file']

        # Extract width (x) and height (y) information.
        width = kwargs['width']
        height = kwargs['height']

        # Set the darkness
        fn = lambda x: 255 if x > threshold else 0
        label_image = label_image.convert('L').point(fn, mode='1')

        # Uncomment this if you need the intermetiate png file for debugging.
        # label_image.save('/home/user/label.png')

        # Convert image to Zebra zpl
        l = zpl.Label(height, width, dpmm)
        l.set_darkness(darkness)
        l.labelhome(0,0)
        l.zpl_raw(printer_init)
        l.origin(0,0)
        l.write_graphic(label_image, width)
        l.endorigin()

        # Uncomment this if you need the intermetiate zpl file for debugging.
        # datafile=open('/home/user/label.txt','w')
        # datafile.write(l.dumpZPL())
        # datafile.close()

        # Send the label to the printer
        if(connection == 'local'):
            try:
                pass
                printer=open(interface,'w')
                printer.write(l.dumpZPL())
                printer.close()
            except Exception as error:
                raise ConnectionError('Error connecting to local printer: ' + str(error))
        elif(connection=='network'):
            try:
                mysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                mysocket.connect((ip_address, port))
                data = l.dumpZPL()
                mysocket.send(data.encode())
                mysocket.close()
            except Exception as error:
                raise ConnectionError('Error connecting to network printer: ' + str(error))
        else:
            print('Unknown Interface')
