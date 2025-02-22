from flask import Flask, render_template, request, jsonify # serveur Flask pour gérer les paramètres utilisateur
from flask_cors import CORS # évite les erreurs cross origine
from gpiozero import Button, LED, DigitalOutputDevice # Utilisation des gpio
from gpiozero.pins.rpigpio import RPiGPIOFactory 
import smbus # I2C CAN
import time #chrono, sleep ...
import sqlite3 # Base de donnée
from datetime import datetime # timestamp
from rpi_hardware_pwm import HardwarePWM # Utilisation de PWM pour le haut parleur
import adafruit_ssd1306 # Ecran OLED
import busio # I2C ecran OLED
from PIL import Image, ImageDraw, ImageFont # ecran OLED
from rpi_ws281x import PixelStrip, Color # STRIP LED
import threading # thread

# Debug affichage du répertoire de travail
#import os
#print(f"Répertoire de travail actuel: {os.getcwd()}")

app = Flask(__name__)
CORS(app) # pour eviter les erreurs de sécurité sur les routes

# Forcer l'utilisation de RPi.GPIO
RPiGPIOFactory()

# Configuration des capteurs et périphériques
MQ_pin = 17  # MQ Sensor (GAZ) GPIO17
mq_sensor = Button(MQ_pin) #Utiliser comme une entrée so

relay_pin = 23
relay = DigitalOutputDevice(relay_pin)

BP_IHM = 26  # BP carte IHM GPIO 26
LED_IHM = 19 # LED IHM GPIO 19
button = Button(BP_IHM, pull_up=False, bounce_time=0.05)
led_ihm = LED(LED_IHM)

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
sound_threshold = 70  # Seuil de déclenchement de l'alarme sonore (valeur par défaut)
luminosity_threshold = 60  # Seuil de luminosité pour activer le relais (valeur par défaut)
force_relay = 0 # Variable de forcage de l etat du relais par l'utilisateur
state_relay = 0

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
        font = ImageFont.truetype("/home/geii/html/ressources/font/font.ttf", 26)  # Chemin de la font
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
        return [0, 0, 0, 0, 0]  # Retourner une liste par défaut si running est False

    bus.write_byte(addresse, capt_son)  # directive: lire l'entrée A0
    value_son = bus.read_byte(addresse)  # lecture du résultat

    bus.write_byte(addresse, capt_lum)  # directive: lire l'entrée A0
    value_lum = bus.read_byte(addresse)  # lecture du résultat

    # Gaz sensor
    MQ_state = mq_sensor.value  # lit l'état du capteur MQ (GAZ et Fumée)

    # HTU21D
    htu_sensor = HTU21D()

    # Lecture des valeurs de température et d'humidité
    temperature = htu_sensor.read_temperature()
    humidity = htu_sensor.read_humidity()

    print("capt_son: %1.2f pourcent" % (value_son * 100 / 255))  # Affichage valeur capt_son en %
    print("capt_lum: %1.2f pourcent" % (value_lum * 100 / 255))  # Affichage valeur capt_lum en %
    print("MQ: %d" % MQ_state)  # Affichage capteur de gaz (booléen)
    print(f"Temperature: {temperature:.2f} C, Humidite: {humidity:.2f} %")

    # Retourne les valeurs sous forme d'un tableau avec les valeurs exploitables
    return [value_son*100/255, value_lum*100/255 , MQ_state, temperature, humidity]

# Base de données
emplacement_db = '/home/geii/html/serveur/database.db3'

# Fonction d'envoi des données dans la BDD
def send_data():
    while running:
        data = read_data()
        if data[0] is not None: #si on a bien une mesure
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
            except sqlite3.Error as db_error: # pour la maintenance
                print(f"error: {db_error}")
        time.sleep(5)  # Envoi des données toutes les 5 secondes

