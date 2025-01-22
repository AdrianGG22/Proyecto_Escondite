#!/usr/bin/env python3
import rospy
from std_msgs.msg import String, Bool
import torch
import cv2
import warnings

# Obviar warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Ruta al modelo entrenado
MODEL_PATH = "../trained_model/best.pt"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

TOPIC_START_DETECCION = "/deteccion"
TOPIC_CAM = "/human_detected"

# Lista para almacenar las personas detectadas
humans_detected = []

class Yolov5:
    def __init__(self):
        self.toggle_camera_sub = rospy.Subscriber(TOPIC_START_DETECCION, Bool, self.toggle_camera_callback)
        self.task_done = False
        
        # Inicializar el modelo
        self.model = torch.hub.load("ultralytics/yolov5", "custom", path=MODEL_PATH, force_reload=True)  # Cargar el modelo
        self.model.to(DEVICE)  # Mover el modelo al dispositivo adecuado
        
        # Nos subscribimos al topic
        camara_estado = rospy.Publisher('/camara_lista', Bool, queue_size=5)
        
        rospy.sleep(1)
        camara_estado.publish(True)
        camara_estado.unregister()
        

    def toggle_camera_callback(self, msg):
        # Verifica si el estado ha cambiado
        if msg.data:
            rospy.sleep(5)
            rospy.loginfo("Detección de caras activada")
            self.main()

    def main(self):
        pub_human = rospy.Publisher(TOPIC_CAM, String, queue_size=10)
        
        # Inicializar la cámara
        cap = cv2.VideoCapture(0)  # 0 es el ID de la cámara por defecto

        if not cap.isOpened():
            print("Error: No se pudo acceder a la cámara.")
            exit()

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error al capturar el frame.")
                break

            # Realizar detección
            results = self.model(frame)

            # Extraer información de las detecciones
            detections = results.pandas().xyxy[0]  # Convertir las detecciones a un DataFrame
            detected_human = None  # Variable en la que guardar la persona detectada

            global humans_detected

            for index, row in detections.iterrows():
                detected_human = row['name']  # Agregar el nombre de la clase detectada a la lista

            # Si se ha detectado a alguien y ese alguien no ha sido anteriormente entonces tarea terminada
            if not (detected_human in humans_detected) and detected_human:
                humans_detected.append(detected_human)
                self.task_done = True

            # Obtener el frame procesado (una sola imagen renderizada)
            rendered_frame = results.render()[0]  # Renderiza las detecciones en el frame
            rendered_frame = cv2.cvtColor(rendered_frame, cv2.COLOR_RGB2BGR)  # Convertir a formato correcto para OpenCV

            # Salir si se ha terminado la tarea o se ha cerrado ROS
            if self.task_done or rospy.is_shutdown():
                pub_human.publish(detected_human)
                self.task_done = False
                break

        # Liberar la cámara y cerrar ventanas
        cap.release()
        cv2.destroyAllWindows()

rospy.init_node('deteccion_node')
cd = Yolov5()
rospy.spin()
