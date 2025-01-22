# -*- coding: utf-8 -*-
# from __future__ import print_function

import rospy
import subprocess
import smach_ros
import math
import actionlib
import os
from smach import State, StateMachine
from smach_ros import SimpleActionState
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from actionlib_msgs.msg import GoalID
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String, Int32, Bool
from geometry_msgs.msg import Twist

# Topics que se van a utilizar
TOPIC_CAM = None                        # Topic donde los detectores publican los objetos detectados
TOPIC_EXPLORE_STATE = "/explore_state"  # Topic del estado de exploración
TOPIC_DETECCION = "/deteccion"          # Topic para activar o desactivar la detección

# Variables globales
humans_to_find = ["daniel", "adrian", "martin"] # Lista con las personas a encontrar
color_to_find = ["rojo", "verde", "azul"]       # Lista con los colores a encontrar
objects_to_find = None
objects_found = []

# Definimos la posición de origen
BASE_POSE = (0.0, 0.0), (0.0, 0.0, 0.0, 1.0)  # Posición origen en (x,y) = (0,0) y orientación (x,y,z,w) = (0,0,0,1)
POSE_1 = (0.0, 2.0), (0.0, 0.0, 0.0, 1.0)

# Clase del estado: GetReadyToStart
class GetReadyToStart(State):
    # Inicialización: 
    def __init__(self):
        State.__init__(self, outcomes=['ready_to_start'])   # Creamos el estado y la salida del estado

    # Función execute: creamos el flujo del estado
    def execute(self, userdata):
        global TOPIC_CAM
        global objects_to_find

        print(f"Vamos a jugar al escondite!")

        # Inicializamos las variables necesarias y hacemos preparaciones

        # Preguntamos al jugador que desea detectar:
        while True:
            print()
            user_input = input("¿Que deseas detectar? (Personas = p | Colores = c): ").strip().lower()
            # En función de lo que se haya elejido a detectar...
            # Personas:
            if user_input == "p":
                print("¡Genial! Vamos a buscar a Daniel, Adrian y Martin.")
                print()
                TOPIC_CAM = "/human_detected"
                objects_to_find = humans_to_find
                subprocess.Popen(['python3', 'human_detector.py'])
                rospy.wait_for_message('/camara_lista', Bool)
                break

            # Colores
            elif user_input == "c":
                print("¡Genial! Vamos a buscar obstáculos de color.")
                print()
                TOPIC_CAM = "/color_detected"
                objects_to_find = color_to_find
                subprocess.Popen(['python3', 'color_detector.py'])
                break

            # Opción no válida:
            else:
                print(f"{user_input} no es una opción válida. Por favor selecciona una opción válida.")
        
        return "ready_to_start" # Devolvemos "ready_to_start" para finalizar y cambiar al siguiente estado

