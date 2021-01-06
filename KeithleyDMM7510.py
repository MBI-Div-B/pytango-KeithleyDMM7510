#!/usr/bin/python3 -u
# coding: utf8
from tango import AttrWriteType, DevState, DispLevel
from tango.server import Device, attribute, command, device_property

import pyvisa
from enum import IntEnum


class MeasurementType(IntEnum):
    VoltDC = 0
    VoltAC = 1
    CurrDC = 2
    CurrAC = 3


class KeithleyDMM7510(Device):
    '''KeithleyDMM7510

    This controls the Keithley DMM7510 digital multimeter

    '''

    Resource = device_property(dtype=str, default_value='TCPIP::192.168.1.201::inst0::INSTR')

    measurement_type = attribute(
        dtype=MeasurementType,
        label='Measurement Type',
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.OPERATOR,
        doc='Sets the measurement type.'
    )
    
    range = attribute(
        dtype=float,
        label='Range',
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.OPERATOR,
        format='%6.3e',
        doc='Range according to measurement type. Device automatically selects nearest range.'
    )
    
    trigger_status = attribute(
        dtype=str,
        label='Trigger Status',
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR
    )
    
    last_value = attribute(
        dtype=float,
        format='%12.9f',
        label='Value',
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR
    )
    
    stats_average = attribute(
        dtype=float,
        format='%9:6e',
        label='Stats Average',
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR
    )
    
    stats_peak2peak = attribute(
        dtype=float,
        format='%9:6e',
        label='Stats Peak2Peak',
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR
    )
    
    stats_std = attribute(
        dtype=float,
        format='%9:6e',
        label='Stats STD',
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR
    )
    
    stats_span = attribute(
        dtype=float,
        format='%d',
        label='Stats Span',
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR
    )
    
    stats_min = attribute(
        dtype=float,
        format='%9:6e',
        label='Stats Min',
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR
    )
    
    stats_max = attribute(
        dtype=float,
        format='%9:6e',
        label='Stats Max',
        access=AttrWriteType.READ,
        display_level=DispLevel.OPERATOR
    )

    def init_device(self):
        super().init_device()
        self.info_stream('Connecting to resource {:s} ...'.format(self.Resource))
        try:
            rm = pyvisa.ResourceManager()
            self.dmm = rm.open_resource(self.Resource)
            self.dmm.read_termination = '\n'
            
            idn = self.dmm.query('*IDN?')
            self.info_stream('Connection established: {:s}'.format(idn))
            self.set_state(DevState.ON)
        except:
            self.error_stream('Cannot connect!')
            self.set_state(DevState.OFF)

        self.__sense_prefix = ''
        self.__set_sense_prefix(self.read_measurement_type())
        self.read()
            
    def delete_device(self):
        self.set_state(DevState.OFF)
        del self.dmm
        self.info_stream('Device was deleted!')
        
    def read_measurement_type(self):
        meas_type = self.dmm.query('SENS:FUNC?').strip('\"')
        if meas_type == 'VOLT:DC':
            return 0
        elif meas_type == 'VOLT:AC':
            return 1
        elif meas_type == 'CURR:DC':
            return 2
        elif meas_type == 'CURR:AC':
            return 3
        else:
            return -1

    def write_measurement_type(self, value):        
        if value == 0:
            cmd = 'VOLT:DC'
        elif value == 1:
            cmd = 'VOLT:AC'
        elif value == 2:
            cmd = 'CURR:DC'
        elif value == 3:
            cmd = 'CURR:AC'
        
        self.dmm.write(':SENS:FUNC "{:s}"'.format(cmd))
        self.__set_sense_prefix(value)

    def read_range(self):
        return float(self.dmm.query('SENS:{:s}:RANG?'.format(self.__sense_prefix)))

    def write_range(self, value):
        self.dmm.write('SENS:{:s}:RANG {:f}'.format(self.__sense_prefix, value))

    def read_trigger_status(self):
        return self.dmm.query(':TRIG:STAT?').split(';')[0]

    def read_last_value(self):
        return float(self.dmm.query(':FETC?'))

    def read_stats_average(self):
        return float(self.dmm.query(':TRAC:STAT:AVER?'))

    def read_stats_peak2peak(self):
        return float(self.dmm.query(':TRAC:STAT:PK2P?'))

    def read_stats_std(self):
        return float(self.dmm.query(':TRAC:STAT:STDD?'))

    def read_stats_span(self):
        return float(self.dmm.query(':TRAC:ACT?'))

    def read_stats_min(self):
        return float(self.dmm.query(':TRAC:STAT:MIN?'))

    def read_stats_max(self):
        return float(self.dmm.query(':TRAC:STAT:MAX?'))

    @command
    def trigger_abort(self):
        self.dmm.write(':TRIG:ABOR')

    @command
    def clear_stats(self):
        self.dmm.write(':TRAC:STAT:CLE')

    @command
    def clear_trace(self):
        self.dmm.write(':TRAC:CLE')        
      
    @command
    def read(self):
        self.__last_value = float(self.dmm.query(':READ?'))

    @command(dtype_in=float, doc_in="duration")
    def trigger_duration(self, duration):
        self.dmm.write('TRIG:LOAD "DurationLoop", {:f}, 0'.format(duration))
        self.dmm.write('INIT')

    def __set_sense_prefix(self, value):
        if value == 0:
            self.__sense_prefix = 'VOLT'
        elif value == 1:
            self.__sense_prefix = 'VOLT'
        elif value == 2:
            self.__sense_prefix = 'CURR'
        elif value == 3:
            self.__sense_prefix = 'CURR'
        
# start the server
if __name__ == "__main__":
    KeithleyDMM7510.run_server()
