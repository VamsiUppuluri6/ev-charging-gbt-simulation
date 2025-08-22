from pymodbus.client.sync import ModbusSerialClient

client = ModbusSerialClient(
    method='rtu',
    port='/dev/ttyUSB0',
    baudrate=9600,
    timeout=3,
    parity='N',
    stopbits=1,
    bytesize=8
)
jj=9100+150

def smps(jj,onoff):
 for dev in  range(1,4):   
  if client.connect():  # Trying for connect to Modbus Server/Slave
    '''Reading from a holding register with the below content.'''
    re=client.write_register(2,onoff,unit=dev)
    re=client.write_register(0,jj,unit=dev)
    res = client.read_holding_registers(address=0, count=1, unit=dev)

    '''Reading from a discrete register with the below content.'''
    # res = client.read_discrete_inputs(address=1, count=1, unit=1)

    if not res.isError():
        print(res.registers)
    else:
        print(res)

  else:
    print('Cannot connect to the Modbus Server/Slave')
smps(jj,0)
