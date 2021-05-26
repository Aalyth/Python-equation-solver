import re

# doing math stuff with objects of class unit
def unit_math(unit1, unit2, function):
    if unit1.suffix == unit2.suffix:
        return Unit(str(function(unit1.value(), unit2.value())) + unit1.get_suffix_str())
    else: 
        return None

class Symbol():
    def __init__(self, string):
        if re.search("\^\d+", string):
            self.power = int(re.findall(r"(?<=\^)\d+", string)[0])
        else:
            self.power = 1
        self.symbol = re.findall(r"([a-z])", string)[0]
    
    def __str__(self):
        if self.power == 1:
            return self.symbol
        return self.symbol + '^' + str(self.power)
    
    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.power == other.power and self.symbol == other.symbol

    def __add__(self, other):
        return str(self) + str(other)

    def __mul__(self, other):
        if type(other) == Symbol:
            if self.symbol == other.symbol:
                return Symbol(self.symbol + "^" + str(self.power + other.power))
            else:
                return None
        else:
            return None

class Unit():
    def __init__(self, string):
        if re.search(r'[a-z]', string):
            temp = re.findall(r'([a-z](\^\d+)?)', string)
            self.suffix = []
            for i in temp:
                self.suffix.append(Symbol(i[0]))
        else:
            self.suffix = ''
        self.prefix = re.sub(r'([a-z](\^\d+)?)', '', string)
        if re.search(r'[^\d\-\.]+', self.prefix):
            raise SyntaxError("Incorrect unit declaration")

    def __add__(self, other):
        if type(other) == Unit:
            return unit_math(self, other, lambda x,y: x + y)
        else:
            return f"{str(self)}+{str(other)}"

    def __sub__(self, other):
        if type(other) == Unit:
            return unit_math(self, other, lambda x,y: x - y)
        else:
            return f"{str(self)}-{str(other)}"

    def __mul__(self, other):
        def is_round(num): # if it's a round number we remove the .0
            return str(int(num)) if num == int(num) else str(num)

        if type(other) == str:
            return Unit(is_round(float(self.prefix) * float(other)) + "".join(str(i) for i in self.suffix))
        elif type(other) == Unit:
            prefix = is_round(float(self.prefix) * float(other.prefix))

            suffix_symbols = {} # this represents the variables and their respective power
            self_symbols = set([i.symbol for i in self.suffix])
            other_symbols = set([i.symbol for i in other.suffix])

            for i in self_symbols | other_symbols:
                suffix_symbols.update({f"{i}": 0})
                for j in self.suffix:
                    if j.symbol == i:
                        suffix_symbols[i] += j.power
                for k in other.suffix:
                    if k.symbol == i:
                        suffix_symbols[i] += k.power

            suffix = ""
            for i in suffix_symbols:
                if suffix_symbols[i] > 1:
                    suffix += f"{i}^{suffix_symbols[i]}"
                else:
                    suffix += str(i)
            return Unit(prefix + suffix)

    def __str__(self):
        return str(self.prefix) + "".join(str(i) for i in self.suffix)

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if type(other) == Unit:
            self_suffix = set([str(i) for i in self.suffix])
            other_suffix = set([str(i) for i in other.suffix])
            return self.prefix == other.prefix and self_suffix == other_suffix
        else:
            return False

    def value(self):
        if self.prefix == '':
            return 1
        elif self.prefix == '-':
            return -1
        elif self.prefix[0] == '-':
            return -float(self.prefix[1:])
        else:
            return float(self.prefix)

    def get_suffix_list(self):
        return [str(i) for i in self.suffix]

    def get_suffix_str(self):
        return "".join(str(i) for i in self.suffix)

    def compare_suffix(self, other):
        if type(other) == Unit:
            return set(self.get_suffix_list()) == set(other.get_suffix_list())
        else:
            return False

class Expression:
    def __init__(self, expression):
        self.units = []
        for i in re.findall(r'\-?[^\+\-]+', expression):
            self.units.append(Unit(i))

    def __add__(self, other):
        if type(other) == Unit:
            unique = True
            for i in range(len(self.units)):
                temp = self.units[i] + other
                if type(temp) == Unit:
                    self.units[i] = temp
                    unique = False
                    break
            if unique:
                self.units.append(other)
            return self
        elif type(other) == Expression:
            for i in range(len(other.units)):
                for j in range(len(self.units)):
                    if self.units[j].compare_suffix(other.units[i]):
                        self.units[j] += other.units[i]
                        break
                    elif j == len(self.units) - 1 and not self.units[j].compare_suffix(other.units[i]):
                        self.units.append(other.units[i])
            return self
        else:
            return None

    def __sub__(self, other):
        if type(other) == Unit:
            unique = True
            for i in range(len(self.units)):
                temp = self.units[i] - other
                if type(temp) == Unit:
                    self.units[i] = temp
                    unique = False
                    break
            if unique:
                self.units.append(Unit(f"-{other.prefix}{other.get_suffix()}"))
            return self
        elif type(other) == Expression:
            for i in range(len(other.units)):
                for j in range(len(self.units)):
                    if self.units[j].compare_suffix(other.units[i]):
                        self.units[j] -= other.units[i]
                        break
                    elif j == len(self.units) - 1 and not self.units[j].compare_suffix(other.units[i]):
                        self.units.append(Unit(f"-{other.units[i].prefix}{other.units[i].get_suffix_str()}"))
            return self
        else:
            return None

    def __mul__(self, other):
        if type(other) == Unit:
            for i in range(len(self.units)):
                self.units[i] = self.units[i] * other
            return self
        elif type(other) in [Expression, list]:
            result = []
            for i in self.units:
                if type(other) == Expression:
                    for j in other.units:
                        result.append(i * j)
                else:
                    for j in other:
                        result.append(i * j)
            self.units = result
            return self

    def __pow__(self, other):
        if re.search(r"[a-z]", str(self)):
            raise SyntaxError("Incorrect usage of the power operator")
        if type(other) in [str, int, float]:
            other = int(other)
            if other == 0:
                return Expression("1")
            elif other > 1:
                temp = self.get_units()
                for i in range(other - 1):
                    self = self * temp
                return self
            elif other < 0:
                return Expression(f"{1/int(str((self**(-other))))}")
        elif type(other) == Expression:
            other = int(float(other.units[0].prefix))
            return self ** other
        else:
            return Expression("1")

    def __str__(self):
        if self.units != []:
            result = str(self.units[0])
            for i in self.units[1:]:
                if float(i.prefix) >= 0:
                    result += '+' + str(i)
                else:
                    result += str(i)
            return result
        else:
            return ""

    def __repr__(self):
        return str(self)

    def get_units(self):
        return [Unit(i.prefix+i.get_suffix_str()) for i in self.units]
