 /*  BlueSensor v1.0
  *  Arduino firmware for using various sensors (MQ-x GAS sensors, DHT-22 (humidity and temperature) sensor, DS18B20 temperature sensor, etc.).
  *  DS18B20 temperature sensor uses OneWire protocol and you can connect multiple sensors on the same cable.
  *  DS18B20 sensors are distinguised by index (0 is first device, 1 is second device, etc.)-
  *  
  *  Output data are printed to serial console (ttyUSB0). 
  *  Code runs on Arduino Nano (ATMega328).

  *  MQ1-x sensor connection
  *  ======================
  *  [MQ-x sensor - Arduino Nano]
  *  A0 - A0
  *  D0 - not connected
  *  GND - GND
  *  VCC - 5V


  *  MQ2-x sensor connection
  *  ======================
  *  [MQ-x sensor - Arduino Nano]
  *  A0 - A1
  *  D0 - not connected
  *  GND - GND
  *  VCC - 5V

  *  DHT-22 (AM2302) sensor connection
  *  =================================
  *  [DHT-22 sensor - Arduino Nano]
  *  "-" - GND 
  *  out - D2
  *  "+" - 5v

  *  DS12B20 sensor connection
  *  =========================
  *  (you can  use multiple sensors on the same cable)
  *  Very important: between red and yellow cable you must connect 4.7 kOhm resistor!
  *  
  *  [DS12B20 sensor - Arduino Nano]
  *  "red cable" - 5v
  *  "yellow cable" - D4
  *  "black cable" - GND
  *  between "red cable" and "yellow cable" is 4.7k Ohm resistor

  *  Buzzer
  *  ======
  *  [buzzer (12 mm) - Arduino Nano]
  *  "-" - GND 
  *  "+" - 100 Ohm resistor - D6

  *  LED diode
  *  =========
  *  [LED diode - Arduino Nano]
  *  "-" - GND 
  *  "+" - 270 Ohm resistor - D7

  *  Battery connection
  *  ==================
  *  [battery pack - Arduino Nano]
  *  "+" - VIN
  *  "-" - GND
  *  
  *  IMPORTANT INFORMATION:
  *  Gas sensor becomes hot after some time (avoid touching it!). So if you place DHT-22 sensor near gas sensor,
  *  temperature reading will not be correct!
*/

// Required libraries for DHT-22 humidity and temperature sensor: "Adafruit Unified Sensor" and "DHT Sensor Library".
// Required libraries for DS18B20 temperature sensor: "OneWire" and "DallasTemperature"
// Installation via IDE: Sketch, Include Library, Manage Library

#include <DHT.h>                // import the DHT library
#include <OneWire.h>            // import the OneWire protocol library
#include <DallasTemperature.h>  // import DS18B20 library

// Set if sensor is connected!

const char DEVICE_BTNAME[] = "SENSOR1";
const char DEVICE_NAME[] = "BlueSensor";
const char DEVICE_LOCATION[] = "CodeWeek";

const char GAS1_NAME[] = "Alkohol";
const char GAS1_TYPE[] = "MQ-3";
const char GAS1_UNIT[] = "raw value";
const char GAS1_COLOR[] = "blue";
const boolean GAS1_CONNECTED = true;

const char GAS2_NAME[] = "Vodik";
const char GAS2_TYPE[] = "MQ-8";
const char GAS2_UNIT[] = "raw value";
const char GAS2_COLOR[] = "black";
const boolean GAS2_CONNECTED = true;

const char HUMIDITY_NAME[] = "Vlaga";
const char HUMIDITY_TYPE[] = "DHT-22";
const char HUMIDITY_UNIT[] = "%";
const char HUMIDITY_COLOR[] = "cornflowerblue";
const boolean HUMIDITY_CONNECTED = false;

const char TEMPERATURE1_NAME[] = "Temperatura v prostoru";
const char TEMPERATURE1_TYPE[] = "DHT-22";
const char TEMPERATURE1_UNIT[] = "°C";
const char TEMPERATURE1_COLOR[] = "tomato";
const boolean TEMPERATURE1_CONNECTED = false;

const char TEMPERATURE2_NAME[] = "Temperatura - tekočina 1";
const char TEMPERATURE2_TYPE[] = "DS18B20";
const char TEMPERATURE2_UNIT[] = "°C";
const char TEMPERATURE2_COLOR[] = "red";
const boolean TEMPERATURE2_CONNECTED = true;

const char TEMPERATURE3_NAME[] = "Temperatura - tekočina 2";
const char TEMPERATURE3_TYPE[] = "DS18B20";
const char TEMPERATURE3_UNIT[] = "°C";
const char TEMPERATURE3_COLOR[] = "salmon";
const boolean TEMPERATURE3_CONNECTED = true;

#define DHTPIN 2         // DHT sensor is connected to D2 pin
#define DHTTYPE DHT22    // we use DHT-22  (AM2302) sensor

#define ONE_WIRE_BUS 9   // DS18B20 sensor is connected to D9 pin

