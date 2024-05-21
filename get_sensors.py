import asyncio
import struct
from bleak import BleakClient, BleakScanner

from ha_mqtt_discoverable import Settings, DeviceInfo
from ha_mqtt_discoverable.sensors import Sensor, SensorInfo, Button, ButtonInfo
from paho.mqtt.client import Client, MQTTMessage
from time import sleep
import traceback

mqtt_settings = Settings.MQTT(

)

class SensorInfoExtra(SensorInfo):
    suggested_display_precision: int

SERV_BAT          = "0000180f-0000-1000-8000-00805f9b34fb"
CHAR_BAT          = "00002a19-0000-1000-8000-00805f9b34fb"
CHAR_BAT_H        = 0x004a

SERV_WATER        = "39e1f900-84a8-11e2-afba-0002a5d5c51b"
CHAR_WATER_START  = "39e1f906-84a8-11e2-afba-0002a5d5c51b"
CHAR_WATER_LEVEL  = "39e1f907-84a8-11e2-afba-0002a5d5c51b"

CHAR_LIGHT        = "39e1fa01-84a8-11e2-afba-0002a5d5c51b" 
CHAR_SOIL_CONDU   = "39e1fa02-84a8-11e2-afba-0002a5d5c51b"
CHAR_SOIL_TEMP    = "39e1fa03-84a8-11e2-afba-0002a5d5c51b"
CHAR_AIR_TEMP     = "39e1fa04-84a8-11e2-afba-0002a5d5c51b"

CHAR_SOIL_MOIST   = "39e1fa09-84a8-11e2-afba-0002a5d5c51b"

CHAR_AIR_TEMP_CAL = "39e1fa0a-84a8-11e2-afba-0002a5d5c51b"
CHAR_LIGHT_CAL    = "39e1fa0b-84a8-11e2-afba-0002a5d5c51b"

