import RPi.GPIO as GPIO  # GPIO pour Raspberry Pi
import smbus  # bibliothèque pour capteurs
import time
import sqlite3  # utilitaires
from datetime import datetime  # timestamp
from rpi_hardware_pwm import HardwarePWM  # PWM Pour le haut-parleur
import adafruit_ssd1306  # écran OLED
import busio  # I2C ecran OLED
from PIL import Image, ImageDraw, ImageFont  # écran OLED
from rpi_ws281x import PixelStrip, Color  # Strip led

# GPIO
try:
    GPIO.setmode(GPIO.BOARD)  # Numérotation broches physiques
except ValueError:
    # GPIO déjà initialisé, alors on ne fait rien, évite des erreurs "already been defined"
    pass
GPIO.setwarnings(False)  # désactivation des avertissements de sécurité

# Configuration des capteurs et périphériques
MQ_pin = 18  # MQ Sensor (GAZ) GPIO24
GPIO.setup(MQ_pin, GPIO.IN)

BP1 = 21  # Bouton carte principale
GPIO.setup(BP1, GPIO.IN)

BP_IHM = 26  # BP carte IHM
GPIO.setup(BP_IHM, GPIO.OUT)  # Configurer broche sortie

# Haut-parleur
pwm = HardwarePWM(pwm_channel=0, hz=440, chip=0)
pwm.stop()  # pwm.start(100) # full duty cycle

# Strip LED
LED_PIN = 21  # GPIO 21 car le 18 est le même canal que le 12 (erreur à notifier)
LED_COUNT = 2  # Nombre de LEDs dans la bande
LED_BRIGHTNESS = 255  # Luminosité maximale (0-255)
LED_ORDER = Color(0, 0, 0)  # Ordre des couleurs, on va définir GRB par défaut

# Initialiser l'objet PixelStrip avec rpi_ws281x (sans auto_write)
strip = PixelStrip(LED_COUNT, LED_PIN, brightness=LED_BRIGHTNESS)
strip.begin()  # Démarrer la communication avec les LEDs

# ADC
addresse = 0x48  # adresse i2c du module PCF8591
capt_son = 0x40  # utiliser 0x40 pour A0, 0x41 pour A1, 0x42 pour A2 et 0x43 pour A3
capt_lum = 0x41
bus = smbus.SMBus(1)  # définition du bus i2c (parfois 0 ou 2)

# OLED Screen
SCL_PIN = 3  # Pin de SCL GPIO3
SDA_PIN = 2  # Pin de SDA GPIO2
i2c_SCREEN = busio.I2C(SCL_PIN, SDA_PIN)
oled_width = 128  # Largeur écran
oled_height = 64  # Hauteur écran
oled = adafruit_ssd1306.SSD1306_I2C(oled_width, oled_height, i2c_SCREEN)  # Init écran

# Effacer l'écran au démarrage
oled.fill(0)
oled.show()

# Créer une image monochrome pour dessiner
image = Image.new('1', (oled_width, oled_height))
draw = ImageDraw.Draw(image)

