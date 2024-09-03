import unittest
from unittest.mock import MagicMock, patch
import logging

# Import the MqttLoggingHandler directly from your my_package
from mqtt_logger import MqttLoggingHandler
from paho.mqtt.enums import MQTTErrorCode

class TestMqttLoggingHandler(unittest.TestCase):
    
    @patch('paho.mqtt.client.Client')
    def setUp(self, MockMQTTClient):
        self.mock_client = MockMQTTClient.return_value
        self.handler = MqttLoggingHandler("localhost", "testprefix")
        self.handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))
        
    def test_initialization(self):
        self.assertEqual(self.handler._mqttserver, "localhost")
        self.assertEqual(self.handler._prefix, "testprefix")
        self.assertEqual(self.handler._mqttport, 1883)
        self.assertEqual(self.handler._mqttuser, "")
        self.assertEqual(self.handler._mqttpasswd, "")

    def test_connect_success(self):
        self.mock_client.connect.return_value = MQTTErrorCode.MQTT_ERR_SUCCESS
        self.assertTrue(self.handler.connect())
        self.mock_client.publish.assert_called_with("testprefix/state", "STARTED")
        
    def test_connect_failure(self):
        self.mock_client.connect.return_value = MQTTErrorCode.MQTT_ERR_AUTH
        with patch('sys.stderr'):
            self.assertFalse(self.handler.connect())
        
    def test_reconnect_existing_client_success(self):
        self.mock_client.is_connected.return_value = False
        self.mock_client.reconnect.return_value = MQTTErrorCode.MQTT_ERR_SUCCESS
        self.assertTrue(self.handler.reconnect())

    def test_reconnect_new_client(self):
        self.handler._mqttClient = None
        with patch.object(self.handler, 'connect', return_value=True) as mock_connect:
            self.assertTrue(self.handler.reconnect())
            mock_connect.assert_called_once()

    def test_publish_success(self):
        mock_pi = MagicMock()
        mock_pi.is_published.return_value = True
        self.mock_client.publish.return_value = mock_pi
        self.assertTrue(self.handler.publish("subtopic", "message"))
          
    def test_disconnect_mqtt(self):
        with patch.object(self.handler, 'publish') as mock_publish:
            self.handler.disconnect_mqtt(True)
            mock_publish.assert_called_with(self.handler.statustopic, "FINISHED", 5)
            self.mock_client.disconnect.assert_called_once()
            
    def test_emit(self):
        record = logging.LogRecord(name="test", level=logging.INFO, pathname="", lineno=42, msg="Test message", args=None, exc_info=None)
        
        # Mocking methods within the class
        with patch.object(self.handler, 'reconnect', return_value=True), \
             patch.object(self.handler, 'publish', return_value=True):

           self.handler.emit(record)
           

if __name__ == '__main__':
    unittest.main()
