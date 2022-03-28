from random import randint
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import serial
import math
import json
from OpenGL.GL import *
from OpenGL.GL import shaders

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *  

import numpy as np
from stl import mesh

from pathlib import Path

ser = serial.Serial('COM4')
ser.baudrate = 115200

class MyWindow(QMainWindow):

    def __init__(self):
        super(MyWindow, self).__init__()
        self.setGeometry(0, 0, 700, 900) 
        self.setAcceptDrops(True)
        
        self.initUI()
        
        self.currentSTL = None
        self.lastDir = None
        
        self.droppedFilename = None
    
    def initUI(self):
        centerWidget = QWidget()
        self.setCentralWidget(centerWidget)
        
        layout = QVBoxLayout()
        centerWidget.setLayout(layout)
        
        self.viewer = gl.GLViewWidget()
        layout.addWidget(self.viewer, 1)

        self.gx = gl.GLGridItem()
        self.gx.setSize(200, 200)
        self.gx.setSpacing(10, 10)
        self.gx.rotate(90, 0, 1, 0)
        self.gx.translate(-100, 0, 0)
        self.gx.color()

        self.gy = gl.GLGridItem()
        self.gy.setSize(200, 200)
        self.gy.setSpacing(10, 10)
        self.gy.rotate(90, 1, 0, 0)
        self.gy.translate(0, -100, 0)

        self.gz = gl.GLGridItem()
        self.gz.setSize(200, 200)
        self.gz.setSpacing(10, 10)
        self.gz.translate(0, 0, -100)

        self.viewer.addItem(self.gx)
        self.viewer.addItem(self.gy)
        self.viewer.addItem(self.gz)
        
        self.pitch = 0
        self.roll = 0

        btn = QPushButton(text="Load STL")
        btn.clicked.connect(self.showDialog)
        btn.clicked.connect(self.clicked)
        btn.setFont(QFont("Ricty Diminished", 14))
        layout.addWidget(btn)

        self.graphWidget = pg.PlotWidget()
        self.graphWidget.setYRange(-180, 180)
        p1 = self.graphWidget.getPlotItem()
        p1.hideAxis('bottom')

        pen_x = pg.mkPen(color=(255, 0, 0), width=2)
        pen_y = pg.mkPen(color=(0, 255, 0), width=2)
        #pen_z = pg.mkPen(color=(0, 0, 255), width=2)

        layout.addWidget(self.graphWidget)

        self.pitch_plot_values = [0 for _ in range(100)] # 100 data points
        self.roll_plot_values = [0 for _ in range(100)] # 100 data points

        self.xAxis = list(range(len(self.pitch_plot_values)))  # 100 time points

        self.xAccel_data_line = self.graphWidget.plot(
            self.xAxis, self.pitch_plot_values, pen=pen_x)

        self.yAccel_data_line = self.graphWidget.plot(
            self.xAxis, self.roll_plot_values, pen=pen_y)
            
        self.viewer.setWindowTitle('STL Accelerometer Viewer')
        self.viewer.setCameraPosition(distance=40)
        
        """
        self.slider_x = QSlider(Qt.Horizontal)
        self.slider_x.setMinimum(-180)
        self.slider_x.setMaximum(180)
        self.slider_x.setValue(0)
        self.slider_x.setTickPosition(QSlider.TicksBelow)
        self.slider_x.setTickInterval(1)
        layout.addWidget(self.slider_x)

        self.slider_y = QSlider(Qt.Horizontal)
        self.slider_y.setMinimum(-180)
        self.slider_y.setMaximum(180)
        self.slider_y.setValue(0)
        self.slider_y.setTickPosition(QSlider.TicksBelow)
        self.slider_y.setTickInterval(1)
        layout.addWidget(self.slider_y)

        self.slider_z = QSlider(Qt.Horizontal)
        self.slider_z.setMinimum(-180)
        self.slider_z.setMaximum(180)
        self.slider_z.setValue(0)
        self.slider_z.setTickPosition(QSlider.TicksBelow)
        self.slider_z.setTickInterval(1)
        layout.addWidget(self.slider_z)
        """
        self.timer = QtCore.QTimer()
        self.time = QtCore.QTime(0, 0, 0)
        self.timer.timeout.connect(self.timerEvent)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start(10)

    def update_plot_data(self):

        #send '.' to get response (jsonobject)
        message = '.'
        messate_bytes = message.encode()
        ser.write(messate_bytes)
        response =  ser.readline()
        decoded_bytes = response[0:len(response)-2].decode("utf-8")
        jsonObject = json.loads(decoded_bytes)
        print(decoded_bytes)
        """
        self.pitch = self.calc_angle(
            jsonObject["x-accel"], jsonObject["y-accel"], jsonObject["z-accel"], True)
        self.roll = self.calc_angle(
            jsonObject["x-accel"], jsonObject["y-accel"], jsonObject["z-accel"], False)
        """
        self.pitch = jsonObject["pitch"]
        self.roll = jsonObject["roll"]
        

        #this prevents catching the following exceptions should maybe be solved und mcu side.. dunno if possible
        if self.pitch and self.roll is not None:
            self.pitch_plot_values = self.pitch_plot_values[1:]
            self.roll_plot_values = self.roll_plot_values[1:]

            if self.pitch > 45 or self.roll > 45 or self.pitch < -45 or self.roll < -45:
                self.gx.setColor((120, 0, 0))
                self.gy.setColor((120, 0, 0))
                self.gz.setColor((120, 0, 0))
            else:
                self.gx.setColor((100, 100, 100))
                self.gy.setColor((100, 100, 100))
                self.gz.setColor((100, 100, 100))
            
            #lowpassfilered (TODO: Add checkbox in gui to enable lowpassfiltering)
            self.pitch_plot_values.append(0.80 *self.pitch_plot_values[-1] + 0.20 * self.pitch)
            self.roll_plot_values.append(0.80 *self.roll_plot_values[-1] + 0.20 * self.roll)
            try:
                self.xAccel_data_line.setData(self.xAxis, self.pitch_plot_values)
                self.yAccel_data_line.setData(self.xAxis, self.roll_plot_values)
            except:
                print("Error - MCU sendin NULL --> needs further investigation1")
                
            try:
                if self.currentSTL:
                    self.currentSTL.resetTransform()

                    #lowpassfilered
                    self.currentSTL.rotate(0.95 *self.pitch_plot_values[-1] + 0.05 * self.pitch,1,0,0)
                    self.currentSTL.rotate(0.95 *self.roll_plot_values[-1] + 0.05 * self.roll,0,1,0)
                    #self.currentSTL.rotate(self.pitch,1,0,0)
                    #self.currentSTL.rotate(self.roll,0,1,0)
                    #self.currentSTL.rotate(0,0,0,1)
            
            except:
                print("Error - MCU sendin NULL --> needs further investigation2")

    def calc_angle(self, x, y, z, pitch):
        # else return roll
        if pitch:
            return math.atan(x/(math.sqrt(z*z+y*y)))*180/math.pi
        else:
            return math.atan(y/(math.sqrt(z*z+x*x)))*180/math.pi

    def timerEvent(self):
        self.time = self.time.addSecs(1)
        """
        if self.currentSTL:
            self.currentSTL.resetTransform()
            self.currentSTL.rotate(self.slider_x.value(),1,0,0)
            self.currentSTL.rotate(self.slider_y.value(),0,1,0)
            self.currentSTL.rotate(self.slider_z.value(),0,0,1)
        """
        print(self.time.toString("hh:mm:ss"))

    def clicked(self):
        if self.currentSTL:
            self.currentSTL.rotate(1,1,0,0)
        print("clicked")

    def showDialog(self):
        directory = Path("")
        if self.lastDir:
            directory = self.lastDir
        fname = QFileDialog.getOpenFileName(self, "Open file", str(directory), "STL (*.stl)")
        if fname[0]:
            self.showSTL(fname[0])
            self.lastDir = Path(fname[0]).parent
            
    def showSTL(self, filename):
        if self.currentSTL:
            self.viewer.removeItem(self.currentSTL)

        points, faces = self.loadSTL(filename)
        meshdata = gl.MeshData(vertexes=points, faces=faces)
        mesh = gl.GLMeshItem(meshdata=meshdata, smooth=True, drawFaces=False, drawEdges=True, edgeColor=(0, 1, 0, 1))
        #mesh.setShader()
        self.viewer.addItem(mesh)
        
        self.currentSTL = mesh
        #self.currentSTL.rotate(20,1,0,0)

    def loadSTL(self, filename):


        m = mesh.Mesh.from_file(filename)
        shape = m.points.shape
        points = m.points.reshape(-1, 3)
        faces = np.arange(points.shape[0]).reshape(-1, 3)
        return points, faces

    def dragEnterEvent(self, e):
        print("enter")
        mimeData = e.mimeData()
        mimeList = mimeData.formats()
        filename = None
        
        if "text/uri-list" in mimeList:
            filename = mimeData.data("text/uri-list")
            filename = str(filename, encoding="utf-8")
            filename = filename.replace("file:///", "").replace("\r\n", "").replace("%20", " ")
            filename = Path(filename)
            
        if filename.exists() and filename.suffix == ".stl":
            e.accept()
            self.droppedFilename = filename
        else:
            e.ignore()
            self.droppedFilename = None
        
    def dropEvent(self, e):
        if self.droppedFilename:
            self.showSTL(self.droppedFilename)


if __name__ == '__main__':
    app = QtGui.QApplication([])
    window = MyWindow()
    window.show()
    app.exec_()