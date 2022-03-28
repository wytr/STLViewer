from PyQt5 import QtWidgets, QtCore
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import os
from random import randint
import json
import serial
import math


ser = serial.Serial('COM4')
ser.baudrate = 115200
# ser.flushInput()


class MyStringAxis(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        pg.AxisItem.__init__(self, *args, **kwargs)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        ser.set_buffer_size(64)
        
        self.graphWidget = pg.PlotWidget()
        self.setGeometry(100, 60, 320, 240)
        self.setCentralWidget(self.graphWidget)
        # self.graphWidget.useOpenGL(True)
        self.graphWidget.setYRange(-90, 90)

        p1 = self.graphWidget.getPlotItem()
        p1.hideAxis('bottom')
        # self.graphWidget.
        self.pitch_val = [0 for _ in range(100)]
        self.roll_val = [0 for _ in range(100)]

        self.xAxis = list(range(len(self.pitch_val)))  # 100 time points
        # 100 data points

        self.graphWidget.setBackground('black')

        pen_x = pg.mkPen(color=(255, 0, 0), width=2)
        pen_y = pg.mkPen(color=(0, 255, 0), width=2)
        pen_z = pg.mkPen(color=(0, 0, 255), width=2)

        self.xAccel_data_line = self.graphWidget.plot(
            self.xAxis, self.pitch_val, pen=pen_x)

        self.yAccel_data_line = self.graphWidget.plot(
            self.xAxis, self.roll_val, pen=pen_y)

       # ... init continued ...
        self.timer = QtCore.QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

    def calc_angle(self, x, y, z, pitch):
        # else return roll
        if pitch:
            return math.atan(x/(math.sqrt(z*z+y*y)))*180/math.pi
        else:
            return math.atan(y/(math.sqrt(z*z+x*x)))*180/math.pi

    def update_plot_data(self):

        ser_bytes = ser.readline()

        decoded_bytes = ser_bytes[0:len(ser_bytes)-2].decode("utf-8")

        jsonObject = json.loads(decoded_bytes)

        self.xAxis = self.xAxis[1:]

        self.xAxis.append(self.xAxis[-1] + 1)

        self.pitch_val = self.pitch_val[1:]
        self.roll_val = self.roll_val[1:]

        self.pitch_val.append(self.calc_angle(
            jsonObject["x-accel"], jsonObject["y-accel"], jsonObject["z-accel"], True))
        self.roll_val.append(self.calc_angle(
            jsonObject["x-accel"], jsonObject["y-accel"], jsonObject["z-accel"], False))

        self.xAccel_data_line.setData(self.xAxis, self.pitch_val)
        self.yAccel_data_line.setData(self.xAxis, self.roll_val)

        print(f'{self.pitch_val[-1]} {self.roll_val[-1]}')


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
