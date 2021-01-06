#!/usr/bin/python3 -u
from tango import AttrWriteType, DevState, DispLevel
from tango.server import Device, attribute, command, device_property

import instruments as ik
from enum import IntEnum


class Mode(IntEnum):
    manual = 0
    auto = 1
    single = 2
    repeat = 3
    external = 4


class TriggerMode(IntEnum):
    internal = 0
    external = 1


class ExTriggerMode(IntEnum):
    shutter = 0
    controller = 1


class BaudRate(IntEnum):
    _9600 = 0
    _115200 = 1


class ThorlabsSC10(Device):
    '''ThorlabsSC10

    This controls the Thorlabs SC10 shutter controller

    '''

    Port = device_property(dtype=str, default_value='/dev/ttyUSB0')
    Baudrate = device_property(dtype=int, default_value=9600)
    Timeout = device_property(dtype=float, default_value=1)
    
    # device attributes
    enabled = attribute(
        dtype='bool',
        label='Enabled',
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR,
        doc='Returns "0" if the shutter is disabled and "1" if enabled',
    )
    
    open = attribute(
        dtype='bool',
        label='Open',
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR,
        doc='Returns "1" if the shutter is open or "0" if cloesed.',
    )
    
    interlock = attribute(
        dtype='bool',
        label='Interlock',
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR,
        doc='Returns "1" if interlock is tripped, otherwise "0".'
    )
    
    repeat_count = attribute(
        dtype='int',
        label='Repeat Count',
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.OPERATOR,
        min_value=1,
        max_value=99,
        doc='Repeat count for repeat mode. The value nmust be from 1 to 99.'
    )
    
    baudrate = attribute(
        dtype=BaudRate,
        label='Baud Rate',
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.EXPERT,
        doc='Either 9600 or 115200'
    )

    mode = attribute(
        dtype=Mode,
        label='Mode',
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.OPERATOR,
        doc='''The operating mode values:
mode=1: Sets the unit to Manual Mode
mode=2: Sets the unit to Auto Mode
mode=3: Sets the unit to Single Mode
mode=4: Sets the unit to Repeat Mode
mode=5: Sets the unit to the External Gate Mode
'''
    )
        
    trigger_mode = attribute(
        dtype=TriggerMode,
        label='Trigger Mode',
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.OPERATOR,
        doc='''The trigger mode (see section 4.1.4 for more details)
trig=0: Internal trigger mode
trig=1: External trigger mode
'''
    )

    extrigger_mode = attribute(
        dtype=ExTriggerMode,
        label='Ex-Trigger Mode',
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.OPERATOR,
        doc='''The ex-trigger mode
xto=0: Trigger Out TTL follows shutter output.
xto=1: Trigger Out TTL follows controller output. 
'''
    )

    open_duration = attribute(
        dtype='int',
        format='%6d',
        label='Open Duration',
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.OPERATOR,
        min_value=0,
        max_value=999999,
        unit='ms',
        doc='The shutter open time.'
    )

    close_duration = attribute(
        dtype='int',
        format='%6d',
        label='Close Duration',
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.OPERATOR,
        min_value=0,
        max_value=999999,
        unit='ms',
        doc='The shutter close time.'
    )

    def init_device(self):
        Device.init_device(self)
        self.__enabled = False
        self.__open = False
        self.__interlock = False
        self.info_stream('Connecting to serial port {:s} with baudrate {:d} ...'.format(self.Port, self.Baudrate))
        try:
            self.sc = ik.thorlabs.SC10.open_serial(self.Port, self.Baudrate, timeout=self.Timeout)
            self.sc.prompt = '> '
            name = self.sc.query('id?')
            self.info_stream('Connection established: {:s}'.format(name))
            self.set_state(DevState.ON)
        except:
            self.error_stream('Cannot connect!')
            self.set_state(DevState.OFF)
            
            
    def delete_device(self):
        self.set_state(DevState.OFF)
        del self.sc
        self.info_stream('Device was deleted!')

    def always_executed_hook(self):
        self.__enabled = bool(int(self.sc.query('ens?')))
        self.__open = not bool(int(self.sc.query('closed?')))
        self.__interlock = bool(int(self.sc.query('interlock?')))
        if self.__open:
            self.set_status('Device is OPEN')
            self.set_state(DevState.OPEN)
            return DevState.OPEN
        else:
            self.set_status('Device is CLOSED')
            self.set_state(DevState.CLOSE)

    def read_enabled(self):
        return self.__enabled

    def read_open(self):
        return self.__open

    def read_interlock(self):
        return self.__interlock

    def read_baudrate(self):
        return BaudRate._115200 if bool(int(self.sc.query('baud?'))) else BaudRate._9600

    def write_baudrate(self, value):
        self.sc.sendcmd('baud={:d}'.format(value))

    def read_mode(self):
        return int(self.sc.query('mode?'))-1

    def write_mode(self, value):
        self.sc.sendcmd('mode={:d}'.format(value+1))

    def read_trigger_mode(self):
        return int(self.sc.query('trig?'))

    def write_trigger_mode(self, value):
        self.sc.sendcmd('trig={:d}'.format(value))
        
    def read_extrigger_mode(self):
        return int(self.sc.query('xto?'))

    def write_extrigger_mode(self, value):
        self.sc.sendcmd('xto={:d}'.format(value))
        
    def read_repeat_count(self):
        return int(self.sc.query('rep?'))

    def write_repeat_count(self, value):
        self.sc.sendcmd('rep={:d}'.format(value))

    def read_open_duration(self):
        return int(self.sc.query('open?'))

    def write_open_duration(self, value):
        self.sc.sendcmd('open={:d}'.format(value))

    def read_close_duration(self):
        return int(self.sc.query('shut?'))

    def write_close_duration(self, value):
        self.sc.sendcmd('shut={:d}'.format(value))


    @command()
    def enable(self):
        if self.__enabled:
            self.debug_stream('shutter already enabled')
        else:
            self.debug_stream('enable shutter')
            self.sc.sendcmd('ens')

    @command()
    def disable(self):
        if self.__enabled:
            self.debug_stream('disable shutter')
            self.sc.sendcmd('ens')
        else:
            self.debug_stream('shutter already disabled')
        
    @command(doc_in='Store config (ex. mode, open time, closed time) into EEPROM.')
    def store_config(self):
        self.debug_stream('store config')
        self.sc.sendcmd('savp')
        
    @command(doc_in='Load config from EEPROM.')    
    def restore_config(self):
        self.debug_stream('load config')
        self.sc.sendcmd('resp')
        
        
# start the server
if __name__ == "__main__":
    ThorlabsSC10.run_server()
