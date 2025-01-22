# Proyecto_Escondite
Este repositorio ha sido creado por:
- Adrian Gea   
- Martin Cámara
- Daniel Burgos

<p align="justify">
Este paquete de ROS tiene el objetivo de realizar una tarea donde el robot tenga que buscar caras y objetos con colores distintos por todo el mapa. En este caso para la detección de caras se ha utilizado el modelo de visión por computadora YOLOv5, una versión de optimizada de YOLO con la capacidad de ejecutarse en tiempo real, y para la detección de colores se ha modelado una cámara en gazebo para el turtlebot 3 que le permitirá diferenciar los colores que estén dentro de cierto umbral.
</p>

Para este paquete se han utilizado las siguientes librerías:
- Turtlebot3:
  ```bash
  sudo apt install ros-noetic-dynamixel-sdk
  sudo apt install ros-noetic-turtlebot3-msgs
  sudo apt install ros-noetic-turtlebot3

- YOLOv5:<br>
  [Link a su repositorio](https://github.com/ultralytics/yolov5).

- ROS:
  ```bash
  sudo apt install ros-noetic-desktop-full
  sudo apt-get install ros-noetic-joy ros-noetic-teleop-twist-joy \
  ros-noetic-teleop-twist-keyboard ros-noetic-laser-proc \
  ros-noetic-rgbd-launch ros-noetic-rosserial-arduino \
  ros-noetic-rosserial-python ros-noetic-rosserial-client \
  ros-noetic-rosserial-msgs ros-noetic-amcl ros-noetic-map-server \
  ros-noetic-move-base ros-noetic-urdf ros-noetic-xacro \
  ros-noetic-compressed-image-transport ros-noetic-rqt* ros-noetic-rviz \
  ros-noetic-gmapping ros-noetic-navigation ros-noetic-interactive-markers
