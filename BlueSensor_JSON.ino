 /* Arduino firmware for BlueSensor 1.0
  Sensors:
  - 2x MQ-x gas sensor,
  - DHT-22 (humidity and temperature) sensor,
  - 2x DS18B20 temperature sensor).

  Required libraries for DHT-22 humidity and temperature sensor:
  - "Adafruit Unified Sensor" and "DHT Sensor Library";
  Required libraries for DS18B20 temperature sensor:
  - "OneWire" and "DallasTemperature"
  
 Installation via IDE: Sketch, Include Library, Manage Library */

#include <SoftwareSerial.h>     // import the serial library
#include <DHT.h>                // import the DHT library
#include <OneWire.h>            // import the OneWire protocol library
#include <DallasTemperature.h>  // import DS18B20 library
#include <ArduinoJson.h>        // import JSON library

#define DHTPIN 2           // DHT sensor is connected to pin D2
#define DHTTYPE DHT22      // we are using DHT-22 (AM2302) sensor

#define ONE_WIRE_BUS 9     // DS18B20 sensor is connected to pin D9

const int MQxPin1 = A0;    // GAS sensor 1 is connected to pin A0
const int MQxPin2 = A1;    // GAS sensor 2 is connected to  pinA1

const int led = 7;         // LED diode is connected to pin D7
const int buzzer = 6;      // buzzer is connected to pin D6

int gasvalue1;             // variable to store raw reading from gas sensor 1
int gasvalue2;             // variable to store raw reading from gas sensor 2

boolean dht_present;      // is DHT-22 sensor present and ready?
boolean onewire1_present; // is first DS18B20 sensor present and connected properly?
boolean onewire2_present; // is second DS18B20 sensor present and connected properly?

DHT dht(DHTPIN, DHTTYPE);             // initialize DHT sensor
OneWire oneWire(ONE_WIRE_BUS);        // establish OneWire instance to communicate with any OneWire deviceD
DallasTemperature sensors(&oneWire);   // pass our oneWire reference to Dallas Temperature library

void setup()
{
  Serial.begin(9600);    // initialize serial port (9600 bps)
  sensors.begin();       // start up the Dallas Temperature library 
  pinMode(led, OUTPUT);  // initialize LED output
  tone(buzzer, 1000);    // beep 1KHz sound signal to indicate system is ready...
  delay(100);            // ...for 0.1 sec
  noTone(buzzer);        // stop sound.
}

