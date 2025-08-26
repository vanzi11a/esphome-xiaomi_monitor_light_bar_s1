# ESPHome support for Mi Computer Monitor Light Bar 1S (MJGJD02YL)

The Xiaomi Mi Computer Monitor Light Bar 1S is a smart CWWW (Cold+Warm White Light) LED lamp, produced by Yeelight for the Xiaomi Mi brand. It can be controlled via the WiFi network and with a rotating BLE dimmer device. Dimmer supports single and long press action, regular and pressed rotation.

This project provides configuration packages for ESPHome, which make it possible to fully integrate the lamp in your Home Assistant setup.


- [Features](#features)
- [Installation](#installation)
  - [Obtaining the dimmer bindkey](#obtaining-the-dimmer-bindkey)
    - [Method 1 - downloading from Xiaomi Cloud account](#method-1---downloading-from-xiaomi-cloud-account)
    - [Method 2 - using an ESP32 sniffer](#method-2----using-an-esp32-sniffer)
  - [ESPHome configuration](#esphome-configuration)
  - [Hardware preparation](#hardware-preparation)
- [Advanced Configuration](#advanced-configuration)
  - [Presets](#presets)
    - [Option 1: Original Presets](#option-1-original-presets)
    - [Option 2: Generated Custom Presets](#option-2-generated-custom-presets)
  - [Blinking Service](#blinking-service)
    
## Features

### No reliance on Xiaomi Cloud
That's the most obvious one. The lamp is fully controlled by your Home Assistant installation 

### Full support for BLE dimmer, mimicking the stock firmware behaviour
- Single press toggles light
- Rotation changes brightness
- Rotation with pressed button changes white temperature
- Long press cycles between presets

### Full support for light presets
#### Original presets
Following presets from the stock firmware are provided in `original-presets.yaml` package:
- Office - 4500k Temperature, 100% Brightness
- Reading - 5000k Temperature, 100% Brightness
- Leisure - 4000k Temperature, 50% Brightness
- Computer - 2700k Temperature, 50% Brightness
- Warm - 3500k Temperature, 60% Brightness 

Original firmware also included "Blinking" preset, which blinks the lamp 5 times. This is available as an optional service (see [Blinking Service](#blinking-service) section below).

#### Custom presets
Using a provided generator script, custom presets could be defined (see [Advanced Configuration](#advanced-configuration) section below).

## Installation
### Obtaining the dimmer bindkey

Dimmer communication with the lamp is encrypted. To be able to control the lamp, you need to obtain the bindkey from the dimmer. This could be done by one of these methods.

#### Method 1 - downloading from Xiaomi Cloud account
If your lamp is connected to your Xiaomi Cloud account, you can use python-miio to obtain the token for your lamp. You can then use the token to obtain both the dimmer mac and bindkey (note that mac would be reversed):

```
miiocli yeelight --token <token> --ip <ip> dump_ble_debug
```
**NOTE:** currently, due to changes in Xiaomi Cloud API, this method doesn't seem to be working.

#### Method 2 -- using an ESP32 sniffer

You'll need a spare esp32 board to flash with a special firmware (thank you @dentra).
1. Copy `extractor.yaml` and edit wifi network data, flash that firmware. Don't bother putting any meaningful MAC address in dimmer_mac_address if you don't know it yet.
2. Start reading logs from the extractor node, then click the button on the dimmer. You should see a log line that looks like this (`15CE` is a product_id of the dimmer).
```
[22:07:26][D][miot:126]: Got MiBeacon: 48.50.CE.15.4A.D8.03.73.F3.2E.AF.77.00.00.B5.10.41.BD (18)
[22:07:26][D][miot:128]:    [15CE] (encrypted) D4:F0:EA:ED:B9:50 RSSI=-41 (excellent)
[22:07:26][D][miot:135]:   Data: D8.03.73.F3.2E.AF (6)
```
`Data: D8.03.73.F3.2E.AF (6)` -- this is your dimmer's MAC. Put that value into `dimmer_mac_address` replacing `.` with `:`, and flash extractor firmware again.

3. Start reading logs from the extractor node.
4. Remove batteries from the dimmer.
5. Press and hold dimmer key for 2 seconds. Logs would look like this:
```
...
[22:15:39][D][esp32_ble_client:208]: [0] [B8:50:D8:1B:A4:67] ESP_GATTC_REG_FOR_NOTIFY_EVT
[22:15:39][D][esp32_ble_client:423]: Wrote notify descriptor 1, properties=24
[22:15:39][D][miot_legacy_bond_client:059]: Step 2 complete: YES
[22:15:39][D][miot_legacy_bond_client:104]: Step 3 running
[22:15:39][W][miot:111]: B850D81BA467 [15CE] Object is encrypted but bindkey is not configured
[22:15:39][D][miot:126]: Got MiBeacon: 48.50.CE.15.02.05.9A.51.EA.48.B0.38.00.00.AB.47.8B.56 (18)
[22:15:39][D][miot:128]:    [15CE] (encrypted) B8:50:D8:1B:A4:67 RSSI=-44 (excellent)
[22:15:39][D][miot:135]:   Data: 05.9A.51.EA.48.B0 (6)
[22:15:39][D][esp32_ble_client:208]: [0] [B8:50:D8:1B:A4:67] ESP_GATTC_WRITE_DESCR_EVT
[22:15:39][W][miot:111]: B850D81BA467 [15CE] Object is encrypted but bindkey is not configured
[22:15:39][D][miot:126]: Got MiBeacon: 48.50.CE.15.02.05.9A.51.EA.48.B0.38.00.00.AB.47.8B.56 (18)
[22:15:39][D][miot:128]:    [15CE] (encrypted) B8:50:D8:1B:A4:67 RSSI=-48 (excellent)
[22:15:39][D][miot:135]:   Data: 05.9A.51.EA.48.B0 (6)
[22:15:39][D][esp32_ble_client:208]: [0] [B8:50:D8:1B:A4:67] ESP_GATTC_NOTIFY_EVT
[22:15:39][D][miot_legacy_bond_client:116]: Step 3 complete: NO
...
```
First bindkey extraction usually fails, `Step 3 complete: NO` is an indication of that.

6. Remove batteries again and re-try binding by re-inserting batteries and pressing down the dimmer. Successful extraction looks like this:
```
...
[22:19:04][D][esp32_ble_client:208]: [0] [B8:50:D8:1B:A4:67] Found device
[22:19:04][D][esp32_ble_tracker:807]: Found device B8:50:D8:1B:A4:67 RSSI=-39
[22:19:04][D][esp32_ble_tracker:828]:   Address Type: PUBLIC
[22:19:04][D][esp32_ble_tracker:234]: Stopping scan to make connection
[22:19:04][D][esp32_ble_tracker:116]: connecting: 0, discovered: 1, searching: 0, disconnecting: 0
[22:19:04][D][esp32_ble_tracker:343]: End of scan, set scanner state to IDLE.
[22:19:04][D][esp32_ble_tracker:237]: Promoting client to connect
[22:19:04][D][esp32_ble_tracker:241]: Setting coexistence to Bluetooth to make connection.
[22:19:04][I][esp32_ble_client:127]: [0] [B8:50:D8:1B:A4:67] 0x00 Attempting BLE connection
[22:19:04][D][esp32_ble_tracker:116]: connecting: 1, discovered: 0, searching: 0, disconnecting: 0
[22:19:04][D][esp32_ble_client:208]: [0] [B8:50:D8:1B:A4:67] ESP_GATTC_CONNECT_EVT
[22:19:04][D][esp32_ble_client:208]: [0] [B8:50:D8:1B:A4:67] ESP_GATTC_OPEN_EVT
[22:19:04][D][esp32_ble_tracker:116]: connecting: 0, discovered: 0, searching: 0, disconnecting: 0
[22:19:04][D][esp32_ble_tracker:217]: Setting coexistence preference to balanced.
[22:19:04][D][esp32_ble_tracker:307]: Starting scan, set scanner state to STARTING.
[22:19:05][D][esp32_ble_client:433]: [0] [B8:50:D8:1B:A4:67] Event 46
[22:19:05][D][esp32_ble_client:208]: [0] [B8:50:D8:1B:A4:67] ESP_GATTC_SEARCH_CMPL_EVT
[22:19:05][I][esp32_ble_client:354]: [0] [B8:50:D8:1B:A4:67] Connected
[22:19:05][D][miot_legacy_bond_client:086]: Bonding started, token: 4229727e140349d58eec9ea1
[22:19:05][D][miot_legacy_bond_client:092]: Step 1 running
[22:19:05][D][esp32_ble_client:313]: [0] [B8:50:D8:1B:A4:67] cfg_mtu status 0, mtu 247
[22:19:05][D][esp32_ble_client:208]: [0] [B8:50:D8:1B:A4:67] ESP_GATTC_WRITE_CHAR_EVT
[22:19:05][D][miot_legacy_bond_client:045]: Step 1 complete: YES
[22:19:05][D][miot_legacy_bond_client:098]: Step 2 running
[22:19:05][D][esp32_ble_client:208]: [0] [B8:50:D8:1B:A4:67] ESP_GATTC_REG_FOR_NOTIFY_EVT
[22:19:05][D][esp32_ble_client:423]: Wrote notify descriptor 1, properties=24
[22:19:05][D][miot_legacy_bond_client:059]: Step 2 complete: YES
[22:19:05][D][miot_legacy_bond_client:104]: Step 3 running
[22:19:05][D][esp32_ble_client:208]: [0] [B8:50:D8:1B:A4:67] ESP_GATTC_WRITE_DESCR_EVT
[22:19:05][D][esp32_ble_client:208]: [0] [B8:50:D8:1B:A4:67] ESP_GATTC_NOTIFY_EVT
[22:19:05][D][miot_legacy_bond_client:116]: Step 3 complete: YES
[22:19:05][D][miot_legacy_bond_client:128]: Step 5 running
[22:19:05][D][esp32_ble_client:208]: [0] [B8:50:D8:1B:A4:67] ESP_GATTC_WRITE_CHAR_EVT
[22:19:05][D][miot_legacy_bond_client:048]: Step 5 complete: YES
[22:19:05][D][miot_legacy_bond_client:135]: Step 6 running
[22:19:05][D][esp32_ble_client:208]: [0] [B8:50:D8:1B:A4:67] ESP_GATTC_WRITE_CHAR_EVT
[22:19:05][D][esp32_ble_client:208]: [0] [B8:50:D8:1B:A4:67] ESP_GATTC_READ_CHAR_EVT
[22:19:05][D][miot_legacy_bond_client:066]: Step 6 complete: YES
[22:19:05][D][miot_legacy_bond_client:069]: Bonding complete
[22:19:05][D][text_sensor:069]: 'miot_ylxx0xyl_pair Version': Sending state '2.0.0_0001'
[22:19:05][D][esp32_ble_client:208]: [0] [B8:50:D8:1B:A4:67] ESP_GATTC_READ_CHAR_EVT
[22:19:05][D][text_sensor:069]: 'miot_ylxx0xyl_pair Bindkey': Sending state '2C120545B879B64967DA2666'
...
```

This ESPHome sensor has your bindkey. Store the value somewhere safe:

`[22:19:05][D][text_sensor:069]: 'miot_ylxx0xyl_pair Bindkey': Sending state '2C120545B879B64967DA2666'`.


### ESPHome configuration
This one's pretty straightforward. Use `example.yaml`, copy it to your configuration directory and rename it to `<your_desired_node_name>.yaml`.
Edit the configuration adjusting `dimmer_bindkey` and `dimmer_mac_address` variables along with your wifi credentials, 
API and OTA secrets.

### Hardware preparation
There's a very thorough guide (with pictures) available here: [Xiaomi Mi Computer Monitor Light Bar 1S Light (MJGJD02YL) Configuration for Tasmota](https://templates.blakadder.com/xiaomi_MJGJD02YL.html).
Once you have everything wired up, upload your ESPHome firmware.

## Advanced Configuration

### Presets
You have an option to keep presets from the original firmware, or create custom presets with a little extra effort. BLE dimmer long-press cycling works either way.

#### Option 1: Original Presets
If you prefer to keep the 5 original presets (Office/Reading/Leisure/Computer/Warm), use `packages/original-presets.yaml`

```yaml
packages:
  mijamonitorlamp:
    url: https://github.com/vanzi11a/esphome-xiaomi_monitor_light_bar_s1
    ref: main
    files:
      - packages/core.yaml
      - packages/original-presets.yaml

  # Your wifi, api, ota config...
```

#### Option 2: Generated Custom Presets
This allows you to define your own lighting scenes with any number of presets (3, 7, 10, etc.) and customize temperature and brightness values to your liking.

Preset configuration is JSON a file that looks like this:
```json
{
  "presets": [
    {
      "name": "Deep Work",
      "description": "Cool focused lighting",
      "temperature": 6000,
      "brightness": 0.9,
      "icon": "mdi:brain"
    },
    {
      "name": "Gaming",
      "description": "Warm comfortable lighting",
      "temperature": 3200,
      "brightness": 0.7,
      "icon": "mdi:gamepad-variant"
    },
    {
      "name": "Night Mode",
      "temperature": 2200,
      "brightness": 0.1,
      "icon": "mdi:weather-night"
    }
  ]
}
```

1. Generate ESPHome configuration using provided preset generator:
```bash
# Create an example preset file to get started
python scripts/generate_presets.py --create-example

# Generate your custom presets (button style)
python scripts/generate_presets.py my-presets.json --style buttons

# Alternative: generate as select component
python scripts/generate_presets.py my-presets.json --style select
```

2. Update your main configuration to include the generated presets:
```yaml
packages:
  mijamonitorlamp:
    url: https://github.com/vanzi11a/esphome-xiaomi_monitor_light_bar_s1
    ref: main
    files:
      - packages/core.yaml
  local: !include path/to/generated-preset-buttons.yaml  # or generated-preset-select.yaml

# Your wifi, api, ota config...
```

**Note:** The preset generator validates temperature values (2200-6500K) and brightness (0.1-1.0).

### Blinking Service
The original firmware's "Blinking" preset is available as an optional service (one use-case I can think of is notifications).
The service blinks the lamp 5 times over 3 seconds then automatically restores the previous state. That _probably_ matches the original firmware behavior, but I forgot to take original firmware backup so if it's different -- feel free to file an issue, and I'll get it fixed.

#### Features
- **Preserves state**: Automatically returns to previous brightness and temperature after blinking
- **Works when light is off**: Can blink even when the light is initially turned off (and would turn off the light afterward)
- **Configurable**: Brightness and color temperature can be customized per call
- **Button entity**: Includes a "Blink Notification" button for easy testing
- **Home Assistant integration**: Perfect for notifications, alerts, and automations


#### Usage
Include the blinking service package in your configuration:
```yaml
packages:
  mijamonitorlamp:
    url: https://github.com/vanzi11a/esphome-xiaomi_monitor_light_bar_s1
    ref: main
    files:
      - packages/core.yaml
      - packages/blinking-service.yaml
  # Plus your preset package of choice

  # Your wifi, api, ota config...
```

#### Call the Service (from your own ESPHome automation or another ESPHome node)
```yaml
# Basic usage - blinks 5 times with default settings (4000K, 100% brightness)
- service: blink

# Custom brightness and temperature  
- service: blink
  data:
    brightness: 0.8        # 80% brightness
    color_temperature: 6000  # Cool white
```

#### Example Home Assistant Automation
```yaml
automation:
  - alias: "Doorbell Notification"
    trigger:
      platform: state
      entity_id: binary_sensor.doorbell
      to: 'on'
    action:
      service: esphome.your_device_name_blink
      data:
        brightness: 1.0
        color_temperature: 3000
```