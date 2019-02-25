import math

class READ_TERM():
    def __init__(self, adc, balance, termist, a, b, c, k, d=False):
        self.adc_max = 1023
        self._adc = adc
        self._bal = balance     # Балансный резистор в схеме (ом)
        self._term = termist    # Номинал терморезистора (ом)
        self._a = a     # Коеффициент А терморезистора
        self._b = b     # Коеффициент B терморезистора
        self._c = c     # Коеффициент C терморезистора
        self._d = d     # Коеффициент D терморезистора
        self._k = k     # Погрешность терморезистора %
        self.kelv = 273.15  # Температура в кельвинах, для перевода в градусы


    def _adc_read(self):
        val = 0
        n = 100 # считываний с датчика
        for i in range(n):
            val += self._adc.read()
        val = val / n # Среднее значение
        #Rt = self._bal * (self.adc_max / val - 1) # Вычисляем значение терморезистора, если терморезистор к плюсу питания
        Rt = self._bal / (self.adc_max / val - 1) # Вычисляем значение терморезистора, если терморезистор на землю
        if self._d: # Если используются все 4 коэффициента (для термисторов VISHAY www.vishay.com)
            Tlog = math.log(Rt / self._term)
            return math.pow((self._a + self._b * Tlog + self._c * math.pow(Tlog, 2) + \
                self._d * math.pow(Tlog, 3)), -1) - self.kelv + self._k
        else: # Если используется 3 коэффициента. Коеффициент D должен быть задан как False
            Tlog = math.log(Rt)
            return math.pow((self._a + self._b * Tlog + self._c * math.pow(Tlog, 3)), -1) - self.kelv + self._k

    @property
    def value(self):
        return self._adc_read()