const int MQxPin1 = A0;  // GAS sensor 1 is connected to A0 pin
const int MQxPin2 = A1;  // GAS sensor 2 is connected to A1 pin

const int led = 7;       // LED diode is connected to D7 pin
const int buzzer = 6;    // buzzer is connected to D6 pin

int gasvalue1;
int gasvalue2;

DHT dht(DHTPIN, DHTTYPE);              // initialize DHT sensor
OneWire oneWire(ONE_WIRE_BUS);         // establish OneWire instance to communicate with any OneWire device
DallasTemperature sensors(&oneWire);   // pass our oneWire reference to Dallas Temperature library

void setup()
{
  Serial.begin(9600);                  // initialize serial port (9600 bps)
  sensors.begin();                     // start up the Dallas Temperature library 
  pinMode(led, OUTPUT);                // initialize LED output
  tone(buzzer, 1000);                  // play 1kHz sound signal...
  delay(100);                          // ...for 0.1 sec
  noTone(buzzer);                      // stop sound.
}

void loop()
{
  digitalWrite(led, HIGH);             // Start reading sensors, diode is ON...
  
  // Read the gas value
  gasvalue1 = analogRead(MQxPin1);
  gasvalue2 = analogRead(MQxPin2);
  
  // Read humidity (it takes about 250 milliseconds, sensor readings may also be up to 2 seconds 'old', because sensor is slow):
  float humidity = dht.readHumidity();
  // read temperature as Celsius
  float temperature1 = dht.readTemperature();

  // Get temperature readings from all devices on the OneWire bus:
  sensors.requestTemperatures();
  float temperature2 = sensors.getTempCByIndex(0);
  float temperature3 = sensors.getTempCByIndex(1);
  
  // Print to serial console
  // values[0], values[1], values[2],
  Serial.print(DEVICE_NAME); Serial.print(","); Serial.print(DEVICE_BTNAME); Serial.print(","); Serial.print(DEVICE_LOCATION); Serial.print(",");


  // values[4]
  if (GAS1_CONNECTED) {
    // values[3]
    Serial.print(GAS1_NAME); Serial.print(",");
    Serial.print(gasvalue1); Serial.print(",");
  }
  else {
    // values[3]
    Serial.print("(ni senzorja)"); Serial.print(",");
    Serial.print("null"); Serial.print(",");
  }


  // values[6]
  if (GAS2_CONNECTED) {
    // values[5]
    Serial.print(GAS2_NAME); Serial.print(",");
    Serial.print(gasvalue2); Serial.print(",");
  }
  else {
    // values[5]
    Serial.print("(ni senzorja)"); Serial.print(",");
    Serial.print("null"); Serial.print(",");
  }


  // values[8]
  if (HUMIDITY_CONNECTED) {
    // values[7]
    Serial.print(HUMIDITY_NAME); Serial.print(",");
    if (isnan(humidity)) {  // Check if reading from DHT-22 fails
      Serial.print("null"); Serial.print(",");
    }
    else
    {
      Serial.print(humidity,0); Serial.print(",");
    }
  }
  else {
    // values[7]
    Serial.print("(ni senzorja)"); Serial.print(",");
    Serial.print("null"); Serial.print(",");
  }


  // values[10]
  if (TEMPERATURE1_CONNECTED) {
    // values[9]
    Serial.print(TEMPERATURE1_NAME); Serial.print(",");    
    if (isnan(temperature1)) {  // Check if reading from DHT-22 fails
      Serial.print("null"); Serial.print(",");
    }
    else
    {
      Serial.print(temperature1,1); Serial.print(",");
    }
  }
  else {
    // values[9]
    Serial.print("(ni senzorja)"); Serial.print(",");  
    Serial.print("null"); Serial.print(",");
  }


  // values[12]
  if (TEMPERATURE2_CONNECTED) {
    // values[11]
    Serial.print(TEMPERATURE2_NAME); Serial.print(",");
    if (temperature2 == -127) {  // Check if reading from OneWire fails
      Serial.print("null"); Serial.print(",");
    }
    else
    {
      Serial.print(temperature2,1); Serial.print(",");
    }
  }
  else {
    // values[11]
    Serial.print("(ni senzorja)"); Serial.print(",");    
    Serial.print("null"); Serial.print(",");
  }


  // values[14]
  if (TEMPERATURE3_CONNECTED) {
    // values[13]
    Serial.print(TEMPERATURE3_NAME); Serial.print(",");
    if (temperature3 == -127) {  // Check if reading from OneWire fails
      Serial.print("null"); Serial.print(",");
    }
    else
    {
      Serial.print(temperature3,1); Serial.print(",");
    }
  }
  else {
    // values[13]
    Serial.print("(ni senzorja)"); Serial.print(",");
    Serial.print("null"); Serial.print(",");
  }


  // values[15]
  Serial.print("EOL");
  Serial.println();
  

  digitalWrite(led, LOW);  // Stop reading sensors, diode is OFF...
  delay(1000);             // wait 1 sec...
}

