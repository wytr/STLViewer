"""
Main application for uScope
"""

import sys
import time
import threading
from PyQt5 import QtCore, QtWidgets, QtOpenGL, QtGui
from OpenGL.GL import *
from OpenGL.GLU import *
import OpenGL

window_count = 0
# -------------------------------------------------------------------
#                           GL THREAD
# -------------------------------------------------------------------
#class GLThread(QtCore.QThread):  # Uncomment to use QThreads instead of python threads
class GLThread(threading.Thread):

    def __init__(self, glWidget, thread_id):
        #        QtCore.QThread.__init__(self)   # Uncomment to use QThreads instead of python threads
        threading.Thread.__init__(self)
        self.glw = glWidget
        self.doRendering = True
        self.doResize = False
        self.width = 512
        self.height = 512
        self.thread_id = thread_id
        print('Thread', thread_id, 'created.')

        self.last_render_time = time.time()
        self.fps_avg = 30.0
        self.rotAngle = 0.0

        # the background color
        self.backgroundColor = (0.0,.0,1.0,1.0)
        
    def resizeViewport(self, size):
        self.width = size.width()
        self.height = size.height()
        self.doResize = True

    def stop(self):
        self.doRendering = False

    # ---------------------- OPENGL DISPLAY CODE ----------------------
    def glDrawTriangle(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)		# Clear The Screen And The Depth Buffer
        glLoadIdentity()				# Reset The View

        glTranslatef(-1.5,0.0,-6.0)
  
        glRotatef(self.rotAngle,0.0,1.0,0.0)		# Rotate The Pyramid On The Y axis 

        # draw a pyramid (in smooth coloring mode)
        glBegin(GL_POLYGON)				# start drawing a pyramid

        # front face of pyramid
        glColor3f(1.0,0.0,0.0)			# Set The Color To Red
        glVertex3f(0.0, 1.0, 0.0)		        # Top of triangle (front)
        glColor3f(0.0,1.0,0.0)			# Set The Color To Green
        glVertex3f(-1.0,-1.0, 1.0)		# left of triangle (front)
        glColor3f(0.0,0.0,1.0)			# Set The Color To Blue
        glVertex3f(1.0,-1.0, 1.0)		        # right of traingle (front)	

        # right face of pyramid
        glColor3f(1.0,0.0,0.0)			# Red
        glVertex3f( 0.0, 1.0, 0.0)		# Top Of Triangle (Right)
        glColor3f(0.0,0.0,1.0)			# Blue
        glVertex3f( 1.0,-1.0, 1.0)		# Left Of Triangle (Right)
        glColor3f(0.0,1.0,0.0)			# Green
        glVertex3f( 1.0,-1.0, -1.0)		# Right Of Triangle (Right)

        # back face of pyramid
        glColor3f(1.0,0.0,0.0)			# Red
        glVertex3f( 0.0, 1.0, 0.0)		# Top Of Triangle (Back)
        glColor3f(0.0,1.0,0.0)			# Green
        glVertex3f( 1.0,-1.0, -1.0)		# Left Of Triangle (Back)
        glColor3f(0.0,0.0,1.0)			# Blue
        glVertex3f(-1.0,-1.0, -1.0)		# Right Of Triangle (Back)
        
        # left face of pyramid.
        glColor3f(1.0,0.0,0.0)			# Red
        glVertex3f( 0.0, 1.0, 0.0)		# Top Of Triangle (Left)
        glColor3f(0.0,0.0,1.0)			# Blue
        glVertex3f(-1.0,-1.0,-1.0)		# Left Of Triangle (Left)
        glColor3f(0.0,1.0,0.0)			# Green
        glVertex3f(-1.0,-1.0, 1.0)		# Right Of Triangle (Left)

        glEnd()					# Done Drawing The Pyramid

    # ---------------------- THREAD RUN LOOP ----------------------

    def run(self):
        time.sleep(1) # This sleep timer seems to be necessary to give
                        # the openGL system a second to initialize
                        # before we start rendering.  Without this the
                        # program crashes immediately.  Maybe this is
                        # a clue?

        # This was an attempt to create a new context per-thread.  I'm
        # fairly certain this is not necessary.
        #
        #        ctx = QtOpenGL.QGLContext(self.glw.format(), self.glw)
        #        success = ctx.create()
        #        if not success:
        #            print 'Error creating new context'
        #        self.glw.setContext(ctx)

        self.glw.makeCurrent()
        glClearColor(0.0, 0.0, 0.0, 0.0)		# This Will Clear The Background Color To Black
        glClearDepth(1.0)				# Enables Clearing Of The Depth Buffer
        glDepthFunc(GL_LESS)				# The Type Of Depth Test To Do
        glEnable(GL_DEPTH_TEST)			# Enables Depth Testing
        glShadeModel(GL_SMOOTH)			# Enables Smooth Color Shading

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()				# Reset The Projection Matrix
        gluPerspective(45.0,float(self.width)/float(self.height),0.1,100.0)	
        glMatrixMode(GL_MODELVIEW)

        while (self.doRendering):
            self.rotAngle = self.rotAngle + 3 # threads rotate pyramid at different rate!
            if (self.doResize):
                glViewport(0, 0, self.width, self.height)
                glMatrixMode(GL_PROJECTION)
                glLoadIdentity()
                gluPerspective(45.0,float(self.width)/float(self.height),0.1,100.0)
                glMatrixMode(GL_MODELVIEW)
                self.doResize = False

            # Rendering code goes here
            try:
                self.glDrawTriangle()
            except (OpenGL.error.GLError, e):
                print(e)
                sys.exit(0)
            self.glw.updateGL()
            time.sleep(1.0/30.0)

