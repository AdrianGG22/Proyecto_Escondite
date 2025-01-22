# -*- coding: utf-8 -*-
# from __future__ import print_function
import rospy, cv2, cv_bridge
import numpy as np
import time
from sensor_msgs.msg import Image
from std_msgs.msg import String, Int32, Bool

TOPIC_START_DETECCION = "/deteccion"
TOPIC_CAM = "/color_detected"
TOPIC_IMAGE = "/image_raw"

# Definimos el umbral píxeles mínimo para considerar que hemos detectado el color
UMBRAL_PIXELS = 100

# Clase para detectar un color
class ColorDetector:
     
    def __init__(self):
        
        self.bridge = cv_bridge.CvBridge()                          # Creamos el puente entre formatos
        self.pub = rospy.Publisher(TOPIC_CAM, String, queue_size=5) # Creamos el publicador de color detectado
        
        self.red = True         # Flag para saber si la detección de rojo está activa
        self.green = True       # Flag para saber si la detección de verde está activa
        self.blue = True        # Flag para saber si la detección de azul está activa
        self.detection = False  # Flag para saber si la detección general está activa

        self.main()
        
    def main(self):
        # Creamos el suscriptor del topic donde se publican los frames de la cámara
        self.image_sub = rospy.Subscriber(TOPIC_IMAGE, Image, self.image_callback)

        # Callback que detecta la activación y desactivación de la detección                                  
        self.toggle_detection_sub = rospy.Subscriber(TOPIC_START_DETECCION, Bool, self.toggle_detection_callback)

    # Función image_callback:
    def image_callback(self, msg):

        if not self.detection:  # Si la detección está desactivada, no procesamos la imagen
            return

        # Conversiones entre formatos de color de imagen
        cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")   # Convertimos la imagen recibida a BGR
        hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)     # Convertimos la imagen de BGR a HSV

        # Definimos los rangos de detección del color rojo en HSV
        lower_red = np.array([0,50,50])     # Límite inferior del color rojo
        upper_red = np.array([10,255,255])  # Límite superior del color rojo

        # Definimos los rangos de detección para el color verde en HSV
        lower_green = np.array([50, 50, 50])    # Límite inferior del color verde
        upper_green = np.array([70, 255, 255])  # Límite superior del color verde

        # Definimos los rangos de detección para el color azul en HSV
        lower_blue = np.array([110, 50, 50])    # Límite inferior del color azul
        upper_blue = np.array([130, 255, 255])  # Límite superior del color azul

        # Creamos una máscara binaria: nos sirve para identificar las zonas de la imagen dentro del rango del color
        mask_red = cv2.inRange(hsv, lower_red, upper_red)       # Máscara para rojo
        mask_green = cv2.inRange(hsv, lower_green, upper_green) # Máscara para verde
        mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)    # Máscara para azul

        # Contamos el número de píxeles en la máscara (para saber la cantidad de píxeles de color)
        pixels_red = cv2.countNonZero(mask_red)
        pixels_green = cv2.countNonZero(mask_green)
        pixels_blue = cv2.countNonZero(mask_blue)

        # Si la cantidad de píxeles rojos es mayor a UMBRAL_PIXELS, publicamos que se ha detectado un objeto rojo
        if pixels_red>UMBRAL_PIXELS and self.red:
            self.pub.publish("rojo")
            self.red = False
            # rospy.loginfo(f"Objeto rojo detectado.")  # Se ha utilizado para depuración

        # Si la cantidad de píxeles verdes es mayor a UMBRAL_PIXELS, publicamos que se ha detectado un objeto verde
        elif pixels_green>UMBRAL_PIXELS and self.green:
            self.pub.publish("verde")
            self.green = False
            # rospy.loginfo(f"Objeto verde detectado.") # Se ha utilizado para depuración

        # Si la cantidad de píxeles azules es mayor a UMBRAL_PIXELS, publicamos que se ha detectado un objeto azul
        elif pixels_blue>UMBRAL_PIXELS and self.blue:
            self.pub.publish("azul")
            self.blue = False
            # rospy.loginfo(f"Objeto azul detectado.")  # Se ha utilizado para depuración

    # Callback que detecta la activación y desactivación de la detección
    def toggle_detection_callback(self, msg):
        self.detection = msg.data   # Activamos o desactivamos la detección
        rospy.loginfo(f"Detección de obstáculos {'activada' if self.detection else 'desactivada'}.")


# Creamos el nodo detector del color y lo mantenemos activo
rospy.init_node('color_detector')
cd  = ColorDetector()
rospy.spin()