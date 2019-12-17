#
# from collections import deque
# from math import ceil
# from numpy import interp, linspace, minimum
# from PySide2 import QtCore, QtWidgets
# import pyqtgraph as pg
# import queue
#
#
# def DrummerAnimateRun(inputQueue):
#     app = QtWidgets.QApplication([])
#     # app.setAttribute(QtCore.Qt.AA_Use96Dpi)
#
#     pg.setConfigOptions(antialias=False)  # True seems to work as well
#     pg.setConfigOption('background', 'w')
#     pg.setConfigOption('foreground', 'k')
#
#     win = DrummerAnimate(inputQueue)
#     win.show()
#     win.resize(800, 600)
#     win.raise_()
#     app.exec_()
#
#
# class DrummerAnimate(pg.GraphicsWindow):
#
#     def __init__(self, inputQueue, parent=None):
#         super().__init__(parent=parent)
#
#         # Setup process safe queue
#         self.inputQueue = inputQueue
#
#         # GPU rendering
#         self.useOpenGL(True)
#
#         # Setup GUI
#         self.timer = QtCore.QTimer(self)
#         self.timer.setTimerType(QtCore.Qt.PreciseTimer)
#         self.timer.setInterval(100)  # in milliseconds
#         self.timer.start()
#         self.timer.timeout.connect(self.frames)
#
#         # Axes
#         self.intensity_ax = self.addPlot(row=0, col=2, rowspan=3, title='Intensity')
#         self.complexity_ax = self.addPlot(row=3, col=2, rowspan=3, title='Complexity')
#         self.sudden_shift_ax = self.addPlot(row=0, col=0, title='Sudden shift')
#         self.average_velocity_ax = self.addPlot(row=1, col=0, title='Average Velocity')
#         self.hype_ax = self.addPlot(row=2, col=0, title='Crescendo')
#         self.high_density_ax = self.addPlot(row=3, col=0, title='High Register Density')
#         self.low_density_ax = self.addPlot(row=4, col=0, title='Low Register Density')
#         self.pedal_ax = self.addPlot(row=5, col=0, title='Pedal')
#
#         #Colors
#         # b = (31, 119, 180)
#         # g = (44, 160, 44)
#         # r = (214, 39, 40)
#         # c = (23, 190, 207)
#         # m = (227, 119, 194)
#         # y = (188, 189, 34)
#
#         # Intensity
#         self.intensity_ax.setXRange(0, 127)
#         self.intensity_ax.setYRange(0, 1.2)
#
#         self.x_space = linspace(0, 127, 127*2)
#
#         self.Low = interp(self.x_space, [0, 0, 25.4], [1, 1, 0])
#         self.Mid_Low = interp(self.x_space, [0, 25.4, 50.8], [0, 1, 0])
#         self.Middle = interp(self.x_space, [25.4, 50.8, 76.19999999999999], [0, 1, 0])
#         self.Mid_High = interp(self.x_space, [50.79999999999999, 76.19999999999999, 101.6], [0, 1, 0])
#         self.High = interp(self.x_space, [76.19999999999999, 101.6, 127], [0, 1, 0])
#         self.Max = interp(self.x_space, [101.6, 127.0, 127], [0, 1, 1])
#         self.intensity_ax.plot(x=self.x_space, y=self.Low, pen=(31, 119, 180), name='Low')
#         self.intensity_ax.plot(x=self.x_space, y=self.Mid_Low, pen=(44, 160, 44), name='Mid-Low')
#         self.intensity_ax.plot(x=self.x_space, y=self.Middle, pen=(214, 39, 40), name='Middle')
#         self.intensity_ax.plot(x=self.x_space, y=self.Mid_High, pen=(23, 190, 207), name='Mid-High')
#         self.intensity_ax.plot(x=self.x_space, y=self.High, pen=(227, 119, 194), name='High')
#         self.intensity_ax.plot(x=self.x_space, y=self.Max, pen=(188, 189, 34), name='Max')
#
#         self.intensity_low = self.intensity_ax.plot(x=[], y=[], fillLevel=0, fillBrush=(31, 119, 180, 127))
#         self.intensity_mid_low = self.intensity_ax.plot(x=[], y=[], fillLevel=0, fillBrush=(44, 160, 44, 127))
#         self.intensity_middle = self.intensity_ax.plot(x=[], y=[], fillLevel=0, fillBrush=(214, 39, 40, 127))
#         self.intensity_mid_high = self.intensity_ax.plot(x=[], y=[], fillLevel=0, fillBrush=(23, 190, 207, 127))
#         self.intensity_high = self.intensity_ax.plot(x=[], y=[], fillLevel=0, fillBrush=(227, 119, 194, 127))
#         self.intensity_max = self.intensity_ax.plot(x=[], y=[], fillLevel=0, fillBrush=(188, 189, 34, 127))
#         self.intensity_line = self.intensity_ax.plot(x=[], y=[], pen=(0, 0, 0))
#
#         # Complexity
#         self.complexity_ax.setXRange(0, 127)
#         self.complexity_ax.setYRange(0, 1.2)
#
#         self.complexity_ax.plot(x=self.x_space, y=self.Low, pen=(31, 119, 180), name='Low')
#         self.complexity_ax.plot(x=self.x_space, y=self.Mid_Low, pen=(44, 160, 44), name='Mid-Low')
#         self.complexity_ax.plot(x=self.x_space, y=self.Middle, pen=(214, 39, 40), name='Middle')
#         self.complexity_ax.plot(x=self.x_space, y=self.Mid_High, pen=(23, 190, 207), name='Mid-High')
#         self.complexity_ax.plot(x=self.x_space, y=self.High, pen=(227, 119, 194), name='High')
#         self.complexity_ax.plot(x=self.x_space, y=self.Max, pen=(188, 189, 34), name='Max')
#
#         self.complexity_low = self.complexity_ax.plot(x=[], y=[], fillLevel=0, fillBrush=(31, 119, 180, 127))
#         self.complexity_mid_low = self.complexity_ax.plot(x=[], y=[], fillLevel=0, fillBrush=(44, 160, 44, 127))
#         self.complexity_middle = self.complexity_ax.plot(x=[], y=[], fillLevel=0, fillBrush=(214, 39, 40, 127))
#         self.complexity_mid_high = self.complexity_ax.plot(x=[], y=[], fillLevel=0, fillBrush=(23, 190, 207, 127))
#         self.complexity_high = self.complexity_ax.plot(x=[], y=[], fillLevel=0, fillBrush=(227, 119, 194, 127))
#         self.complexity_max = self.complexity_ax.plot(x=[], y=[], fillLevel=0, fillBrush=(188, 189, 34, 127))
#         self.complexity_line = self.complexity_ax.plot(x=[], y=[], pen=(0, 0, 0))
#
#         # Shared time data
#         self.time_x = deque(maxlen=(ceil(5/0.01)))
#
#         # Intensity sudden shift
#         self.sudden_shift_ax.setXRange(0, 5)
#         self.sudden_shift_ax.setYRange(-1, 1)
#         self.shift_data = deque(maxlen=(ceil(5/0.01)))
#         self.sudden_shift_line = self.sudden_shift_ax.plot(x=[], y=[], pen=pg.mkPen((0, 0, 0), width=1.5))
#
#         # Average Velocity
#         self.average_velocity_ax.setXRange(0, 5)
#         self.average_velocity_ax.setYRange(0, 127)
#         self.avgvel_data = deque(maxlen=(ceil(5 / 0.01)))
#         self.average_velocity_line = self.average_velocity_ax.plot(x=[], y=[], pen=pg.mkPen((0, 0, 0), width=1.5))
#
#         # Hype
#         self.hype_ax.setXRange(0, 5)
#         self.hype_ax.setYRange(0, 1)
#         self.hype_data = deque(maxlen=(ceil(5 / 0.01)))
#         self.hype_line = self.hype_ax.plot(x=[], y=[], pen=pg.mkPen((0, 0, 0), width=1.5))
#
#         # Pedal
#         self.pedal_ax.setXRange(0, 5)
#         self.pedal_ax.setYRange(0, 1)
#         self.pedal_ax.getViewBox().invertY(True)
#         self.pedal_data = deque(maxlen=(ceil(5 / 0.01)))
#         self.pedal_line = self.pedal_ax.plot(x=[], y=[], pen=pg.mkPen((0, 0, 0), width=1.5))
#
#         # Low density
#         self.low_density_ax.setXRange(0, 5)
#         self.low_density_ax.setYRange(0, 127)
#         self.lowdensity_data = deque(maxlen=(ceil(5 / 0.01)))
#         self.low_density_line = self.low_density_ax.plot(x=[], y=[], pen=pg.mkPen((0, 0, 0), width=1.5))
#
#         # High density
#         self.high_density_ax.setXRange(0, 5)
#         self.high_density_ax.setYRange(0, 127)
#         self.highdensity_data = deque(maxlen=(ceil(5 / 0.01)))
#         self.high_density_line = self.high_density_ax.plot(x=[], y=[], pen=pg.mkPen((0, 0, 0), width=1.5))
#
#     def frames(self):
#         try:
#             data = self.inputQueue.get(block=True, timeout=1)
#             self.animate(data)
#         except queue.Empty:
#             exit(0)
#
#     def animate(self, data):
#
#         Low_y = data['Consequents']['Intensity']['Low']
#         Mid_Low_y = data['Consequents']['Intensity']['Mid-Low']
#         Middle_y = data['Consequents']['Intensity']['Middle']
#         Mid_High_y = data['Consequents']['Intensity']['Mid-High']
#         High_y = data['Consequents']['Intensity']['High']
#         Max_y = data['Consequents']['Intensity']['Max']
#         Intensity_x = data['Result']['Intensity']
#         self.intensity_low.setData(x=self.x_space, y=minimum(self.Low, Low_y))
#         self.intensity_mid_low.setData(x=self.x_space, y=minimum(self.Mid_Low, Mid_Low_y))
#         self.intensity_middle.setData(x=self.x_space, y=minimum(self.Middle, Middle_y))
#         self.intensity_mid_high.setData(x=self.x_space, y=minimum(self.Mid_High, Mid_High_y))
#         self.intensity_high.setData(x=self.x_space, y=minimum(self.High, High_y))
#         self.intensity_max.setData(x=self.x_space, y=minimum(self.Max, Max_y))
#         self.intensity_line.setData(x=[Intensity_x, Intensity_x], y=[0, 1])
#
#         Low_y = data['Consequents']['Complexity']['Low']
#         Mid_Low_y = data['Consequents']['Complexity']['Mid-Low']
#         Middle_y = data['Consequents']['Complexity']['Middle']
#         Mid_High_y = data['Consequents']['Complexity']['Mid-High']
#         High_y = data['Consequents']['Complexity']['High']
#         Max_y = data['Consequents']['Complexity']['Max']
#         Complexity_x = data['Result']['Complexity']
#         self.complexity_low.setData(x=self.x_space, y=minimum(self.Low, Low_y))
#         self.complexity_mid_low.setData(x=self.x_space, y=minimum(self.Mid_Low, Mid_Low_y))
#         self.complexity_middle.setData(x=self.x_space, y=minimum(self.Middle, Middle_y))
#         self.complexity_mid_high.setData(x=self.x_space, y=minimum(self.Mid_High, Mid_High_y))
#         self.complexity_high.setData(x=self.x_space, y=minimum(self.High, High_y))
#         self.complexity_max.setData(x=self.x_space, y=minimum(self.Max, Max_y))
#         self.complexity_line.setData(x=[Complexity_x, Complexity_x], y=[0, 1])
#
#         time = data['Info']['Absolute Time in song']
#         self.time_x.append(time)
#
#         if data['Info']['Time Since Shift Up'] < 1:
#             self.shift_data.append((1 - data['Info']['Time Since Shift Up']))
#         elif data['Info']['Time Since Shift Down'] < 1:
#             self.shift_data.append((0 - 1 + data['Info']['Time Since Shift Down']))
#         else:
#             self.shift_data.append(0)
#         self.sudden_shift_line.setData(x=list(self.time_x), y=list(self.shift_data))
#
#         self.avgvel_data.append(data['Info']['Average Velocity'])
#         self.average_velocity_line.setData(x=list(self.time_x), y=list(self.avgvel_data))
#
#         self.hype_data.append(data['Info']['Hype'])
#         self.hype_line.setData(x=list(self.time_x), y=list(self.hype_data))
#
#         self.pedal_data.append(data['Info']['Pedal'])
#         self.pedal_line.setData(x=list(self.time_x), y=list(self.pedal_data))
#
#         self.lowdensity_data.append(data['Info']['Low Average Density'])
#         self.low_density_line.setData(x=list(self.time_x), y=list(self.lowdensity_data))
#
#         self.highdensity_data.append(data['Info']['High Average Density'])
#         self.high_density_line.setData(x=list(self.time_x), y=list(self.highdensity_data))
#
#         if time >= 5 - 1:
#             self.average_velocity_ax.setXRange(time - 5 + 1, time + 1)
#             self.sudden_shift_ax.setXRange(time - 5+1, time+1)
#             self.pedal_ax.setXRange(time - 5+1, time+1)
#             self.low_density_ax.setXRange(time - 5 + 1, time + 1)
#             self.high_density_ax.setXRange(time - 5 + 1, time + 1)
#             self.hype_ax.setXRange(time - 5 + 1, time + 1)