# Fonction de gestion du bouton IHM
def button_handler():
    global mode, running

    press_time = time.time()
    while button.is_pressed:
        if (time.time() - press_time > 5) and not running:  # Appui long de 5 secondes pour redémarrer le système
            running = True
            time.sleep(0.3)
            pwm.stop()
            startup_animation()
            led_ihm.on()
            display_text("System ON")
            update_display()
            threading.Thread(target=update_display_and_leds, daemon=True).start() # thread de mise à jour der l'écran et des leds
            threading.Thread(target=send_data, daemon=True).start() # thread envoi des données à la BDD
            threading.Thread(target= run_flask_app, daemon=True).start() # Thread serveur flask sur le port 5000!
            break
        elif (time.time() - press_time > 3) and running:  # Appui long de 3 secondes pour éteindre le système
            running = False
            time.sleep(0.3)
            pwm.stop()
            fade_leds()
            led_ihm.off()
            display_text("System OFF")
            break

    # Changement de mode si appui court
    if running:
        mode = (mode + 1) % 4
        update_display()

# Fonction de mise à jour de l'affichage et des LEDs
def update_display_and_leds():
    global sound_threshold, luminosity_threshold, state_relay
    while running:
        data = read_data()

        if mode == 0:
            display_text(datetime.now().strftime("%H:%M:%S"))
            color = Color(255, 255, 255)  # Blanc écran par défaut
        elif mode == 1:
            display_text(f"Temp: {data[3]:.1f}C\nHum: {data[4]:.1f}%")
        elif mode == 2:
            display_text(f"Lum: {data[1]:.2f}%")
        elif mode == 3:
            display_text(f"Son: {data[0]:.2f}%")

        # Mise à jour de la bande LED en fonction des niveaux
        if mode == 1:
            if (data[3] <= 18):
                color = Color(255-int(255 * (data[3]/18)), 255-int(255 * (data[3]/18)), 255) # si froid bleu produit en croix n/18 (car 18 est le max) donne un coeff pour variance de bleu plus clair vers le froid
            elif (data[3] > 18) and (data[3] <= 25):
                color = Color(255-int(255 * (data[3]/25)), 255, 0) #variance de vert qui tend vers le jaune
            elif (data[3] > 25):
                color = Color(255, 255-int((255 * data[3]/60)), 255-int((255 * data[3]/60)))  # Variance de orange à Rouge on fixe le max à 60
        elif mode == 2:
            color = Color(int(255*data[1]/100), int(255*data[1]/100), 0) # Jaune plus ou moins éclairé
        elif mode == 2:
            color = Color(int(233*data[0]/100), int(39*data[0]/100), int(249*data[0]/100))  # violet plus ou moins éclairé  

        # Mise à jour de la bande LED
        strip.setPixelColor(0, color)
        strip.setPixelColor(1, color)
        strip.show()
        led_ihm.on()  # Active la LED

        # Vérification des seuils
        if (data[0]  > sound_threshold) or (data[2] == 1): # On déclenche l'alarme si on dépasse le seuil son ou si on détecte du gaz
            pwm.start(50)  # Déclencher l'alarme sonore
            time.sleep(1)
        else:
            pwm.stop()

        if (data[1]  < luminosity_threshold and force_relay == 0) or force_relay == 1 : # Active le relais si on est inférieur au seuil de luminosité (Lumière)
            relay.off()  # Activer le relais
            state_relay = 1
        elif (data[1]  > luminosity_threshold and force_relay == 0) or force_relay == 2:
            relay.on()  # Désactiver le relais
            state_relay = 0


# Fonction pour mettre à jour l'affichage en fonction du mode
def update_display():
    data = read_data()
    if mode == 0:
        display_text(datetime.now().strftime("%H:%M:%S"))
    elif mode == 1:
        display_text(f"Temp: {data[3]:.1f}C\nHum: {data[4]:.1f}%")
    elif mode == 2:
        display_text(f"Lum: {data[1]:.2f}%")
    elif mode == 3:
        display_text(f"Son: {data[0]:.2f}%")

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
    for brightness in range(0, 256, 5):  # Inverse de l'original : on commence à 0 et on monte jusqu'à 255
        color = Color(brightness, brightness, brightness)
        strip.setPixelColor(0, color)
        strip.setPixelColor(1, color)
        strip.show()
        time.sleep(0.05)

