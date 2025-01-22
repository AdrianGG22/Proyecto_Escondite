#!/usr/bin/env python

import rospy
import os
import subprocess
from actionlib_msgs.msg import GoalID
from std_msgs.msg import Bool


TOPIC_EXPLORE_STATE = "/explore_state"

def cancel_goal():
    
    # rospy.loginfo("Cancelando el objetivo actual de move_base...") # Se ha utilizado para depuración
    # Publicamos un mensaje en el topic /move_base/cancel para detener cualquier objetivo activo.
    cancel_pub = rospy.Publisher('/move_base/cancel', GoalID, queue_size=10)
    rospy.sleep(1)  # Espera para asegurarse de que el publicador esté activo
    cancel_pub.publish(GoalID())
    # rospy.loginfo("Objetivo cancelado.") # Se ha utilizado para depuración

def kill_explore_lite():
    
    # rospy.loginfo("Matando el nodo explore_lite...") # Se ha utilizado para depuración
    # Llamamos al comando rosnode kill para detener el nodo explore_lite.
    subprocess.run(["rosnode", "kill", "/explore"], check=True)
    # rospy.loginfo("Nodo explore_lite terminado.") # Se ha utilizado para depuración

if __name__ == "__main__":
    
    rospy.init_node('explore_lite_stop', anonymous=True)
    
    # Cancelamos el objetivo de move_base
    cancel_goal()
    
    # Finalizamos el nodo explore_lite
    kill_explore_lite()

    pub_ExploracionDetenida = rospy.Publisher(TOPIC_EXPLORE_STATE, Bool, queue_size=5)
    rospy.sleep(1)
    pub_ExploracionDetenida.publish(False)

    # rospy.loginfo("Exploración detenida completamente.") # Se ha utilizado para depuración
    rospy.sleep(1)

