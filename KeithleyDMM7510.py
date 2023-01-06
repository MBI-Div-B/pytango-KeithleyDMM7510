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
    DigVolt = 4
    DigCurr = 5


class KeithleyDMM7510(Device):
    '''KeithleyDMM7510

    This controls the Keithley DMM7510 digital multimeter

    '''

    Resource = device_property(dtype=str, default_value='TCPIP::192.168.1.201::inst0::INSTR')
    DigitizerCounts = device_property(dtype=int, default_value=15)

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
    
    auto_range = attribute(
        dtype='bool',
        label='Auto Range',
        access=AttrWriteType.READ_WRITE,
        display_level=DispLevel.OPERATOR,
        doc='Enable/Disable auto range.'
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
        elif meas_type == 'NONE':
            digi_type = self.dmm.query('SENS:DIG:FUNC?').strip('\"')
            if digi_type == 'VOLT':
                return 4
            elif digi_type == 'CURR':
                return 5
            else:
                return -1
        else:
            return -1

    def write_measurement_type(self, value):        
        if value == 0:
            self.dmm.write(':SENS:FUNC "VOLT:DC"')
        elif value == 1:
            self.dmm.write(':SENS:FUNC "VOLT:AC"')
        elif value == 2:
            self.dmm.write(':SENS:FUNC "CURR:DC"')
        elif value == 3:
            self.dmm.write(':SENS:FUNC "CURR:AC"')
        elif value == 4:
                self.dmm.write(':SENS:DIG:FUNC "VOLT"')
        elif value == 5:
                self.dmm.write(':SENS:DIG:FUNC "CURR"')
        
        self.__set_sense_prefix(value)

    def read_range(self):
        if self.__sense_prefix == 'DIG':
            return -1
        else:
            return float(self.dmm.query('SENS:{:s}:RANG?'.format(self.__sense_prefix)))

    def write_range(self, value):
        if self.__sense_prefix == 'DIG':
            return
        else:
            self.dmm.write('SENS:{:s}:RANG {:f}'.format(self.__sense_prefix, value))

    def read_auto_range(self):
        if self.__sense_prefix == 'DIG':
            return
        else:
            return int(self.dmm.query('SENS:{:s}:RANG:AUTO?'.format(self.__sense_prefix)))

    def write_auto_range(self, value):
        if self.__sense_prefix == 'DIG':
            return
        else:
            self.dmm.write('SENS:{:s}:RANG:AUTO {:d}'.format(self.__sense_prefix, int(value)))

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
    def trigger_duration_loop(self, duration):
        self.dmm.write('TRIG:LOAD "DurationLoop", {:f}, 0'.format(duration))
        
    @command(dtype_in=int, doc_in="counts")
    def trigger_external(self, counts):
        self.dmm.write(':TRIG:LOAD "EMPTY"')
        self.dmm.write(':TRIG:BLOC:BUFF:CLEAR 1')
        self.dmm.write(':TRIGger:BLOCk:WAIT 2, EXT, ENT')
        self.dmm.write(':TRIG:EXT:IN:EDGE RIS')
        self.dmm.write(':TRIG:BLOC:DEL:CONS 3, 0')
        self.dmm.write(':TRIG:BLOC:DIGITIZE 4, "defbuffer1", {:d}'.format(self.DigitizerCounts)) 
        self.dmm.write(':TRIG:BLOC:BRAN:COUN 5, {:d}, 2'.format(counts))

    @command
    def trigger_init(self):
        self.dmm.write('INIT')

    @command
    def continuous(self):
        self.dmm.write('TRIG:CONT REST')

    def __set_sense_prefix(self, value):
        if value == 0:
            self.__sense_prefix = 'VOLT'
        elif value == 1:
            self.__sense_prefix = 'VOLT'
        elif value == 2:
            self.__sense_prefix = 'CURR'
        elif value == 3:
            self.__sense_prefix = 'CURR'
        else:
            self.__sense_prefix = 'DIG'
        
# start the server
if __name__ == "__main__":
    KeithleyDMM7510.run_server()
