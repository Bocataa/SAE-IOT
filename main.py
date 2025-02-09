import RPi.GPIO as GPIO  # GPIO pour Raspberry Pi
import smbus#, Adafruit_DHT  # bibliothèques pour capteurs
import time, sqlite3 # utilitaires
from datetime import datetime # timestamp
from rpi_hardware_pwm import HardwarePWM # PWM Pour le haut-parleur

import adafruit_ssd1306 #écran OLED
from PIL import Image, ImageDraw, ImageFont #écran OLED

from rpi_ws281x import PixelStrip, Color # Strip led


# GPIO
GPIO.setmode(GPIO.BOARD)  # Numérotation broches physiques
GPIO.setwarnings(False) # désactivation des avertissements de sécurité

MQ_pin = 18 # MQ Sensor (GAZ) GPIO24
GPIO.setup(MQ_pin, GPIO.IN) # Configuration du pin en enntrée (on n'utilise pas de resistance pullup/pulldown de la carte !! à cabler électroniquement !! ou pull_up_down=GPIO.PUD_UP)

BP1 = 40 # Bouton 1 carte makerphat
BP2 = 36 #Bouton 2 carte makerphat
GPIO.setup(BP1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BP2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

ledpin = 12  # Broche LED 12
GPIO.setup(ledpin, GPIO.OUT)  # Configurer broche sortie

# Haut Parleur
pwm = HardwarePWM(pwm_channel=1, hz=440, chip=0)
pwm.stop()
#pwm.start(100) # full duty cycle

# Strip Led
    # Définir les paramètres des LEDs
LED_PIN = 12             # GPIO 12 pour envoyer les données
LED_COUNT = 30           # Nombre de LEDs dans la bande
LED_BRIGHTNESS = 255     # Luminosité maximale (0-255)
LED_ORDER = Color(0, 0, 0)  # Ordre des couleurs, on va définir GRB par défaut

    # Initialiser l'objet PixelStrip avec rpi_ws281x (sans auto_write)
strip = PixelStrip(LED_COUNT, LED_PIN, brightness=LED_BRIGHTNESS)
strip.begin()  # Démarrer la communication avec les LEDs


# ADC
addresse = 0x48 # adresse i2c du module PCF8691
capt_son = 0x40  # utiliser 0x40 pour A0, 0x41 pour A1, 0x42 pour A2 et 0x43 pour A3
capt_lum = 0x41

# I2C
bus = smbus.SMBus(1) # définition du bus i2c (parfois 0 ou 2)

# OLED Screen
oled_width = 128 # Largeur écran
oled_height = 64 # Hauteur écran
oled = adafruit_ssd1306.SSD1306_I2C(oled_width, oled_height, bus) # Init écran

    # Effacer l'écran au démarrage
oled.fill(0)
oled.show()

    # Créer une image monochrome pour dessiner
image = Image.new('1', (oled_width, oled_height))
draw = ImageDraw.Draw(image)

def display_text(msg): # Fonction d'affichage text ecran oled
        bbox = draw.textbbox((0, 0), msg, font=font)
        text_width = bbox[2] - bbox[0]  # largeur
        text_height = bbox[3] - bbox[1]  # hauteur
        draw.text((oled_width // 2 - text_width // 2, oled_height // 2 - text_height // 2), text, font=font, fill=255)

    # Charger une police de caractères 
font = ImageFont.load_default()

# HTU21D
    # Déclaration variable
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

# Base de données
emplacement_db = './serveur/database.db3'

# Fonction de lecture des données
def read_data():
    bus.write_byte(addresse,capt_son) # directive: lire l'entree A0
    value_son = bus.read_byte(addresse) # lecture du résultat

    bus.write_byte(addresse,capt_lum) # directive: lire l'entree A0
    value_lum = bus.read_byte(addresse) # lecture du résultat

    # Gaz sensor
    MQ_state = GPIO.input(MQ_pin) # lit l'état du capteur MQ (GAZ et Fumée)

    # HTU21D
    htu_sensor = HTU21D()

    # Lecture des valeurs de température et d'humidité
    temperature = htu_sensor.read_temperature()
    humidity = htu_sensor.read_humidity()
    

    print("capt_son: %1.2f V" %(value_son*5/255)) # Affichage valeur capt_son en Volt
    print("capt_lum: %1.2f V" %(value_lum*5/255)) # Affichage valeur capt_lum en Volt
    print("MQ: %d" % MQ_state) # Affichage valeur capt_lum en Volt
    print(htu_sensor.read_temperature)

    # Retourne les valeurs sous forme d'un tableau (valeurs analogiques convertis en 0-5V)
    return [value_son * 5 / 255,  value_lum * 5 / 255, MQ_state, temperature, humidity]


#Fonction d'envoi des données dans la BDD 
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
        humidity INTEGER,
        )
        ''')

        #insertion des données
        timestamp = datetime.now() # récupération de l'heure pour horodatage
                                
        cur.execute('''INSERT INTO sensor_data (timestamp, smoke_presence, light_level, audio_level, temperature, humidity) VALUES (?, ?, ?, ?, ?, ?)''', (timestamp, data[2], data[1], data[0], 20, 30))

        # Récupérer l'ID de la dernière mesure insérée (si elle existe)
        #sqlite_query1 = """SELECT id FROM mesure ORDER BY id DESC LIMIT 1;"""
        #cur.execute(sqlite_query1)
        #results = cur.fetchone() # résultat de l'ID

        # Calculer le nouvel ID à insérer (si la table est vide, on commence à 1)
        #monId = results[0] + 1 if results else 1

        # Insérer la nouvelle mesure dans la table
        #sqlite_query2 = """INSERT INTO mesure (id, TimeBD, valeur_mesure) VALUES (?, ?, ?);"""
        #timeBDusdepart = datetime.datetime.now()  # Enregistrement de l'heure actuelle
        #cur.execute(sqlite_query2, (monId, timeBDusdepart, temp))

        # Commit des changements et fermer la connexion à la DB
        con.commit()
        con.close()
        #print(f"Mesure insérée : ID={monId}, Temps={timeBDusdepart}, Temp={temp}°C")
    
    except sqlite3.Error as db_error:
        print(f"Erreur lors de l'accès à la base de données : {db_error}")


while True:
    data = read_data() # data correspond à un tableau qui contient les valeurs des capteurs

    # Affichage d'un texte simple sur l'écran OLED
    display_text(data[3] + "°C") 
    send_data(data)
    if data:
        print(f"Son: {data[0]:.2f} V, Lumière: {data[1]:.2f} V, Fumée: {data[2]}, Temp: {data[3]} C, Hum: {data[4]} %")

    if data[1] <= 4:
        GPIO.output(ledpin, GPIO.HIGH)  # Active la LED
    else:
        GPIO.output(ledpin, GPIO.LOW)  # Active la LED
    time.sleep(0.5) # tempo avat nouvelle lecture 



    

