import asyncio
import struct
from bleak import BleakClient, BleakScanner

from ha_mqtt_discoverable import Settings, DeviceInfo
from ha_mqtt_discoverable.sensors import Sensor, SensorInfo, Button, ButtonInfo
from paho.mqtt.client import Client, MQTTMessage
from time import sleep
import traceback 

mqtt_settings = Settings.MQTT(
    host     = "",
    port     = 1883,
    username = "",
    password = ""
)

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

KNOWN_POTS = {}

async def check_pot():
    pots = await _search_for_pots()
    for pot in pots:
        print(f"    {pot}:")

        if pot.address in KNOWN_POTS:
            update = KNOWN_POTS[pot.address]
            await update()
            continue
        
        # Initialize sensors, buttons, ...

        device_info = DeviceInfo(
            name=pot.name,
            identifiers=pot.address
        )

        soil_moisture = Sensor(
            Settings(
                mqtt=mqtt_settings,
                entity=SensorInfo(
                    name="Moisture",
                    device_class="moisture",
                    unit_of_measurement="%",
                    unique_id="soil_moisture",
                    device=device_info
                )
            )
        )

        water_volume = Sensor(
            Settings(
                mqtt=mqtt_settings,
                entity=SensorInfo(
                    name="Water volume",
                    device_class="volume_storage",
                    unit_of_measurement="L",
                    unique_id="water_volume",
                    device=device_info
                )
            )
        )

        water_volume_perc = Sensor(
            Settings(
                mqtt=mqtt_settings,
                entity=SensorInfo(
                    name="Water volume %",
                    device_class="volume_storage",
                    unit_of_measurement="%",
                    unique_id="water_volume_perc",
                    device=device_info
                )
            )
        )

        soil_conduct = Sensor(
            Settings(
                mqtt=mqtt_settings,
                entity=SensorInfo(
                    name="Soil conductivity",
                    # device_class="volume_storage",
                    unit_of_measurement="uS/cm",
                    unique_id="soil_conduct",
                    device=device_info
                )
            )
        )

        sunlight = Sensor(
            Settings(
                mqtt=mqtt_settings,
                entity=SensorInfo(
                    name="Illuminance",
                    device_class="illuminance",
                    unit_of_measurement="lx",
                    unique_id="illuminance",
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
                    unique_id="battery",
                    device=device_info
                )
            )
        )
        
        air_temp = Sensor(
            Settings(
                mqtt=mqtt_settings,
                entity=SensorInfo(
                    name="Air temperature",
                    device_class="temperature",
                    unit_of_measurement="°C",
                    unique_id="air_temp",
                    device=device_info
                )
            )
        )
        
        soil_temp = Sensor(
            Settings(
                mqtt=mqtt_settings,
                entity=SensorInfo(
                    name="Soil temperature",
                    device_class="temperature",
                    unit_of_measurement="°C",
                    unique_id="soil_temp",
                    device=device_info
                )
            )
        )
        
        def my_callback(client: Client, user_data, message: MQTTMessage):
            async def call():
                print(f"    Trying to connect to: {user_data}")
                async with BleakClient(user_data, timeout= 120.0) as client:
                    print(f"    Watering...")
                    await client.write_gatt_char(CHAR_WATER_START, bytearray(b'\x08\x00'))
                    print(f"    Watering done")
                
            print(f"Water plant: {user_data}")
            try:
                asyncio.run(call())
            except:
                traceback.print_exc()

        user_data = pot.address

        # Instantiate the button
        my_button = Button(
            Settings(
                mqtt=mqtt_settings,
                entity=ButtonInfo(
                    name="water plants",
                    unique_id="water_plants",
                    device=device_info
                )
            ),
            my_callback,
            user_data
        )

        my_button.write_config()

        # update function for this pot
        async def update():
            async with BleakClient(pot, timeout= 120.0) as client:
                print("        Get bat:")
                bat = await client.read_gatt_char(CHAR_BAT)
                bat = int.from_bytes(bat, byteorder='little', signed=False)
                print(f"            bat: {bat:.2f}%")
                battery.set_state(bat)
                
                print("        Get sunlight:")
                val = await client.read_gatt_char(CHAR_LIGHT_CAL)
                val = struct.unpack('f', val)[0]
                if (val != 0):
                    val = round(val) * 11.574 * 53.93 * 10.0
                    print(f"            Sun: {val:.2f} lx")
                    sunlight.set_state(val)
                else:
                    print("            raw value = 0")

                print("        Get water level:")
                val = await client.read_gatt_char(CHAR_WATER_LEVEL)
                val = int.from_bytes(val, byteorder='little', signed=False)
                if (val!=0):
                    print(f"            Water: {int(val)}% {((val*2.2) / 100.0):.2f}L / 2.2L")
                    water_volume.set_state(((val*2.2) / 100.0))
                    water_volume_perc.set_state(val)
                else:
                    print("            raw value = 0")
                
                print("        Get soil conduc:")
                val = await client.read_gatt_char(CHAR_SOIL_CONDU)
                val = int.from_bytes(val, byteorder='little', signed=False)
                if (val!=0):
                    if (val < 1500):
                        val = 1500;
                    if (val > 2036):
                        val = 2036;
                    val = map_range(val, 2036, 1500, 0, 1000);
                    print(f"            Soil conduc: {val}uS/cm")
                    soil_conduct.set_state(val)
                else:
                    print("            raw value = 0")
                
                
                print("        Get soil moisture:")
                val = await client.read_gatt_char(CHAR_SOIL_MOIST)
                val = struct.unpack('f', val)[0]
                if (val!=0):
                    print(f"            Soil moisture: {val:.2f}%")
                    soil_moisture.set_state(val)
                else:
                    print("            raw value = 0")
                
                
                print("        Get air temp:")
                val = await client.read_gatt_char(CHAR_AIR_TEMP)
                val = int.from_bytes(val, byteorder='little', signed=False)
                if (val!=0):
                    val = 0.00000003044 * pow(val, 3.0) - 0.00008038 * pow(val, 2.0) + val * 0.1149 - 30.449999999999999
                    print(f"            temp: {val:.2f} C")
                    air_temp.set_state(val)
                else:
                    print("            raw value = 0")
                
                print("        Get soil temp:")
                val = await client.read_gatt_char(CHAR_SOIL_TEMP)
                val = int.from_bytes(val, byteorder='little', signed=False)
                if (val!=0):
                    val = 0.00000003044 * pow(val, 3.0) - 0.00008038 * pow(val, 2.0) + val * 0.1149 - 30.449999999999999
                    print(f"            temp: {val:.2f} C")
                    soil_temp.set_state(val)
                else:
                    print("            raw value = 0")

    KNOWN_POTS[pot.address] = update
    await update()

while(1):
    try:
        asyncio.run(check_pot())
    except:
        traceback.print_exc()
    print("Wait 15min")
    sleep(15*60)

