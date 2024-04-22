import asyncio
import datetime
import struct
from bleak import BleakClient, BleakScanner

CHAR_BAT          = "00002a19-0000-1000-8000-00805f9b34fb"

CHAR_WATER_START  = "39e1f906-84a8-11e2-afba-0002a5d5c51b"
CHAR_WATER_LEVEL  = "39e1f907-84a8-11e2-afba-0002a5d5c51b"

CHAR_LIGHT        = "39e1fa01-84a8-11e2-afba-0002a5d5c51b" 
CHAR_SOIL_CONDU   = "39e1fa02-84a8-11e2-afba-0002a5d5c51b"
CHAR_SOIL_TEMP    = "39e1fa03-84a8-11e2-afba-0002a5d5c51b"
CHAR_AIR_TEMP     = "39e1fa04-84a8-11e2-afba-0002a5d5c51b"

CHAR_SOIL_MOIST   = "39e1fa09-84a8-11e2-afba-0002a5d5c51b"

CHAR_AIR_TEMP_CAL = "39e1fa0a-84a8-11e2-afba-0002a5d5c51b"
CHAR_LIGHT_CAL    = "39e1fa0b-84a8-11e2-afba-0002a5d5c51b"

def map_range(x, in_min, in_max, out_min, out_max):
  return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

async def _search_for_pot():
    print("Searching for Parrot pot...")
    ret = None

    devices = await BleakScanner.discover()
    for device in devices:
        # print(device.name)
        if device.name == "Parrot pot 2d37":
            ret = device

    if ret is not None:
        print("Parrot pot found!")
    else:
        print("Parrot has not been found.")
        assert ret is not None

    return ret


async def check_pot():
    # t0 = datetime.datetime.now()
    # queue = asyncio.Queue()

    pot = await _search_for_pot()
    print(pot)
    async with BleakClient(pot,  timeout= 100.0) as client:
        # packet_size = (client.mtu_size - 3)
        
        print("Get water level:")
        water = await client.read_gatt_char(CHAR_WATER_LEVEL)
        water = int.from_bytes(water, byteorder='little', signed=False)
        print(f"Water: {((water*2.2) / 100.0):.2f}L / 2.2L")
        
        print("Get soil conduc:")
        val = await client.read_gatt_char(CHAR_SOIL_CONDU)
        val = int.from_bytes(val, byteorder='little', signed=False)
        if (val < 1500):
            val = 1500;
        if (val > 2036):
            val = 2036;
        val = map_range(val, 2036, 1500, 0, 1000);
        print(f"Soil conduc: {val}uS/cm")
        
        print("Get soil moisture:")
        val = await client.read_gatt_char(CHAR_SOIL_MOIST)
        val = struct.unpack('f', val)[0]
        print(f"Soil moisture: {val:.2f}%")
        
        if val < 40 and val != 0:
            print("Water the plant")
            await client.write_gatt_char(CHAR_WATER_START, bytearray(b'\x08\x00'))

if __name__ == '__main__':
    asyncio.run(check_pot())