# Clase del estado: WanderAndSearch
class WanderAndSearch(State):

    # Inicialización:
    def __init__(self):
        State.__init__(self, outcomes=['object_detected'])                          # Creamos el estado y la salida del estado
        self.object_detected = False                                                # Variable para saber si hemos detectado un objeto
        self.object = None                                                          # Variable para almacenar el nombre del objeto
        self.explore_state = False                                                  # Variable para el estado de exploración
        self.pub_Deteccion = rospy.Publisher(TOPIC_DETECCION, Bool, queue_size=5)   # Publicador de estado de detección
        
    # Función execute: creamos el flujo del estado
    def execute(self, userdata):
        global objects_found    # Variable con los objetos encontrados
        
        self.sub_Object = rospy.Subscriber(TOPIC_CAM, String, self.object_detected_callback)    # Suscriptor del topic de la cámara (TOPIC_CAM)
        rospy.sleep(2)
        rate = rospy.Rate(10)

        # Damos comienzo a la exploración y navegación del entorno
        self.launch_explore_lite()          # Comenzamos la exploración
        self.explore_state = True           # Guardamos el estado de exploración como activo
        self.pub_Deteccion.publish(True)    # Publicamos el comienzo de la detección

        # Bucle de espera: hasta que no se detecte un objeto, seguimos explorando
        while not self.object_detected:
            rate.sleep()

        # Cuando encontremos algun objeto
        if self.object_detected:
            self.sub_Object.unregister()        # Nos desuscribimos del topic para "limpiar" el nodo
            objects_found.append(self.object)   # Añadimos el objeto encontrado
            self.object_detected = False        # Reiniciamos la variable de objeto detectado
            self.pub_Deteccion.publish(False)   # Finalizamos la detección
            self.stop_exploring()               # Finalizamos la exploración
        
        # Creamos el nodo suscriptor del estado del estado de exploración
        self.sub_ExploreState = rospy.Subscriber(TOPIC_EXPLORE_STATE, Bool, self.explore_stopped_callback) # Suscriptor del topic de estado de exploración
        rate = rospy.Rate(10)

        # Bucle de espera: hasta que no se desactive la exploración, no acabamos el estado
        while self.explore_state:
            rate.sleep()

        if not self.explore_state:
            self.sub_ExploreState.unregister()  # Nos desuscribimos del topic para "limpiar" el nodo

        return "object_detected" # Devolvemos "object_detected" para finalizar y cambiar al siguiente estado

    # Función que se encarga de lanzar el algoritmo de explore lite para poder explorar y navegar
    def launch_explore_lite(self):
        rospy.loginfo("Lanzando nodo de exploración...")
        # Lanzamos explore lite con roslaunch en un proceso separado
        subprocess.Popen(["roslaunch", "explore_lite", "explore.launch"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # rospy.loginfo("Nodo de exploración activo.")  # Se ha utilizado para depuración

    # Función que se encarga de detener el algoritmo de explore lite
    def stop_exploring(self):
        
        # Se intenta detener explore_lite
        try:
            rospy.loginfo("Deteniendo la exploración...")
            # Se ejecuta el fichero stop_exploring.py para detener explore_lite
            subprocess.Popen(['python3', 'stop_exploring.py'])
        
        # Si no se consigue
        except Exception as e:
            rospy.logerr(f"No ha sido posible detener la exploración: {e}")

    # Callback de cuando se detecta un objeto
    def object_detected_callback(self, msg):
        # Mostramos el nombre del objeto encontrado
        print(f"Te encontré {msg.data}")

        # Almacenamos el objeto y activamos el flag de objeto detectado
        self.object = msg.data
        self.object_detected = True

    # Callback de cuando se detiene explore lite
    def explore_stopped_callback(self, msg):
        rospy.loginfo("Exploración detenida correctamente")
        # Actualizamos el estado de explore lite
        self.explore_state = msg.data

# Clase del estado: ReturnToBase
class ReturnToBase(State):
    
    # Inicialización:
    def __init__(self):
        State.__init__(self, outcomes=['keep_finding', 'game_end'])   # Creamos el estado y las salidas del estado
        self.base = None    # Variable que guarda la posición base

    # Función execute: creamos el flujo del estado
    def execute(self, userdata):
        
        self.base_pose()    # Se encarga de crear la posición base y guardarla en su variable

        # Inicializamos el cliente de acción para 'move_base'
        client = actionlib.SimpleActionClient("move_base", MoveBaseAction)
        client.wait_for_server()

        # Creamos el objetivo de navegación
        goal = self.base

        # Enviamos la orden de volver a base
        rospy.loginfo("Volviendo a base...")
        client.send_goal(goal)
        client.wait_for_result()

        # Verificamos si el robot ha llegado a base
        if client.get_state() == actionlib.GoalStatus.SUCCEEDED:

            rospy.loginfo("He llegado a base.")
            rospy.loginfo(f"De momento encontré a {', '.join(objects_found)}")  # Mostramos que objetos se han encontrado por el momento

            # Si ya se han encontrado todos los objetos:
            if set(objects_to_find).issubset(set(objects_found)):
                rospy.loginfo(f"He encontrado todos los objetos. Encontré a {', '.join(objects_found)}.")
                # Terminamos el estado y terminamos el juego del escondite
                return "game_end"
            
            # Si faltan objetos por encontrar:
            else:
                missing_objects = set(objects_to_find) - set(objects_found)
                rospy.loginfo(f"Faltan {', '.join(missing_objects)} por encontrar. Seguiré buscando.")

                # Terminamos el estado, pero volvemos al estado de búsqueda WanderAndSearch
                return "keep_finding"
        
        # En caso de que no se cosiga llegar a la base, se acaba el juego
        else:

            rospy.loginfo("No he podido llegar a base.")
            return "game_end"
        
    
    # Con está función guardamos la posición origen
    def base_pose(self):
        self.base = MoveBaseGoal()
        self.base.target_pose.header.stamp = rospy.Time.now()
        self.base.target_pose.header.frame_id = 'map'               # La posición es respecto al frame o sistema 'map'
        self.base.target_pose.pose.position.x = BASE_POSE[0][0]     # Posición x
        self.base.target_pose.pose.position.y = BASE_POSE[0][1]     # Posición y
        self.base.target_pose.pose.position.z = 0.0                 # Posición z
        self.base.target_pose.pose.orientation.x = BASE_POSE[1][0]  # Orientación x
        self.base.target_pose.pose.orientation.y = BASE_POSE[1][1]  # Orientación y
        self.base.target_pose.pose.orientation.z = BASE_POSE[1][2]  # Orientación z
        self.base.target_pose.pose.orientation.w = BASE_POSE[1][3]  # Parte escalar w del cuaternión
        
if __name__ == '__main__':
    
    rospy.init_node("escondite")

    # Creamos la máquina de estados
    sm = StateMachine(outcomes=['end']) # La máquina tendrá un estado de finalización "end"

    # Añadimos los estados necesarios a la máquina de estados
    with sm:
        # Estado GetReadyToStart:
        StateMachine.add('GetReadyToStart', GetReadyToStart(),
            transitions={'ready_to_start':'WanderAndSearch'})
        
        # Estado WanderAndSearch:
        StateMachine.add('WanderAndSearch', WanderAndSearch(),
            transitions={'object_detected':'ReturnToBase'})
        
        # Estado ReturnToBase:
        StateMachine.add('ReturnToBase', ReturnToBase(), 
            transitions={'keep_finding':'WanderAndSearch',
                         'game_end':'end'})
              
    # Iniciamos el servidor de introspección para poder visualizar y depurar la máquina de estados
    sis = smach_ros.IntrospectionServer('server_name', sm, '/SM_ROOT')
    sis.start()

    # Ejecutamos la máquina de estados
    sm.execute()
    rospy.spin()