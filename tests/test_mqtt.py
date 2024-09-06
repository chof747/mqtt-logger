import logging
import unittest
import json
import time
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion, MQTTErrorCode
from mqtt_logger.handler import MqttLoggingHandler

class TestMQTTLogger(unittest.TestCase):

    def setUp(self):
        self.broker = "localhost"
        self.port = 1883
        self.topicprefix = "test/mqttlogger"
        self.test_message = "Hello, MQTT!"
        self.received_message = None
        self.connected = False
        self.subscribed = False
        
        self.client = mqtt.Client(CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_subscribe = self.on_subscribe
        self.client.on_message = self.on_message

        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger()
        self.handler = MqttLoggingHandler("localhost", self.topicprefix, node = "tester")
        self.handler.setLevel(logging.INFO)
        self.handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        self.logger.addHandler(self.handler)

        print("Connecting to broker...")
        self.client.connect(self.broker, self.port, 60)
        
        # Start the network loop in a separate thread.
        self.client.loop_start()
        
        # Wait until connected and subscribed
        self.wait_until(lambda: self.connected, timeout=5, msg="Timeout waiting for connection ")

    def tearDown(self):
        print("Tearing down...")
        self.client.loop_stop()
        self.client.disconnect()

    def on_connect(self, client, userdata, flags, rc, properties):
        print(f"Connected with result code {rc}")
        if rc == 0:
            self.connected = True
        else:
            raise ConnectionError(f"Failed to connect with result code {rc}")

    def on_subscribe(self, client, userdata, mid, reason_code_list, properties):
        print(f"Subscribed to topic: {self.topicprefix}/state")
        self.subscribed = True

    def on_message(self, client, userdata, msg):
        print(f"Message received: {msg.payload.decode()}")
        self.received_message = msg.payload.decode()

    def wait_until(self, condition, timeout, msg):
        timeout_time = time.time() + timeout
        while not condition() and time.time() < timeout_time:
            time.sleep(0.1)
        if not condition():
            self.fail(msg)

    def subscribe(self, topic : str):
        self.subscribed = False
        self.client.subscribe(topic)
        self.wait_until(lambda: self.subscribed, timeout=5, msg=f"Timeout waiting for subscription of {topic}")

    def test_connect_disconnect_and_receive_status_message(self):
        self.subscribe(f"{self.topicprefix}/state")
      
        self.received_message = None
        self.handler.connect()
        # Wait for the message to be received
        self.wait_until(lambda: self.received_message is not None, timeout=5, msg="Timeout waiting for message")
        
        print(f"Assert received message: {self.received_message}")
        self.assertEqual(self.received_message, "STARTED")

        self.received_message = None
        self.handler.disconnect_mqtt(True)
        self.wait_until(lambda: self.received_message is not None, timeout=5, msg="Timeout waiting for message")
        self.assertEqual(self.received_message, "FINISHED")

        self.client.unsubscribe(f"{self.topicprefix}/state")

    def test_log_error(self):
        self.subscribe(f"{self.topicprefix}/ERROR")

        self.handler.connect()
        self.received_message = None
        self.logger.error("This is an error")

        self.wait_until(lambda: self.received_message is not None, timeout=5, msg="Timeout waiting for message")
        self.assertEqual(self.received_message, json.dumps({
            'message' : "ERROR: This is an error",
            'additional_data' : [],
            'node' : 'tester'
        }, indent=2))
        self.client.unsubscribe(f"{self.topicprefix}/ERROR")


    def test_log_with_arguments(self):
        self.subscribe(f"{self.topicprefix}/WARNING")

        self.handler.connect()
        self.received_message = None
        self.logger.warning("This is a warning", {
            'x':1, 'y':'test'})

        self.wait_until(lambda: self.received_message is not None, timeout=5, msg="Timeout waiting for message")
        self.assertEqual(self.received_message, json.dumps({
            'message' : "WARNING: This is a warning",
            'additional_data' : {
                'x' : 1,
                'y' : 'test'
            },
            'node' : 'tester'
        }, indent=2))




if __name__ == "__main__":
    unittest.main()