# Fonction lancement de flask sur le port 5000
def run_flask_app():
    app.run(host='0.0.0.0', port=5000)

# Flask 
@app.route('/toggle_BP_IHM', methods=['POST'])
def Virtual_button_handler(): # Fonction de gestion BP IHM Virtuel
    global running
    if not running:  # Appui long de 5 secondes pour redémarrer le système
        running = True
        time.sleep(0.3)
        pwm.stop()
        startup_animation()
        led_ihm.on()
        display_text("System ON")
        update_display()
        threading.Thread(target=update_display_and_leds, daemon=True).start() # thread de mise à jour der l'écran et des leds
        threading.Thread(target=send_data, daemon=True).start() # thread envoi des données à la BDD
        threading.Thread(target= run_flask_app, daemon=True).start() # Thread serveur flask sur le port 5000!
    elif running:  # Appui long de 3 secondes pour éteindre le système
        running = False
        time.sleep(0.3)
        pwm.stop()
        fade_leds()
        led_ihm.off()
        display_text("System OFF")
    return '', 200 # retourne rien juste code 200 = succès

@app.route('/update_thresholds', methods=['POST']) 
def update_thresholds():
    global sound_threshold, luminosity_threshold
    data = request.get_json()  # Récupère les données JSON
    sound_threshold = int(data.get('sound_threshold', 0))  # Défaut à 0 si la clé n'existe pas ou si la conversion échoue
    luminosity_threshold = int(data.get('luminosity_threshold', 0))  # Défaut à 0 si la clé n'existe pas ou si la conversion échoue
    #print(f"new seuil son: {sound_threshold}, new seuil lumière: {luminosity_threshold}") #DEBUG
    return '', 200

@app.route('/get_thresholds') 
def fetch_thresholds():
    global sound_threshold, luminosity_threshold
    return jsonify({'sound_threshold': sound_threshold, 'luminosity_threshold': luminosity_threshold})

@app.route('/get_running_state') 
def fetch_running_state():
    global running
    return jsonify({'running_state': running})


@app.route('/force_relay_on', methods=['POST']) # Force le relay à on 
def force_relay_on():
    global force_relay
    force_relay = 1
    return '', 200  # Ajout d'une réponse vide avec un code 200 pour signaler que tout s'est bien passé.

@app.route('/force_relay_off', methods=['POST']) # Force le relay à on 
def force_relay_of():
    global force_relay
    force_relay = 2
    return '', 200  # Ajout d'une réponse vide avec un code 200 pour signaler que tout s'est bien passé.

@app.route('/unforce_relay', methods=['POST']) # Force le relay à on 
def unforce_relay():
    global force_relay  
    force_relay = 0
    return '', 200  # Ajout d'une réponse vide avec un code 200 pour signaler que tout s'est bien passé.

@app.route('/get_state_relay') # Retourne l'état actuel du relais
def get_state_relay():
    global state_relay 
    return jsonify({'state_relay' : state_relay})




# Détection des interruptions du bouton
button.when_pressed = button_handler # interruption avec lib gpiozero

# Lancement des threads pour l'affichage et l'envoi de données
threading.Thread(target=update_display_and_leds, daemon=True).start() # thread de mise à jour der l'écran et des leds
threading.Thread(target=send_data, daemon=True).start() # thread envoi des données à la BDD
threading.Thread(target= run_flask_app, daemon=True).start() # Thread serveur flask sur le port 5000!

# Animation de démarrage
startup_animation()

# Boucle principale
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    led_ihm.off()
    relay.off()