"""
attr handle: 0x0001, end grp handle: 0x000b uuid: 00001800-0000-1000-8000-00805f9b34fb
attr handle: 0x000c, end grp handle: 0x000f uuid: 00001801-0000-1000-8000-00805f9b34fb
attr handle: 0x0010, end grp handle: 0x0022 uuid: 0000180a-0000-1000-8000-00805f9b34fb
attr handle: 0x0023, end grp handle: 0x0048 uuid: 39e1fa00-84a8-11e2-afba-0002a5d5c51b
attr handle: 0x0049, end grp handle: 0x004c uuid: 0000180f-0000-1000-8000-00805f9b34fb
attr handle: 0x004d, end grp handle: 0x005b uuid: 39e1fc00-84a8-11e2-afba-0002a5d5c51b
attr handle: 0x005c, end grp handle: 0x0066 uuid: 39e1fb00-84a8-11e2-afba-0002a5d5c51b
attr handle: 0x0067, end grp handle: 0x006b uuid: 39e1fd00-84a8-11e2-afba-0002a5d5c51b
attr handle: 0x006c, end grp handle: 0x0076 uuid: 39e1fe00-84a8-11e2-afba-0002a5d5c51b
attr handle: 0x0077, end grp handle: 0x009d uuid: 39e1f900-84a8-11e2-afba-0002a5d5c51b
attr handle: 0x009e, end grp handle: 0x00b4 uuid: 39e1fd80-84a8-11e2-afba-0002a5d5c51b
attr handle: 0x00b5, end grp handle: 0xffff uuid: f000ffc0-0451-4000-b000-000000000000

handle: 0x0002, char properties: 0x02, char value handle: 0x0003, uuid: 00002a00-0000-1000-8000-00805f9b34fb
handle: 0x0004, char properties: 0x02, char value handle: 0x0005, uuid: 00002a01-0000-1000-8000-00805f9b34fb
handle: 0x0006, char properties: 0x02, char value handle: 0x0007, uuid: 00002a02-0000-1000-8000-00805f9b34fb
handle: 0x0008, char properties: 0x08, char value handle: 0x0009, uuid: 00002a03-0000-1000-8000-00805f9b34fb
handle: 0x000a, char properties: 0x02, char value handle: 0x000b, uuid: 00002a04-0000-1000-8000-00805f9b34fb
handle: 0x000d, char properties: 0x20, char value handle: 0x000e, uuid: 00002a05-0000-1000-8000-00805f9b34fb
handle: 0x0011, char properties: 0x02, char value handle: 0x0012, uuid: 00002a23-0000-1000-8000-00805f9b34fb
handle: 0x0013, char properties: 0x02, char value handle: 0x0014, uuid: 00002a24-0000-1000-8000-00805f9b34fb
handle: 0x0015, char properties: 0x02, char value handle: 0x0016, uuid: 00002a25-0000-1000-8000-00805f9b34fb
handle: 0x0017, char properties: 0x02, char value handle: 0x0018, uuid: 00002a26-0000-1000-8000-00805f9b34fb
handle: 0x0019, char properties: 0x02, char value handle: 0x001a, uuid: 00002a27-0000-1000-8000-00805f9b34fb
handle: 0x001b, char properties: 0x02, char value handle: 0x001c, uuid: 00002a28-0000-1000-8000-00805f9b34fb
handle: 0x001d, char properties: 0x02, char value handle: 0x001e, uuid: 00002a29-0000-1000-8000-00805f9b34fb
handle: 0x001f, char properties: 0x02, char value handle: 0x0020, uuid: 00002a2a-0000-1000-8000-00805f9b34fb
handle: 0x0021, char properties: 0x02, char value handle: 0x0022, uuid: 00002a50-0000-1000-8000-00805f9b34fb
handle: 0x0024, char properties: 0x12, char value handle: 0x0025, uuid: 39e1fa01-84a8-11e2-afba-0002a5d5c51b
handle: 0x0027, char properties: 0x12, char value handle: 0x0028, uuid: 39e1fa0f-84a8-11e2-afba-0002a5d5c51b
handle: 0x002a, char properties: 0x12, char value handle: 0x002b, uuid: 39e1fa10-84a8-11e2-afba-0002a5d5c51b
handle: 0x002d, char properties: 0x12, char value handle: 0x002e, uuid: 39e1fa11-84a8-11e2-afba-0002a5d5c51b
handle: 0x0030, char properties: 0x12, char value handle: 0x0031, uuid: 39e1fa02-84a8-11e2-afba-0002a5d5c51b
handle: 0x0033, char properties: 0x12, char value handle: 0x0034, uuid: 39e1fa03-84a8-11e2-afba-0002a5d5c51b
handle: 0x0036, char properties: 0x12, char value handle: 0x0037, uuid: 39e1fa04-84a8-11e2-afba-0002a5d5c51b
handle: 0x0039, char properties: 0x12, char value handle: 0x003a, uuid: 39e1fa05-84a8-11e2-afba-0002a5d5c51b
handle: 0x003c, char properties: 0x0a, char value handle: 0x003d, uuid: 39e1fa06-84a8-11e2-afba-0002a5d5c51b
handle: 0x003e, char properties: 0x0a, char value handle: 0x003f, uuid: 39e1fa07-84a8-11e2-afba-0002a5d5c51b
handle: 0x0040, char properties: 0x12, char value handle: 0x0041, uuid: 39e1fa09-84a8-11e2-afba-0002a5d5c51b
handle: 0x0043, char properties: 0x12, char value handle: 0x0044, uuid: 39e1fa0a-84a8-11e2-afba-0002a5d5c51b
handle: 0x0046, char properties: 0x12, char value handle: 0x0047, uuid: 39e1fa0b-84a8-11e2-afba-0002a5d5c51b
handle: 0x004a, char properties: 0x12, char value handle: 0x004b, uuid: 00002a19-0000-1000-8000-00805f9b34fb
handle: 0x004e, char properties: 0x02, char value handle: 0x004f, uuid: 39e1fc01-84a8-11e2-afba-0002a5d5c51b
handle: 0x0050, char properties: 0x02, char value handle: 0x0051, uuid: 39e1fc02-84a8-11e2-afba-0002a5d5c51b
handle: 0x0052, char properties: 0x0a, char value handle: 0x0053, uuid: 39e1fc03-84a8-11e2-afba-0002a5d5c51b
handle: 0x0054, char properties: 0x02, char value handle: 0x0055, uuid: 39e1fc04-84a8-11e2-afba-0002a5d5c51b
handle: 0x0056, char properties: 0x02, char value handle: 0x0057, uuid: 39e1fc05-84a8-11e2-afba-0002a5d5c51b
handle: 0x0058, char properties: 0x02, char value handle: 0x0059, uuid: 39e1fc06-84a8-11e2-afba-0002a5d5c51b
handle: 0x005a, char properties: 0x02, char value handle: 0x005b, uuid: 39e1fc07-84a8-11e2-afba-0002a5d5c51b
handle: 0x005d, char properties: 0x10, char value handle: 0x005e, uuid: 39e1fb01-84a8-11e2-afba-0002a5d5c51b
handle: 0x0060, char properties: 0x12, char value handle: 0x0061, uuid: 39e1fb02-84a8-11e2-afba-0002a5d5c51b
handle: 0x0063, char properties: 0x0a, char value handle: 0x0064, uuid: 39e1fb03-84a8-11e2-afba-0002a5d5c51b
handle: 0x0065, char properties: 0x0a, char value handle: 0x0066, uuid: 39e1fb04-84a8-11e2-afba-0002a5d5c51b
handle: 0x0068, char properties: 0x02, char value handle: 0x0069, uuid: 39e1fd01-84a8-11e2-afba-0002a5d5c51b
handle: 0x006a, char properties: 0x0a, char value handle: 0x006b, uuid: 39e1fd02-84a8-11e2-afba-0002a5d5c51b
handle: 0x006d, char properties: 0x02, char value handle: 0x006e, uuid: 39e1fe01-84a8-11e2-afba-0002a5d5c51b
handle: 0x006f, char properties: 0x02, char value handle: 0x0070, uuid: 39e1fe03-84a8-11e2-afba-0002a5d5c51b
handle: 0x0071, char properties: 0x02, char value handle: 0x0072, uuid: 39e1fe04-84a8-11e2-afba-0002a5d5c51b
handle: 0x0073, char properties: 0x02, char value handle: 0x0074, uuid: 39e1fe05-84a8-11e2-afba-0002a5d5c51b
handle: 0x0075, char properties: 0x0a, char value handle: 0x0076, uuid: 39e1fe06-84a8-11e2-afba-0002a5d5c51b
handle: 0x0078, char properties: 0x0a, char value handle: 0x0079, uuid: 39e1f901-84a8-11e2-afba-0002a5d5c51b
handle: 0x007a, char properties: 0x0a, char value handle: 0x007b, uuid: 39e1f902-84a8-11e2-afba-0002a5d5c51b
handle: 0x007c, char properties: 0x0a, char value handle: 0x007d, uuid: 39e1f903-84a8-11e2-afba-0002a5d5c51b
handle: 0x007e, char properties: 0x0a, char value handle: 0x007f, uuid: 39e1f904-84a8-11e2-afba-0002a5d5c51b
handle: 0x0080, char properties: 0x0a, char value handle: 0x0081, uuid: 39e1f905-84a8-11e2-afba-0002a5d5c51b
handle: 0x0082, char properties: 0x0a, char value handle: 0x0083, uuid: 39e1f90a-84a8-11e2-afba-0002a5d5c51b
handle: 0x0084, char properties: 0x0a, char value handle: 0x0085, uuid: 39e1f90b-84a8-11e2-afba-0002a5d5c51b
handle: 0x0086, char properties: 0x0a, char value handle: 0x0087, uuid: 39e1f90c-84a8-11e2-afba-0002a5d5c51b
handle: 0x0088, char properties: 0x08, char value handle: 0x0089, uuid: 39e1f906-84a8-11e2-afba-0002a5d5c51b
handle: 0x008a, char properties: 0x12, char value handle: 0x008b, uuid: 39e1f907-84a8-11e2-afba-0002a5d5c51b
handle: 0x008d, char properties: 0x0a, char value handle: 0x008e, uuid: 39e1f908-84a8-11e2-afba-0002a5d5c51b
handle: 0x008f, char properties: 0x0a, char value handle: 0x0090, uuid: 39e1f90d-84a8-11e2-afba-0002a5d5c51b
handle: 0x0091, char properties: 0x0a, char value handle: 0x0092, uuid: 39e1f90e-84a8-11e2-afba-0002a5d5c51b
handle: 0x0093, char properties: 0x0a, char value handle: 0x0094, uuid: 39e1f90f-84a8-11e2-afba-0002a5d5c51b
handle: 0x0095, char properties: 0x0a, char value handle: 0x0096, uuid: 39e1f910-84a8-11e2-afba-0002a5d5c51b
handle: 0x0097, char properties: 0x0a, char value handle: 0x0098, uuid: 39e1f911-84a8-11e2-afba-0002a5d5c51b
handle: 0x0099, char properties: 0x0a, char value handle: 0x009a, uuid: 39e1f912-84a8-11e2-afba-0002a5d5c51b
handle: 0x009b, char properties: 0x12, char value handle: 0x009c, uuid: 39e1f913-84a8-11e2-afba-0002a5d5c51b
handle: 0x009f, char properties: 0x0a, char value handle: 0x00a0, uuid: 39e1fd81-84a8-11e2-afba-0002a5d5c51b
handle: 0x00a1, char properties: 0x0a, char value handle: 0x00a2, uuid: 39e1fd85-84a8-11e2-afba-0002a5d5c51b
handle: 0x00a3, char properties: 0x0a, char value handle: 0x00a4, uuid: 39e1fd84-84a8-11e2-afba-0002a5d5c51b
handle: 0x00a5, char properties: 0x0a, char value handle: 0x00a6, uuid: 39e1fd83-84a8-11e2-afba-0002a5d5c51b
handle: 0x00a7, char properties: 0x0a, char value handle: 0x00a8, uuid: 39e1fd82-84a8-11e2-afba-0002a5d5c51b
handle: 0x00a9, char properties: 0x12, char value handle: 0x00aa, uuid: 39e1fd86-84a8-11e2-afba-0002a5d5c51b
handle: 0x00ac, char properties: 0x12, char value handle: 0x00ad, uuid: 39e1fd87-84a8-11e2-afba-0002a5d5c51b
handle: 0x00af, char properties: 0x12, char value handle: 0x00b0, uuid: 39e1fd88-84a8-11e2-afba-0002a5d5c51b
handle: 0x00b2, char properties: 0x12, char value handle: 0x00b3, uuid: 39e1fd89-84a8-11e2-afba-0002a5d5c51b
handle: 0x00b6, char properties: 0x0e, char value handle: 0x00b7, uuid: f000ffc1-0451-4000-b000-000000000000
handle: 0x00b8, char properties: 0x0e, char value handle: 0x00b9, uuid: f000ffc2-0451-4000-b000-000000000000

"""

