from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from OpenGL import GL as gl
from PyQt5.QtCore import Qt

class Widget(QOpenGLWidget):
    def initializeGL(self):
        gl.glClearColor(0.5, 0.8, 0.7, 1.0)
    def resizeGL(self, w, h):
        gl.glViewport(0, 0, w, h)
    def paintGL(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

def main():
    QApplication.setAttribute(Qt.AA_UseDesktopOpenGL)
    app = QApplication([])
    widget = Widget()
    widget.setWindowTitle("Minimal PyQt5 and OpenGL Example")
    widget.resize(400, 400)
    widget.show()
    app.exec_()

main()