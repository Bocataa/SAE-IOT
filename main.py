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
import threading #pour gérer les interruptions boutons

# Debug affichage du répertoire de travail
#import os
#print(f"Répertoire de travail actuel: {os.getcwd()}")

# GPIO
try:
    GPIO.setmode(GPIO.BOARD)  # Numérotation broches physiques
except ValueError:
    # GPIO déjà initialisé, alors on ne fait rien, évite des erreurs "already been defined"
    pass
GPIO.setwarnings(False)  # désactivation des avertissements de sécurité

# Configuration des capteurs et périphériques
MQ_pin = 17  # MQ Sensor (GAZ) GPIO17
GPIO.setup(MQ_pin, GPIO.IN)

relay_pin = 23
GPIO.setup(relay_pin, GPIO.OUT) # Configurer broche sortie

BP_IHM = 26  # BP carte IHM GPIO 26
LED_IHM = 19 # LED IHM GPIO 19
GPIO.setup(BP_IHM, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Configurer broche entrée avec pull-down
GPIO.setup(LED_IHM, GPIO.OUT) # Configurer broche sortie

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

# Variables globales
running = True
mode = 0  # 0 = heure, 1 = température/humidité, 2 = lumière, 3 = son
sound_threshold = 50  # Seuil de déclenchement de l'alarme sonore (valeur par défaut)
luminosity_threshold = 50  # Seuil de luminosité pour activer le relais (valeur par défaut)

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

# Fonction d'affichage texte écran OLED
def display_text(msg):
    image = Image.new('1', (128, 64))
    draw = ImageDraw.Draw(image)

    # Charger la police
    try:
        font = ImageFont.truetype("./html/ressources/font/font.ttf", 26)  # Remplacez par le bon chemin
    except IOError:
        font = ImageFont.load_default()  # Si la police ne se charge pas, utiliser la police par défaut
        #print('erreur de chargement de la police') # debug

    bbox = draw.textbbox((0, 0), msg, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    draw.text((64 - text_width // 2, 32 - text_height // 2), msg, font=font, fill=255)
    oled.image(image)
    oled.show()

# Fonction de lecture des données
def read_data():
    if not running:
        return 0

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

    print("capt_son: %1.2f pourcent" % (value_son * 100 / 255))  # Affichage valeur capt_son en %
    print("capt_lum: %1.2f pourcent" % (value_lum * 100 / 255))  # Affichage valeur capt_lum en %
    print("MQ: %d" % MQ_state)  # Affichage capteur de gaz (booléen)
    print(f"Température: {temperature:.2f}°C, Humidité: {humidity:.2f}%")

    # Retourne les valeurs sous forme d'un tableau avec les valeurs exploitables
    return [value_son*100/255, value_lum*100/255 , MQ_state, temperature, humidity]

# Base de données
emplacement_db = './html/serveur/database.db3'

# Fonction d'envoi des données dans la BDD
def send_data():
    while running:
        data = read_data()
        if data[0] is not None:
            try:
                con = sqlite3.connect(emplacement_db)
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
                timestamp = datetime.now()
                cur.execute('''INSERT INTO sensor_data (timestamp, smoke_presence, light_level, audio_level, temperature, humidity)
                            VALUES (?, ?, ?, ?, ?, ?)''', (timestamp, data[2], data[1], data[0], data[3], data[4]))
                con.commit()
                con.close()
            except sqlite3.Error as db_error:
                with open("log.txt", "a") as log_file: # On sauvegarde les erreurs dans un fichier de logs
                    log_file.write(f"{datetime.now()} - {str(db_error)}\n")
        time.sleep(10)  # Envoi des données toutes les 10 secondes

# Fonction de gestion du bouton IHM
def button_handler(channel):
    global mode, running

    press_time = time.time()
    while GPIO.input(BP_IHM) == GPIO.HIGH:
        if time.time() - press_time > 5:  # Appui long
            running = False
            GPIO.output(LED_IHM, GPIO.LOW)
            display_text("System OFF")
            fade_leds()
            return

    # Changement de mode si appui court
    mode = (mode + 1) % 4
    update_display()

# Fonction de mise à jour de l'affichage et des LEDs
def update_display_and_leds():
    global sound_threshold, luminosity_threshold
    while running:
        data = read_data()

        if mode == 0:
            display_text(datetime.now().strftime("%H:%M:%S"))
            color = Color(0, 255, 0)  # Vert par défaut pour température
        elif mode == 1:
            display_text(f"Temp: {data[3]:.1f}C\nHum: {data[4]}%")
            color = Color(255, 0, 0)  # Rouge pour température
        elif mode == 2:
            display_text(f"Lum: {data[1]:.2f}V")
            color = Color(0, 0, 255)  # Bleu pour lumière
        elif mode == 3:
            display_text(f"Son: {data[0]:.2f}V")
            color = Color(255, 255, 0)  # Jaune pour son

        # Mise à jour de la bande LED en fonction des niveaux
        if mode == 1:
            color = Color(int(data[3] * 2.55), 0, int(255 - data[3] * 2.55))  # Dégradé rouge-bleu pour température
        elif mode == 2:
            color = Color(0, int(data[4] * 2.55), int(255 - data[4] * 2.55))  # Dégradé vert-bleu pour humidité

        # Mise à jour de la bande LED
        strip.setPixelColor(0, color)
        strip.setPixelColor(1, color)
        strip.show()
        GPIO.output(LED_IHM, GPIO.HIGH)  # Active la LED

        # Vérification des seuils
        if data[0] * 100 / 255 > sound_threshold:
            pwm.start(100)  # Déclencher l'alarme sonore
        else:
            pwm.stop()

        if data[1] * 100 / 255 < luminosity_threshold:
            GPIO.output(relay_pin, GPIO.HIGH)  # Activer le relais
        else:
            GPIO.output(relay_pin, GPIO.LOW)  # Désactiver le relais

        time.sleep(1)

# Fonction pour mettre à jour l'affichage en fonction du mode
def update_display():
    data = read_data()
    if mode == 0:
        display_text(datetime.now().strftime("%H:%M:%S"))
    elif mode == 1:
        display_text(f"Temp: {data[3]:.1f}C\nHum: {data[4]}%")
    elif mode == 2:
        display_text(f"Lum: {data[1]:.2f}V")
    elif mode == 3:
        display_text(f"Son: {data[0]:.2f}V")

# Fonction pour l'effet de fondu progressif des LEDs
def fade_leds():
    for brightness in range(255, -1, -5):
        color = Color(brightness, brightness, brightness)
        strip.setPixelColor(0, color)
        strip.setPixelColor(1, color)
        strip.show()
        time.sleep(0.05)
    strip.setPixelColor(0, Color(0, 0, 0))
    strip.setPixelColor(1, Color(0, 0, 0))
    strip.show()

# Animation de démarrage
def startup_animation():
    colors = [Color(255, 0, 0), Color(0, 255, 0), Color(0, 0, 255)]
    for _ in range(3):
        for color in colors:
            strip.setPixelColor(0, color)
            strip.setPixelColor(1, color)
            strip.show()
            time.sleep(0.5)
    strip.setPixelColor(0, Color(0, 0, 0))
    strip.setPixelColor(1, Color(0, 0, 0))
    strip.show()

# Détection des interruptions du bouton
try: # Pour ne pas faire crash le programme en cas d erreur
    GPIO.add_event_detect(BP_IHM, GPIO.RISING, callback=button_handler, bouncetime=300) 
except RuntimeError as e:
    print(f"Erreur lors de l'ajout de la détection d'événement: {e}")

# Lancement des threads pour l'affichage et l'envoi de données
threading.Thread(target=update_display_and_leds, daemon=True).start()
threading.Thread(target=send_data, daemon=True).start()

# Animation de démarrage
startup_animation()

# Boucle principale
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()