# ----------------------------------------------------------
#                     GL WIDGET
# ----------------------------------------------------------
class GLWidget(QtOpenGL.QGLWidget):

    def __init__(self,  window_id, parent=None):
        # Set up to sync with double-buffer, vertical refresh.  Add
        # Alpha and Depth buffers.  This should prevent frame tearing.
        QtOpenGL.QGLWidget.__init__(self, parent)

        self.gl_thread = GLThread(self, window_id)

        self.setAutoBufferSwap(True)
        self.resize(320, 240)
        self.doneCurrent()

    def __del__(self):
        self.stopRendering()

    # --------------------- EVENT HANDLING CODE ------------------

    def keyPressEvent(self, event):
        """
        Handle some shortcut keys
        """
        if event.key() == QtCore.Qt.Key_Escape:
            self.setVisible(False)

    def mouseDoubleClickEvent(self, event):
        """
        Handle some shortcut keys
        """
        if (self.isFullScreen()):
            self.showNormal()
        else:
            self.showFullScreen()

    def resizeEvent(self, event):
        self.gl_thread.resizeViewport(event.size())

    def paintEvent(self, event):
        pass
    
    def startRendering(self):
        self.gl_thread.start()

    def stopRendering(self):
        self.gl_thread.stop()
        self.gl_thread.wait()
        
    def closeEvent(self, event):
        self.stopRendering()

# ----------------------------------------

# Create the application

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        exitAction = QtWidgets.QAction("E&xit", self)
        exitAction.setShortcut("Ctrl+X")
        exitAction.setStatusTip("Exit the application")
        self.connect(exitAction, QtCore.SIGNAL('triggered()'), self.close)
            
        newThreadAction = QtWidgets.QAction("New Thread", self)
        newThreadAction.setShortcut("Ctrl+N")
        newThreadAction.setStatusTip("&New thread")
        self.connect(newThreadAction, QtCore.SIGNAL('triggered()'), self.newThread)
            
        killThreadAction = QtWidgets.QAction("Kill Thread", self)
        killThreadAction.setShortcut("Ctrl+K")
        killThreadAction.setStatusTip("&Kill thread")
        self.connect(killThreadAction, QtCore.SIGNAL('triggered()'), self.killThread)
            
        tMenu = self.menuBar().addMenu( "&Thread")
        tMenu.addAction( newThreadAction )
        tMenu.addAction( killThreadAction )
        tMenu.addSeparator()
        tMenu.addAction( exitAction )

        self.ws = QtWidgets.QWorkspace(self)
        self.setCentralWidget(self.ws)

    def closeEvent(self, evt):
        windows = self.ws.windowList()
        #        for i in range(0, int(windows.count())):
        #            window = self.windows.at(i)
        #            window.stopRendering()
        QtWidgets.QMainWindow.closeEvent(self, evt)

    def newThread(self):
        global window_count
        windows = self.ws.windowList()
        widget = GLWidget(str(window_count), self.ws)
        window_count += 1
        self.ws.addWindow(widget)
        widget.setWindowTitle("Thread")
        widget.show()
        widget.startRendering()
            
    def killThread(self):
        widget = self.ws.activeWindow()    
        if widget: 
            widget.stopRendering()
            del widget

# --------------------------------

app = QtWidgets.QApplication(sys.argv)

# Create the mainwindow
mainWindow = MainWindow()
mainWindow.show()

result = app.exec_()