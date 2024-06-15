import asyncio
import struct
from bleak import BleakClient, BleakScanner
from bleak.exc import BleakError


from ha_mqtt_discoverable import Settings, DeviceInfo
from ha_mqtt_discoverable.sensors import Sensor, SensorInfo, Button, ButtonInfo
from paho.mqtt.client import Client, MQTTMessage
from time import sleep
import traceback
from time import perf_counter


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

# Other globals

# Main asyncio event loop. Set by main().
loop = None

KNOWN_POTS = {}
to_water = {}

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
        print(f"\n    {len(ret)} Parrot pot found!")
    else:
        print("\n    No Parrot pot has been found.")
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
            print(f"Water plant: {user_data}")
            for i in range(10):
                print(f"    Trying to connect to: {user_data}")
                try:
                    async with BleakClient(user_data, timeout= 60.0) as client:
                        print(f"    Watering...")
                        await client.write_gatt_char(CHAR_WATER_START, bytearray(b'\x08\x00'))
                        print(f"    Watering done")
                        return
                except BleakError as e:
                    print(f"    {e}")
                    print("Waterring failed try again")
                    sleep(15)
        # try:
        to_water[address] = call
            # future = asyncio.run_coroutine_threadsafe(call(), loop)
            # future.result()

        # except:
        #     traceback.print_exc()

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
        print(f"\n    Connect to: {address}")
        for i in range(10):
            try:
                async with BleakClient(address, timeout= 60.0) as client:
                    print("        Battery:", end='')
                    bat = await client.read_gatt_char(int(CHAR_BAT_H))
                    bat = int.from_bytes(bat, byteorder='little', signed=False)
                    print(f" {bat:.0f}%")
                    battery.set_state(bat)
                    
                    print("        Sunlight:", end='')
                    val = await client.read_gatt_char(CHAR_LIGHT_CAL)
                    val = struct.unpack('f', val)[0]
                    if (val != 0):
                        val = round(val) * 11.574 * 53.93 * 10.0
                        print(f" {val:.0f}lx")
                        sunlight.set_state(val)
                    else:
                        print(" raw value = 0")

                    print("        Water tank:", end='')
                    val = await client.read_gatt_char(CHAR_WATER_LEVEL)
                    val = int.from_bytes(val, byteorder='little', signed=False)
                    if (val!=0):
                        print(f" {int(val)}%", end='');
                        print(f" ({((val*2.2) / 100.0):.1f}L / 2.2L)")
                        water_volume.set_state(((val*2.2) / 100.0))
                        water_volume_perc.set_state(val)
                    else:
                        print("            raw value = 0")
                    
                    print("        Soil:")

                    print("           conduc:", end='')
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
                    
                    
                    print("           moist:", end='')
                    val = await client.read_gatt_char(CHAR_SOIL_MOIST)
                    val = struct.unpack('f', val)[0]
                    if (val!=0):
                        print(f"  {val:.2f}%")
                        soil_moisture.set_state(val)
                    else:
                        print("  raw value = 0")
                    
                    print("           temp:", end='')
                    val = await client.read_gatt_char(CHAR_SOIL_TEMP)
                    val = int.from_bytes(val, byteorder='little', signed=False)
                    if (val!=0):
                        val = 0.00000003044 * pow(val, 3.0) - 0.00008038 * pow(val, 2.0) + val * 0.1149 - 30.449999999999999
                        print(f"   {val:.2f}°C")
                        soil_temp.set_state(val)
                    else:
                        print("   raw value = 0")
                    
                    print("        Air temp:", end='')
                    val = await client.read_gatt_char(CHAR_AIR_TEMP)
                    val = int.from_bytes(val, byteorder='little', signed=False)
                    if (val!=0):
                        val = 0.00000003044 * pow(val, 3.0) - 0.00008038 * pow(val, 2.0) + val * 0.1149 - 30.449999999999999
                        print(f"  {val:.2f}°C")
                        air_temp.set_state(val)
                    else:
                        print("  raw value = 0")
                    break
                    
            except BleakError as e:
                print(f"        {e}")
            # sleep(10)
            

    KNOWN_POTS[address] = update

async def check_pot():
    pots = await _search_for_pots()
    for pot in pots:
        print(f"        {pot}:")
        if pot.address not in KNOWN_POTS:
            init_pot(pot)
    for funct in KNOWN_POTS.values():
        # sleep(20)
        try:
            await funct()
        except:
            traceback.print_exc()

next_read = 0
next_water = 0

async def main():
    global loop
    global to_water
    global next_water
    global next_read
    loop = asyncio.get_event_loop()
    while(1):
        if (next_water < perf_counter()):
            for key, value in list(to_water.items()):
                await value()
            to_water = {}
            next_water = perf_counter() + 30
        if (next_read < perf_counter()):
            try:
                await check_pot()
            except:
                traceback.print_exc()
            next_read = perf_counter() + 60 * 20
        await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(main())
