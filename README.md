# HassMonitorMqtt
HassMonitorMQTT is an integration for [HomeAssistant](https://github.com/home-assistant/home-assistant) that receives system data from different computers (that work together as MQTT clients) and provides commands and sensors.
Client-side script for this integrations can be found [here](https://github.com/richibrics/PyMonitorMQTT)

Available information:
* RAM in use (%)
* CPU in use (%)
* Hard Disk used space (%)
* CPU Temperature (°C)
* Battery Level (%)
* Charging status 
* Timestamp of the data
* Running Operating System

Actions:
* Shutdown
* Reboot
* Lock

## HomeAssistant with PyMonitorMQTT preview

![HomeAssistant Example](Home%20Assistant%20Monitors.png?raw=true "HomeAssistant Example")

## Getting Started
### Install the component
To install the component, copy the entire repo in your custom-component folder:

```
$CONFIG_FOLDER$/custom-component/monitor-mqtt
```

Now your configuration folder should look like this:
```
CONFIG_FOLDER/custom_components/monitor_mqtt/
├── binary_sensor.py
├── funcs.py
├── __init__.py
├── Home Assistant Monitors.png (YOU CAN DELETE THIS)
├── README.md
├── sensor.py
└── switch.py

```

### Configure
In your configuration.yaml add the 'monitor-mqtt' component with all your clients:

```
monitor_mqtt:
  - client_name: PcName1
  - client_name: PcName1
```
where PcName1 and PcName2 are the client names that are chosen by the client (passed to the client script with -n argument)


### Lovelace layout

[Here](lovelace_card.yaml) you can find my Lovelace preset for monitor-mqtt 

## Authors

**Riccardo Briccola** - Project development - [Github Account](https://github.com/richibrics)

