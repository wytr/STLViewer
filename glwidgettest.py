import sys
import time as pytime

import numpy as np
import freetype
#import glm

from OpenGL.GLU import *
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader

from TextureLoader import load_texture
from PyQt5 import QtGui
from PyQt5.QtOpenGL import *
from PyQt5 import QtCore, QtWidgets, QtOpenGL
import pyrr
from ObjLoader import ObjLoader
from camera import Camera

timeNow = 0
timeNowTwo = 0

fontfile = "Vera.ttf"


class Ui_MainWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(Ui_MainWindow, self).__init__()
        self.openGlWidget = glWidget()
        self.setWindowTitle("openGL")
        self.button = QtWidgets.QPushButton('Test', self)
        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.addWidget(self.openGlWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        #self.mainLayout.addWidget(self.button)
        self.setLayout(self.mainLayout)

        #self.framecounter = QtWidgets.QLabel(self.openGlWidget)
        #self.framecounter.setText("9999")
        #self.framecounter.setFont(QtGui.QFont('Arial', 20))
        #self.framecounter.setStyleSheet("background-color: red")

        #self.openGlWidget.my_signal.connect(self.updateFramecounter)

    def updateFramecounter(self, fps):
        self.framecounter.setText(str(fps))

    def keyPressEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key.Key_Escape:
            self.close()
        elif key == QtCore.Qt.Key.Key_W:
            self.openGlWidget.forward = True
        elif key == QtCore.Qt.Key.Key_A:
            self.openGlWidget.left = True
        elif key == QtCore.Qt.Key.Key_S:
            self.openGlWidget.backward = True
        elif key == QtCore.Qt.Key.Key_D:
            self.openGlWidget.right = True
        elif key == QtCore.Qt.Key.Key_PageUp:
            self.openGlWidget.up = True
        elif key == QtCore.Qt.Key.Key_PageDown:
            self.openGlWidget.down = True

    def keyReleaseEvent(self, event):
        key = event.key()

        if key == QtCore.Qt.Key.Key_W and not event.isAutoRepeat():
            # print('W RELEASED')
            self.openGlWidget.forward = False

        elif key == QtCore.Qt.Key.Key_A and not event.isAutoRepeat():
            # print('A RELEASED')
            self.openGlWidget.left = False

        elif key == QtCore.Qt.Key.Key_S and not event.isAutoRepeat():
            # print('S RELEASED')
            self.openGlWidget.backward = False

        elif key == QtCore.Qt.Key.Key_D and not event.isAutoRepeat():
            # print('D RELEASED')
            self.openGlWidget.right = False

        elif key == QtCore.Qt.Key.Key_PageUp and not event.isAutoRepeat():
            # print('S RELEASED')
            self.openGlWidget.up = False

        elif key == QtCore.Qt.Key.Key_PageDown and not event.isAutoRepeat():
            # print('D RELEASED')
            self.openGlWidget.down = False

class glWidget(QGLWidget):

    my_signal = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        self.initdone = False
        self.vertex_src = """
        # version 330

        layout(location = 0) in vec3 a_position;
        layout(location = 1) in vec2 a_texture;
        layout(location = 2) in vec3 a_normal;

        uniform mat4 model;
        uniform mat4 projection;
        uniform mat4 view;

        out vec2 v_texture;

        void main()
        {
            gl_Position = projection * view * model * vec4(a_position, 1.0);
            v_texture = a_texture;
        }
        """

        self.fragment_src = """
        # version 330

        in vec2 v_texture;

        out vec4 out_color;

        uniform sampler2D s_texture;

        void main()
        {
            out_color = texture(s_texture, v_texture);
        }
        """

        self.first_mouse = True
        self.width, self.height = 1200, 400
        QGLWidget.__init__(self, parent)
        self.setMinimumSize(self.width, self.height)
        self.setCursor(QtCore.Qt.CursorShape.CrossCursor)
        self.setMouseTracking(False)
        self.cube_indices, self.cube_buffer = ObjLoader.load_model(
            "meshes/zaehler1.obj")
        self.monkey_indices, self.monkey_buffer = ObjLoader.load_model(
            "meshes/monkey.obj")
        self.floor_indices, self.floor_buffer = ObjLoader.load_model(
            "meshes/floor.obj")

        self.frames = 0
        self.fpscap = 60
        self.deltaFrameTime = 1/self.fpscap
        self.textures = None
        self.useFrameCap = True
        self.shader = None

        self.VAO = None
        self.VBO = None

        self.projection = None
        self.cube_pos = None
        self.monkey_pos = None
        self.floor_pos = None

        self.model_loc = None
        self.proj_loc = None
        self.view_loc = None

        self.timer = QtCore.QTimer()
        self.time = QtCore.QTime(0, 0, 0)
        self.timer.timeout.connect(self.paintGL)
        self.timer.start(1)
        self.leaveEvent = lambda event: self.set_first_mouse(True)

        self.cam = Camera()

        self.lastX, self.lastY = self.width / 2, self.height / 2
        self.first_mouse = True
        self.up, self.down, self.left, self.right, self.forward, self.backward = False, False, False, False, False, False

    def set_first_mouse(self, b):
        self.first_mouse = b

    def do_movement(self):
        if self.left:
            self.cam.process_keyboard("LEFT", 0.01)
        if self.right:
            self.cam.process_keyboard("RIGHT", 0.01)
        if self.forward:
            self.cam.process_keyboard("FORWARD", 0.01)
        if self.backward:
            self.cam.process_keyboard("BACKWARD", 0.01)
        if self.up:
            self.cam.process_keyboard("UP", 0.01)
        if self.down:
            self.cam.process_keyboard("DOWN", 0.01)

    def refreshViewport(self):
        if self.initdone:
            glViewport(0, 0, self.width, self.height)
            projection = pyrr.matrix44.create_perspective_projection_matrix(
                45, self.width / self.height, 0.1, 100)
            glUniformMatrix4fv(self.proj_loc, 1, GL_FALSE, projection)

    def resizeEvent(self, event):

        QtWidgets.QWidget.resizeEvent(self, event)
        self.width = self.frameGeometry().width()
        self.height = self.frameGeometry().height()
        self.refreshViewport()

    def mouseMoveEvent(self, event):

        xpos = event.x()
        ypos = event.y()

        global first_mouse, lastX, lastY
        if self.first_mouse:
            lastX = xpos
            lastY = ypos
            self.first_mouse = False

        xoffset = xpos - lastX
        yoffset = lastY - ypos

        lastX = xpos
        lastY = ypos

        self.cam.process_mouse_movement(xoffset, yoffset)

    def paintGL(self):

        global timeNow
        global timeNowTwo
        # TODO: implement framecounter rendering in opengl with  (best performance option)
        self.do_movement()
        if self.initdone:

            if(pytime.time() >= timeNow + 0.5):
                timeNow += 0.5
                # print(self.frames * 2)
                self.my_signal.emit(self.frames * 2)
                self.frames = 0

            if self.useFrameCap == True:

                if(pytime.time() >= timeNowTwo + self.deltaFrameTime):
                    timeNowTwo += self.deltaFrameTime

                    self.glStuff()
            else:
                self.glStuff()

        #TODO: Mutlithreading

    def glStuff(self):
        self.time = self.time.addMSecs(1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        view = self.cam.get_view_matrix()

        glUniformMatrix4fv(self.view_loc, 1, GL_FALSE, view)

        time = float(self.time.toString("s.zzz"))
        #rot_y = pyrr.Matrix44.from_y_rotation(0.8 * time)
        rot_y = pyrr.Matrix44.from_y_rotation(0)
        model = pyrr.matrix44.multiply(rot_y, self.cube_pos)
        floor_rot = pyrr.Matrix44.from_x_rotation(0.314)
        model_2 = pyrr.matrix44.multiply(floor_rot, self.floor_pos)

        # draw the cube
        glBindVertexArray(self.VAO[0])
        glBindTexture(GL_TEXTURE_2D, self.textures[0])
        glUniformMatrix4fv(self.model_loc, 1, GL_FALSE, model)
        glDrawArrays(GL_TRIANGLES, 0, len(self.cube_indices))
        """
        # draw the monkey
        glBindVertexArray(self.VAO[1])
        glBindTexture(GL_TEXTURE_2D, self.textures[1])
        glUniformMatrix4fv(self.model_loc, 1,GL_FALSE, self.monkey_pos)
        glDrawArrays(GL_TRIANGLES, 0, len(self.monkey_indices))
        # draw the floor
        glBindVertexArray(self.VAO[2])
        glBindTexture(GL_TEXTURE_2D, self.textures[2])
        glUniformMatrix4fv(self.model_loc, 1,GL_FALSE, model_e2)
        glDrawArrays(GL_TRIANGLES, 0, len(self.floor_indices))
        """
        self.update()
        self.frames += 1
        
    def initializeGL(self):
        global initdone
        global vertex_src
        global fragment_src

        self.shader = compileProgram(compileShader(
            self.vertex_src, GL_VERTEX_SHADER), compileShader(self.fragment_src, GL_FRAGMENT_SHADER))

        self.textures = glGenTextures(3)
        load_texture("meshes/zaehler.png", self.textures[0])
        load_texture("meshes/monkey.jpg", self.textures[1])
        load_texture("meshes/floor2.jpg", self.textures[2])

        # VAO and VBO
        self.VAO = glGenVertexArrays(3)
        self.VBO = glGenBuffers(3)
        # cube VAO
        glBindVertexArray(self.VAO[0])
        # cube Vertex Buffer Object
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO[0])
        glBufferData(GL_ARRAY_BUFFER, self.cube_buffer.nbytes,
                     self.cube_buffer, GL_STATIC_DRAW)
        # cube vertices
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE,
                              self.cube_buffer.itemsize * 8, ctypes.c_void_p(0))
        # cube textures
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE,
                              self.cube_buffer.itemsize * 8, ctypes.c_void_p(12))
        # cube normals
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE,
                              self.cube_buffer.itemsize * 8, ctypes.c_void_p(20))
        glEnableVertexAttribArray(2)
        # monkey VAO
        glBindVertexArray(self.VAO[1])
        # monkey Vertex Buffer Object
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO[1])
        glBufferData(GL_ARRAY_BUFFER, self.monkey_buffer.nbytes,
                     self.monkey_buffer, GL_STATIC_DRAW)
        # monkey vertices
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE,
                              self.monkey_buffer.itemsize * 8, ctypes.c_void_p(0))
        # monkey textures
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(
            1, 2, GL_FLOAT, GL_FALSE, self.monkey_buffer.itemsize * 8, ctypes.c_void_p(12))
        # monkey normals
        glVertexAttribPointer(
            2, 3, GL_FLOAT, GL_FALSE, self.monkey_buffer.itemsize * 8, ctypes.c_void_p(20))
        glEnableVertexAttribArray(2)
        # floor VAO
        glBindVertexArray(self.VAO[2])
        # floor Vertex Buffer Object
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO[2])
        glBufferData(GL_ARRAY_BUFFER, self.floor_buffer.nbytes,
                     self.floor_buffer, GL_STATIC_DRAW)
        # floor vertices
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE,
                              self.floor_buffer.itemsize * 8, ctypes.c_void_p(0))
        # floor textures
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE,
                              self.floor_buffer.itemsize * 8, ctypes.c_void_p(12))
        # floor normals
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE,
                              self.floor_buffer.itemsize * 8, ctypes.c_void_p(20))
        glEnableVertexAttribArray(2)

        glUseProgram(self.shader)
        glClearColor(1.0, 1.0, 1.0, 1)
        glEnable(GL_DEPTH_TEST)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.projection = pyrr.matrix44.create_perspective_projection_matrix(
            120, self.width / self.height, 0.1, 1000)
        self.cube_pos = pyrr.matrix44.create_from_translation(
            pyrr.Vector3([0, 4, -2]))
        self.monkey_pos = pyrr.matrix44.create_from_translation(
            pyrr.Vector3([-4, 4, -4]))
        self.floor_pos = pyrr.matrix44.create_from_translation(
            pyrr.Vector3([0, 0, 0]))
        self.model_loc = glGetUniformLocation(self.shader, "model")
        self.proj_loc = glGetUniformLocation(self.shader, "projection")
        self.view_loc = glGetUniformLocation(self.shader, "view")
        glUniformMatrix4fv(self.proj_loc, 1, GL_FALSE, self.projection)
        self.initdone = True
        self.refreshViewport()
        global timeNow
        timeNow = pytime.time()
        global timeNowTwo
        timeNowTwo = timeNow


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QMainWindow()
    ui = Ui_MainWindow(Form)
    ui.show()
    sys.exit(app.exec_())
