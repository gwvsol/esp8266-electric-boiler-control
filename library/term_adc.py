from machine import ADC
import math


ADC_B = ADC(0)
BALANCE_R = 98500.0
THERMISTOR_R = 100000.0
A = 3.354016e-03
B = 2.460382e-04
C = 3.405377e-06
D = 1.034240e-07
K = 5.29


class READ_TERM():
    def __init__(self, adc=ADC_B, 
                       balance=BALANCE_R, 
                       termist=THERMISTOR_R, 
                       a=A, b=B, c=C, d=D, k=K):
        self.adc_max = 1023
        self._adc = adc
        self._bal = balance
        self._term = termist
        self._a = a
        self._b = b
        self._c = c
        self._d = d
        self._k = k
        self.kelv = 273.15


    def _adc_read(self):
        val =0
        n = 20
        for i in range(n):
            val += self._adc.read()
        val = val / n
        Rt = self._bal * (self.adc_max / val - 1)
        Tlog = math.log(Rt / self._term)
        return math.pow((self._a + self._b * Tlog + self._c * math.pow(Tlog, 2) + \
            self._d * math.pow(Tlog, 3)), -1) - self.kelv + self._k
            

    @property
    def value(self):
        return self._adc_read()
    
