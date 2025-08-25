# ESPHome support for Mi Computer Monitor Light Bar 1S (MJGJD02YL)

The Xiaomi Mi Computer Monitor Light Bar 1S is a smart CWWW (Cold+Warm White Light) LED lamp, produced by Yeelight for the Xiaomi Mijia brand. It can be controlled via the WiFi network and with a rotating BLE dimmer device. Dimmer supports single and long press action, regular and pressed rotation.

This project provides configuration packages for ESPHome, which make it possible to fully integrate the lamp in your Home Assistant setup.

## Features

### No reliance on Xiaomi Cloud
That's the most obvious one. The lamp is fully controlled by your Home Assistant installation 

### Full support for BLE dimmer, mimicking the stock firmware behaviour
- Single press toggles light
- Rotation changes brightness
- Rotation with pressed button changes white temperature
- Long press cycles between presets

Following presets from the stock firmware are pre-configured:
- Office - 4500k Temperature, 100% Brightness
- Reading - 5000k Temperature, 100% Brightness
- Lesiure - 4000k Temperature, 50% Brightness
- Computer - 2700k Temperature, 50% Brightness
- Warm - 3500k Temperature, 60% Brightness 

Original firmware also included "Blinking" preset, which blinks the lamp 5 times. 
It is not implemented yet.
TODO: add, but should not be cycled through. It should be possible to call it as a service.

## Quick start

### Obtaining the Dimmer bindkey

Dimmer communication with the lamp is encrypted. To be able to control the lamp, you need to obtain the bindkey from the dimmer. This could be done by one of these methods.

#### Method 1 - downloading from Xiaomi Cloud account
If your lamp is connected to your Xiaomi Cloud account, you can use python-miio to obtain the token for your lamp. You can then use the token to obtain the bindkey:

```
miiocli yeelight --token <token> --ip <ip> dump_ble_debug
```
**NOTE:** currently, due to changes in Xiaomi Cloud API, this method doesn't seem to be working.

#### Method 2 -- using an ESP32 sniffer

You'll need a spare esp32 board to flash with a special firmware (thank you @dentra).
1. Copy `extractor.yaml` and edit wifi network data, flash that firmware. Don't bother putting any meaningful MAC address in dimmer_mac_address for now.
2. Start reading logs the extractor node, click the button on the dimmer. You should see a log line that looks like this:
```
[22:07:26][D][miot:126]: Got MiBeacon: 48.50.CE.15.4A.D8.03.73.F3.2E.AF.77.00.00.B5.10.41.BD (18)
[22:07:26][D][miot:128]:    [15CE] (encrypted) D4:F0:EA:ED:B9:50 RSSI=-41 (excellent)
[22:07:26][D][miot:135]:   Data: D8.03.73.F3.2E.AF (6)
```
`Data: D8.03.73.F3.2E.AF (6)` -- this is your dimmer's MAC. Put that value into `dimmer_mac_address` replacing `.` with `:`, and flash extractor firmware again. Now you can extract the bindkey.

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

6. Remove batteries again and re-try binding by re-inserting batteries and holding the key. Successful extraction looks like this:
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
`[22:19:05][D][text_sensor:069]: 'miot_ylxx0xyl_pair Bindkey': Sending state '2C120545B879B64967DA2666'` -- this ESPHome sensor has your bindkey. Store the value somewhere safe.


- Use `example.yaml`. Copy it to your configuration directory and rename it to <your_desired_node_name>.yaml
- Edit the configuration