# Other globals

# Main asyncio event loop. Set by main().
loop = None

KNOWN_POTS = {}

def map_range(x, in_min, in_max, out_min, out_max):
  return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

async def _search_for_pots():
    print("\n\nSearching for Parrot pot...")
    ret = []

    devices = await BleakScanner.discover()
    for device in devices:
        if device.name.startswith("Parrot pot"):
            ret.append(device)
    if ret:
        print(f"    {len(ret)} Parrot pot found!")
    else:
        print(    "No Parrot pot has been found.")
    return ret

# Initialize a pot and put the update function
# in KNOWN_POTS
def init_pot(pot):
    global KNOWN_POTS
    address = pot.address
    # Initialize sensors, buttons, ...

    device_info = DeviceInfo(
        name=pot.name,
        identifiers=pot.address
    )
    soil_moisture = Sensor(
        Settings(
            mqtt=mqtt_settings,
            entity=SensorInfoExtra(
                name="Moisture",
                device_class="moisture",
                unit_of_measurement="%",
                suggested_display_precision=2,
                unique_id="soil_moisture_" + address,
                device=device_info
            )
        )
    )
    water_volume = Sensor(
        Settings(
            mqtt=mqtt_settings,
            entity=SensorInfoExtra(
                name="Water volume",
                device_class="volume_storage",
                unit_of_measurement="L",
                suggested_display_precision=2,
                unique_id="water_volume_" + address,
                device=device_info
            )
        )
    )
    water_volume_perc = Sensor(
        Settings(
            mqtt=mqtt_settings,
            entity=SensorInfoExtra(
                name="Water volume %",
                device_class="volume_storage",
                unit_of_measurement="%",
                suggested_display_precision=2,
                unique_id="water_volume_perc_" + address,
                device=device_info
            )
        )
    )
    soil_conduct = Sensor(
        Settings(
            mqtt=mqtt_settings,
            entity=SensorInfoExtra(
                name="Soil conductivity",
                # device_class="volume_storage",
                unit_of_measurement="uS/cm",
                suggested_display_precision=2,
                unique_id="soil_conduct_" + address,
                device=device_info
            )
        )
    )
    sunlight = Sensor(
        Settings(
            mqtt=mqtt_settings,
            entity=SensorInfoExtra(
                name="Illuminance",
                device_class="illuminance",
                unit_of_measurement="lx",
                suggested_display_precision=2,
                unique_id="illuminance_" + address,
                device=device_info
            )
        )
    )
    battery = Sensor(
        Settings(
            mqtt=mqtt_settings,
            entity=SensorInfo(
                name="battery",
                device_class="battery",
                unit_of_measurement="%",
                unique_id="battery_" + address,
                device=device_info
            )
        )
    )
    air_temp = Sensor(
        Settings(
            mqtt=mqtt_settings,
            entity=SensorInfoExtra(
                name="Air temperature",
                device_class="temperature",
                unit_of_measurement="°C",
                suggested_display_precision=2,
                unique_id="air_temp_" + address,
                device=device_info
            )
        )
    )
    soil_temp = Sensor(
        Settings(
            mqtt=mqtt_settings,
            entity=SensorInfoExtra(
                name="Soil temperature",
                device_class="temperature",
                unit_of_measurement="°C",
                suggested_display_precision=2,
                unique_id="soil_temp_" + address,
                device=device_info
            )
        )
    )
    
    # Instantiate the button
    def my_callback(client: Client, user_data, message: MQTTMessage):
        async def call():
            for i in range(10):
                print(f"    Trying to connect to: {user_data}")
                try:
                    async with BleakClient(user_data, timeout= 30.0) as client:
                        print(f"    Watering...")
                        await client.write_gatt_char(CHAR_WATER_START, bytearray(b'\x08\x00'))
                        print(f"    Watering done")
                        return
                except:
                    traceback.print_exc()
                    print("Waterring failed try again")
                    sleep(15)

        print(f"Water plant: {user_data}")
        try:
            future = asyncio.run_coroutine_threadsafe(call(), loop)
            future.result()
        except:
            traceback.print_exc()

    my_button = Button(
        Settings(
            mqtt=mqtt_settings,
            entity=ButtonInfo(
                name="Water plant",
                unique_id="water_plant_" + address,
                device=device_info
            )
        ),
        my_callback,
        address # user_data
    )
    my_button.write_config()

    # update function for this pot
    pot = None
    async def update():
        print(f"    Connect to: {address}")
        async with BleakClient(address, timeout= 30.0) as client:
            print("        Get bat:", end='')
            bat = await client.read_gatt_char(int(CHAR_BAT_H))
            bat = int.from_bytes(bat, byteorder='little', signed=False)
            print(f" {bat:.2f}%")
            battery.set_state(bat)
            
            print("        Get sunlight:", end='')
            val = await client.read_gatt_char(CHAR_LIGHT_CAL)
            val = struct.unpack('f', val)[0]
            if (val != 0):
                val = round(val) * 11.574 * 53.93 * 10.0
                print(f" {val:.2f} lx")
                sunlight.set_state(val)
            else:
                print(" raw value = 0")

            print("        Get water level:", end='')
            val = await client.read_gatt_char(CHAR_WATER_LEVEL)
            val = int.from_bytes(val, byteorder='little', signed=False)
            if (val!=0):
                print(f" {int(val)}% {((val*2.2) / 100.0):.2f}L / 2.2L")
                water_volume.set_state(((val*2.2) / 100.0))
                water_volume_perc.set_state(val)
            else:
                print(" raw value = 0")
            
            print("        Get soil conduc:", end='')
            val = await client.read_gatt_char(CHAR_SOIL_CONDU)
            val = int.from_bytes(val, byteorder='little', signed=False)
            if (val!=0):
                if (val < 1500):
                    val = 1500;
                if (val > 2036):
                    val = 2036;
                val = map_range(val, 2036, 1500, 0, 1000);
                print(f" {val}uS/cm")
                soil_conduct.set_state(val)
            else:
                print(" raw value = 0")
            
            
            print("        Get soil moisture:", end='')
            val = await client.read_gatt_char(CHAR_SOIL_MOIST)
            val = struct.unpack('f', val)[0]
            if (val!=0):
                print(f" {val:.2f}%")
                soil_moisture.set_state(val)
            else:
                print(" raw value = 0")
            
            
            print("        Get air temp:", end='')
            val = await client.read_gatt_char(CHAR_AIR_TEMP)
            val = int.from_bytes(val, byteorder='little', signed=False)
            if (val!=0):
                val = 0.00000003044 * pow(val, 3.0) - 0.00008038 * pow(val, 2.0) + val * 0.1149 - 30.449999999999999
                print(f" {val:.2f} C")
                air_temp.set_state(val)
            else:
                print(" raw value = 0")
            
            print("        Get soil temp:", end='')
            val = await client.read_gatt_char(CHAR_SOIL_TEMP)
            val = int.from_bytes(val, byteorder='little', signed=False)
            if (val!=0):
                val = 0.00000003044 * pow(val, 3.0) - 0.00008038 * pow(val, 2.0) + val * 0.1149 - 30.449999999999999
                print(f" {val:.2f} C")
                soil_temp.set_state(val)
            else:
                print(" raw value = 0")

    KNOWN_POTS[address] = update

async def check_pot():
    pots = await _search_for_pots()
    for pot in pots:
        print(f"        {pot}:")
        if pot.address not in KNOWN_POTS:
            init_pot(pot)
    for funct in KNOWN_POTS.values():
        sleep(5)
        try:
            await funct()
        except:
            traceback.print_exc()

async def main():
    global loop
    loop = asyncio.get_event_loop()
    while(1):
        try:
            await check_pot()
        except:
            traceback.print_exc()
        print("Wait 15min")
        await asyncio.sleep(15*60)

if __name__ == "__main__":
    asyncio.run(main())
