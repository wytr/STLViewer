import sys
from PyQt5 import QtWidgets, QtCore, QtGui
import stack
import pyqtgraph as pgt
from random import uniform, normalvariate
import random

class ExampleApp(QtWidgets.QMainWindow, stack.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.graphicsView.getAxis('left').setLabel('Data Value', color='#0000ff')
        self.graphicsView.getAxis('bottom').setLabel('time', 's')
        self.graphicsView.showGrid(x=True, y=True)
        self.graphicsView.setYRange(0,10)
        self.graphicsView.addLine(y=5,pen=pgt.mkPen('y'))
        self.graphicsView.addLine(y=7,pen=pgt.mkPen('r'))
        self.curve = self.graphicsView.plot()
        self.L = []
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateplot)
        self.timer.start(500)

    def getdata(self):
        frequency = 0.5
        noise = random.normalvariate(0., 1.)
        new = 10.*math.sin(time.time()*frequency*2*math.pi) + noise
        return new

    def updateplot(self):
        val = round(uniform(0,10), 2)
        self.L.append(val)
        self.curve.setData(self.L)
        #QtGui.QGuiApplication.processEvents()


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = ExampleApp()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()