void loop()
{
  digitalWrite(led, HIGH);  // Start reading sensors, diode is ON...
  
  // Read the gas value:
  gasvalue1 = analogRead(MQxPin1);
  gasvalue2 = analogRead(MQxPin2);
  
  // Read humidity (it takes about 250 milliseconds, sensor readings may also be
  // up to 2 seconds 'old', because sensor is slow):
  float humidity = dht.readHumidity();
  // read temperature as Celsius:
  float temperature1 = dht.readTemperature();

  // Check if any reads failed:
  if (isnan(humidity) || isnan(temperature1)) {
    dht_present = false;  // failed to read from DHT sensor!
  }
  else {
    dht_present = true;
  }

  // Get temperature readings from two devices on the OneWire bus 
  sensors.requestTemperatures();
  float temperature2 = sensors.getTempCByIndex(0);

  // Check if reading failed:
  if (temperature2 == -127) {
    onewire1_present = false;  // failed to read from DS18B20 sensor!
  }
  else {
    onewire1_present = true;
  }
    
  float temperature3 = sensors.getTempCByIndex(1);
  // Check if reading failed:
  if (temperature3 == -127) {
    onewire2_present = false;  // failed to read from DS18B20 sensor!
  }
  else {
    onewire2_present = true;
  }
 
  // Prepare JSON output...
  const size_t bufferSize = 6*JSON_ARRAY_SIZE(5) + JSON_OBJECT_SIZE(3) + JSON_OBJECT_SIZE(4) + 2*JSON_OBJECT_SIZE(6);
  DynamicJsonBuffer jsonBuffer(bufferSize);

  JsonObject& root = jsonBuffer.createObject();

  JsonObject& metadata = root.createNestedObject("metadata");
  metadata["device_name"] = "BlueSensor";
  metadata["device_id"] = "BlueSensor";
  metadata["device_location"] = "CodeWeek";

  JsonObject& metadata_sensors = metadata.createNestedObject("sensors");

  JsonArray& metadata_sensors_temperature1 = metadata_sensors.createNestedArray("temperature1");
  metadata_sensors_temperature1.add("Temperatura v prostoru");
  metadata_sensors_temperature1.add("DHT-22");
  metadata_sensors_temperature1.add("°C");
  metadata_sensors_temperature1.add("salmon");
  if (dht_present == true) {
    metadata_sensors_temperature1.add("ready");
  }
  else {
    metadata_sensors_temperature1.add("not ready");
  }

  JsonArray& metadata_sensors_humidity = metadata_sensors.createNestedArray("humidity");
  metadata_sensors_humidity.add("Vlaga");
  metadata_sensors_humidity.add("DHT-22");
  metadata_sensors_humidity.add("%");
  metadata_sensors_humidity.add("cornflowerblue");
  if (dht_present == true) {
    metadata_sensors_humidity.add("ready");
  }
  else {
    metadata_sensors_humidity.add("not ready");
  }

  JsonArray& metadata_sensors_temperature2 = metadata_sensors.createNestedArray("temperature2");
  metadata_sensors_temperature2.add("Temperatura tekočine 1");
  metadata_sensors_temperature2.add("DS18B20");
  metadata_sensors_temperature2.add("°C");
  metadata_sensors_temperature2.add("red");
  if (onewire1_present == true) {
    metadata_sensors_temperature2.add("ready");
  }
  else {
    metadata_sensors_temperature2.add("not ready");
  }

  JsonArray& metadata_sensors_temperature3 = metadata_sensors.createNestedArray("temperature3");
  metadata_sensors_temperature3.add("Temperatura tekočine 2");
  metadata_sensors_temperature3.add("DS18B20");
  metadata_sensors_temperature3.add("°C");
  metadata_sensors_temperature3.add("yellow");
  if (onewire2_present == true) {
    metadata_sensors_temperature3.add("ready");
  }
  else {
    metadata_sensors_temperature3.add("not ready");
  }

  JsonArray& metadata_sensors_gas1 = metadata_sensors.createNestedArray("gas1");
  metadata_sensors_gas1.add("Alkohol");
  metadata_sensors_gas1.add("DHT-22");
  metadata_sensors_gas1.add("%");
  metadata_sensors_gas1.add("green");
  metadata_sensors_gas1.add("ready");

  JsonArray& metadata_sensors_gas2 = metadata_sensors.createNestedArray("gas2");
  metadata_sensors_gas2.add("Vnetljivi plini");
  metadata_sensors_gas2.add("MQ-x");
  metadata_sensors_gas2.add("raw value");
  metadata_sensors_gas2.add("tomato");
  metadata_sensors_gas2.add("ready");

  root["time"] = 0;

  JsonObject& data = root.createNestedObject("data");

  if (dht_present == true) {
    data["temperature1"] = temperature1;
  }
  else {
    data["temperature1"] = "none";
  }  
  if (dht_present == true) {
    data["humidity"] = humidity;
  }
  else {
    data["humidity"] = "none";
  }    

  if (onewire1_present == true) {
    data["temperature2"] = temperature2;
  }
  else {
    data["temperature2"] = "none";
  }  
  
  if (onewire1_present == true) {
    data["temperature3"] = temperature3;
  }
  else {
    data["temperature3"] = "none";
  }  

  data["gas1"] = gasvalue1;
  data["gas2"] = gasvalue2;

  root.printTo(Serial);
  Serial.println();

  digitalWrite(led, LOW);  // Stop reading sensors, diode is OFF...
  delay(1000);   // wait 1 sec...
}