# Fonction d'affichage texte écran OLED
def display_text(msg):
    bbox = draw.textbbox((0, 0), msg, font=font)
    text_width = bbox[2] - bbox[0]  # largeur
    text_height = bbox[3] - bbox[1]  # hauteur
    draw.text((oled_width // 2 - text_width // 2, oled_height // 2 - text_height // 2), msg, font=font, fill=255)
    oled.image(image)
    oled.show()

# Charger une police de caractères
font = ImageFont.load_default()

# HTU21D
HTU21D_I2C_ADDRESS = 0x40
TRIGGER_TEMP_MEASURE_HOLD = 0xE3
TRIGGER_HUMD_MEASURE_HOLD = 0xE5
RESET_COMMAND = 0xFE

# Création de la classe pour le capteur de température
class HTU21D:
    def __init__(self, bus_number=1):
        self.bus = smbus.SMBus(bus_number)
        self.reset()
        time.sleep(0.1)

    def reset(self):
        self.bus.write_byte(HTU21D_I2C_ADDRESS, RESET_COMMAND)

    def read_temperature(self):
        data = self.bus.read_i2c_block_data(HTU21D_I2C_ADDRESS, TRIGGER_TEMP_MEASURE_HOLD, 3)
        raw_temp = (data[0] << 8) | data[1]
        raw_temp &= 0xFFFC
        temp = -46.85 + (175.72 * raw_temp / 65536.0)
        return temp

    def read_humidity(self):
        data = self.bus.read_i2c_block_data(HTU21D_I2C_ADDRESS, TRIGGER_HUMD_MEASURE_HOLD, 3)
        raw_humidity = (data[0] << 8) | data[1]
        raw_humidity &= 0xFFFC
        humidity = -6.0 + (125.0 * raw_humidity / 65536.0)
        return humidity

# Fonction de lecture des données
def read_data():
    bus.write_byte(addresse, capt_son)  # directive: lire l'entrée A0
    value_son = bus.read_byte(addresse)  # lecture du résultat

    bus.write_byte(addresse, capt_lum)  # directive: lire l'entrée A0
    value_lum = bus.read_byte(addresse)  # lecture du résultat

    # Gaz sensor
    MQ_state = GPIO.input(MQ_pin)  # lit l'état du capteur MQ (GAZ et Fumée)

    # HTU21D
    htu_sensor = HTU21D()

    # Lecture des valeurs de température et d'humidité
    temperature = htu_sensor.read_temperature()
    humidity = htu_sensor.read_humidity()

    print("capt_son: %1.2f V" % (value_son * 5 / 255))  # Affichage valeur capt_son en Volt
    print("capt_lum: %1.2f V" % (value_lum * 5 / 255))  # Affichage valeur capt_lum en Volt
    print("MQ: %d" % MQ_state)  # Affichage capteur de gaz (booleen)
    print(htu_sensor.read_temperature)

    # Retourne les valeurs sous forme d'un tableau (valeurs analogiques converties en 0-5V)
    return [value_son * 5 / 255, value_lum * 5 / 255, MQ_state, temperature, humidity]

# Base de données
emplacement_db = './serveur/database.db3'

# Fonction d'envoi des données dans la BDD
def send_data(data):
    try:
        # Connexion à la base de données SQLite
        con = sqlite3.connect(emplacement_db)
        con.row_factory = sqlite3.Row  # Permet d'accéder aux résultats comme des dictionnaires
        cur = con.cursor()

        cur.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                data_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                smoke_presence BOOLEAN,
                light_level FLOAT,
                audio_level FLOAT,
                temperature FLOAT,
                humidity INTEGER
            )
        ''')

        # Insertion des données
        timestamp = datetime.now()  # récupération de l'heure pour horodatage
        cur.execute('''
            INSERT INTO sensor_data (timestamp, smoke_presence, light_level, audio_level, temperature, humidity)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, data[2], data[1], data[0], data[3], data[4]))

        # Commit des changements et fermeture de la connexion à la DB
        con.commit()
        con.close()
    except sqlite3.Error as db_error:
        print(f"Erreur lors de l'accès à la base de données : {db_error}")

# Boucle principale
try:
    while True:
        data = read_data()  # data correspond à un tableau qui contient les valeurs des capteurs
        strip.setPixelColor(0, Color(255, 0, 0))  # LED 1 : Rouge
        strip.setPixelColor(1, Color(0, 0, 255))  # LED 1 : Rouge
        strip.show()

        # Affichage d'un texte simple sur l'écran OLED
        display_text("Hello World")

        send_data(data)
        if data:
            print(f"Son: {data[0]:.2f} V, Lumière: {data[1]:.2f} V, Fumée: {data[2]}, Temp: {data[3]} C, Hum: {data[4]} %")
        time.sleep(5)
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
