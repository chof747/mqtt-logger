import sys
import logging
import json
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion, MQTTErrorCode

class MqttLoggingHandler(logging.Handler):

    statustopic = "state"

    def __init__(self, host : str, logtopicprefix : str, port : int = 1883, user : str = "", passwd : str = ""):
        logging.Handler.__init__(self)
        
        self._mqttClient = mqtt.Client(CallbackAPIVersion.VERSION2)
        self._mqttserver = host
        self._mqttport = port if (port>0) else 1883
        self._mqttuser = user
        self._mqttpasswd = passwd
        self._prefix = logtopicprefix

    def reconnect(self) -> bool:
        if self._mqttserver:
            if (not self._mqttClient.host):
                return self.connect()
            else: 
                if (self._mqttClient.is_connected()):
                    return True
                else:
                    return (MQTTErrorCode.MQTT_ERR_SUCCESS == self._mqttClient.reconnect())
            

    def connect(self) -> bool:        
        if self._mqttuser:
            self._mqttClient.username_pw_set(self._mqttuser, self._mqttpasswd)
            
        ret = self._mqttClient.connect(self._mqttserver, self._mqttport, 5)

        if MQTTErrorCode.MQTT_ERR_SUCCESS != ret:
            print(f"Cannot connect to mqttserver {self._mqttserver} error is {ret}", file=sys.stderr)
            return False
        else:
            self._mqttClient.publish(f"{self._prefix}/{self.statustopic}", "STARTED")
            return True
        
    def publish(self, subtopic :str, msg : str, timeout : int = 0.5) -> bool:
        if (self.reconnect()):
            pi = self._mqttClient.publish(f"{self._prefix}/{subtopic}", msg)
            pi.wait_for_publish(timeout)
            return pi.is_published()
        else:
            return False

        

    def disconnect_mqtt(self, ok: bool) -> None:
        self.publish(self.statustopic, "FINISHED" if (ok) else "ABORTED", 5)
        self._mqttClient.disconnect()
    
    def emit(self, record: logging.LogRecord):
        logmsg = self.format(record)
        data = record.args

        msg = json.dumps({
            'message' : logmsg,
            'additional_data' : data
        }, indent = 2)

        if ((self._mqttClient.is_connected()) or (self.reconnect())):
            result = False
            for to in [0.5, 1, 2, 5]:
                result = self.publish(record.levelname, msg, to)
                if result: return
            
        print(f"Could not log message {msg} to mqtt!", file=sys.stderr)