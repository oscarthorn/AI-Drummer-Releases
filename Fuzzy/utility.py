class RunningLinearRegression:

    def __init__(self):
        self.meanX = 0
        self.meanY = 0
        self.varX = 0
        self.covXY = 0
        self.n = 0

    def update(self, x, y):
        self.n += 1
        dx = x - self.meanX
        dy = y - self.meanY
        self.varX += (((self.n - 1) / self.n) * dx * dx - self.varX) / self.n
        self.covXY += (((self.n - 1) / self.n) * dx * dy - self.covXY) / self.n
        self.meanX += dx / self.n
        self.meanY += dy / self.n

    def getSlope(self):
        return self.covXY / self.varX

    def reset(self, x_seed, y_seed):
        self.meanX = 0
        self.meanY = 0
        self.varX = 0
        self.covXY = 0
        self.n = 0
        self.update(x_seed, y_seed)
