"""
The units module provides classes that represent quantities and units, 
with quantities like Duration, Length and Speed, and units for the quantities,
e.g.,'s', 'h' and 'min' for the Duration quantity. For simulation models, 
it is convenient to enter durations and delays using a quantity with a unit,
and to display the simulator time in a value with a unit, to know, e.g., 
that 3 hours have passed in the simulation.

For now, units assume linear scales with respect to a base unit, usually
an SI unit. Most of the calculation and transformation work is done in the
Quantity class. The Quantity class subclasses the builtin float class. 
Internally, the value of the quantity is stored in the base unit in the
float class, and the actual unit is stored in the Quantity class as a str. 

This module has been based on the Java DJUNITS project (Delft Java units), as
documented at https://djunits.org. 
"""
from typing import TypeVar, Generic
from abc import ABC, abstractmethod

Q = TypeVar('Q')


class Quantity(Generic[Q], ABC, float):
    
    __unitlist = ('rad', 'sr', 'kg', 'm', 's', 'A', 'K', 'mol', 'cd')

    @classmethod
    @abstractmethod
    def baseunit(cls) -> str:
        """
        Return the baseunit for this quantity, preferably an SI unit.
        The baseunit is coded as a string, and should be present in the 
        units dictionary with a conversion factor of 1.
        """

    @classmethod
    @abstractmethod
    def units(cls) -> dict[str, float]:
        """
        Return the available units for this quantity with a conversion 
        factor to the baseunit. The units are specified in a dictionary,
        mapping each string descriptor for the unit onto the conversion
        factor to the baseunit.
        """
        
    @classmethod
    @abstractmethod
    def displayunits(cls) -> dict[str, str]:
        """
        Return a dictionary with a translation of the unit as it is
        entered in the code and the way the unit will be displayed in the
        str(..) and repr(..) methods. An example is the 'micro' sugn, 
        which is entered as 'mu' in the units, but should be displayed as 
        a real mu sign (\u03BC). To make this translation for, for instance, 
        a micrometer, the displayunits method should return a dict
        {'mum', '\03BCm'}. Another examples is the Angstrom sign for length. 
        In case no transformations are necessary for the units in the 
        quantity, an empty dict {} can be returned.
        """
        
    @classmethod
    @abstractmethod
    def sisig(cls) -> dict[str, int]:
        """
        Return a dictionary with the SI signature of the quantity. The 
        symbols that can be used are '1', 'kg', 'm', 's', 'A', 'K', 'mol',
        and 'cd'. For force (Newton), the SI signature would be given as
        {'kg': 1, 'm': 1, 's': -2} equivalent to kg.m/s^2. In addition to
        the SI-units, we allow 'rad' (m/m) and 'sr' (m^2/m^2) as well for
        reasons of clarity. 
        """
        
    @classmethod
    @abstractmethod
    def instantiate(cls, value, unit: str=None, **kwargs) -> Q:
        """
        Instantiate a new quantity of the right type.
        """
    
    def __new__(cls, value, unit: str=None, **kwargs):
        """
        The __new__ method created a Quantity instance of the right type. 
        It stores the si-value of the quantity in the float that Quantity
        subclasses. The storage of the unit is done in __init__. 
        
        Raises
        ------
        ValueError
            when the provided unit is not defined for this quantity
        """
        if unit == None:
            unitmultiplier = cls.units()[cls.baseunit()]
        else:
            if not unit in cls.units():
                raise ValueError(f"unit {unit} not defined")
            unitmultiplier = cls.units()[unit]
        basevalue = value * unitmultiplier
        return super().__new__(cls, basevalue, **kwargs)
    
    def __init__(self, value: float, unit: str=None, **kwargs):
        """
        Create a Quantity instance of the right type. The si-value of 
        the quantity is stored in the float that Quantity subclasses, so
        internally all values are stored in their base-unit, which is 
        most often the si-unit.
        
        Raises
        ------
        ValueError
            when the provided unit is not defined for this quantity
        """
        if unit == None:
            self._unit = self.baseunit()
        else:
            self._unit = unit
    
    @property
    def displayvalue(self) -> float:
        """
        Return the display value of the quantity. So, for Length(14, 'cm')
        the displayvalue is 14. 
        """
        return float(self) / self.units()[self._unit]
    
    @property
    def si(self) -> float:
        """
        Return the internal unit (often, but not always, si) value of the 
        quantity. So, for Length(14, 'cm') si is 0.14, since the base si unit
        is meters. 
        """
        return float(self)

    @property
    def unit(self) -> str:
        """
        Return the unit with which the quantity was defined. So, for 
        Length(14, 'cm') the unit is 14. Note that the unit is different from
        the displayunit. For Length(14, 'mum'), the unit is 'mum'.   
        """
        return self._unit
        
    def as_unit(self, newunit: str) -> Q:
        """
        Return a new quantity that has been transformed to the new unit.
        The instantiation avoids multiplication and division for the
        allocation to the new unit as would be the case in:
        return self.instantiate(float(self) / self.units()[newunit], newunit).
        Instead, the internal si-value is copied into the return value and
        the unit is adapted to the new unit. This means that the two 
        quantities Length(3.4, 'mi').si and Length(3.4, 'mi').as_unit('mm').si
        are exactly the same without rounding errors. 
        
        Raises
        ------
        ValueError
            when newunit is not defined for this quantity
        """
        if not newunit in self.units():
            raise ValueError(f"unit {newunit} not defined")
        ret = self.instantiate(self.si, self.baseunit())
        ret._unit = newunit
        return ret
    
    def _val(self, si:float) -> Q:
        """
        Create a new quantity with the given si value and the base unit
        of the current quantity. So, if _val(80) is called on Area(10, "ha"),
        the returning value will be 
        """
        q = self.instantiate(si, self.baseunit())
        q._unit = self._unit
        return q

    def __abs__(self) -> Q:
        """
        Return a new quantity with the absolute value. So, abs(Length(-2, 'm')
        will return Length(2.0, 'm').
        """
        return self._val(abs(float(self)))
    
    def __add__(self, other) -> Q:
        """
        Return a new quantity containing the sum of this quantity and the
        other quantity.
        
        Raises
        ------
        ValueError
            when the two quantities are of different types
        """
        if (self.__class__ != other.__class__):
            raise ValueError("adding incompatible quantities")
        return self._val(float(self) + float(other))
    
    def __ceil__(self) -> Q:
        """
        Return the nearest integer value above the value of this quantity.
        Note that this function works on the display value of the quantity
        and not on the internal si-value. When we want to calculate the
        ceiling of 10.4 cm, we expect 11 cm, and not 100 cm (the nearest 
        integer value above 0.104 m is 1 m = 100 cm). Note that the ceil of 
        -3.5 is -3.
        """
        return self.instantiate(self.displayvalue.__ceil__(), self._unit)
    
    def __floor__(self) -> Q:
        """
        Return the nearest integer value below the value of this quantity.
        Note that this function works on the display value of the quantity
        and not on the internal si-value. When we want to calculate the
        floor of 10.4 cm, we expect 10 cm, and not 0 cm (the nearest integer
        value below 0.104 m is 0 m). Note that the floor of -3.5 is -4.
        """
        return self.instantiate(self.displayvalue.__floor__(), self._unit)
    
    def __floordiv__(self, other):
        """
        Return the nearest integer value below the value of the division of 
        this quantity by the provided float or integer value. Note that 
        this function works on the display value of the quantity and
        not on the internal si-value. When we want to calculate 
        (10.0 cm // 3), we expect 3 cm, and not 0 cm (the nearest integer
        value below the result of 0.1 // 3 in the si unit meter is 0 m). 
        """
        if not (other.__class__ == float or other.__class__ == int):
            raise ValueError("// operator needs float or int")
        return self.instantiate(self.displayvalue // other, self._unit)
    
    def __mod__(self, other):
        """
        Return the remainder of the integer division of  this quantity 
        by the provided float or integer value. Note that this function 
        works on the display value of the quantity and not on the internal 
        si-value. When we want to calculate (10.0 cm % 3), we expect 1 cm, 
        and not 0.1 m (the remainder of 0.1 % 3 in the si unit meter). 
        """
        if not (other.__class__ == float or other.__class__ == int):
            raise ValueError("% operator needs float or int")
        return self.instantiate(self.displayvalue % other, self._unit)

    def __mul__(self, other):
        """
        Return a new quantity containing the multiplication of this quantity 
        by the provided factor (where the factor comes last in the 
        multiplication). The factor has to be of type float or int. 
        The result of Area(25.0, 'm^2') * 2 = Area(50.0, 'm^2).
        
        Raises
        ------
        ValueError
            when the multiplication factor is not a float or an int
        """
        if not (other.__class__ == float or other.__class__ == int):
            raise ValueError("* operator needs float or int")
        return self._val(float(self) * other)

    def __neg__(self):
        """
        Return a new quantity containing the negation of the value of the
        quantity. A Duration of 10 seconds becomes a Duration of -10 
        seconds. The __neg__ function implements the behavior of the
        unary "-" behavior in front of a number. 
        """
        return self._val(-float(self))

    def __pos__(self):
        """
        Return the quantity, since the unary "+" operator (placing a "+"
        sign in front of a number or quantity) has no effect.
        """
        return self

    def __radd__(self, other):
        """
        Return a new quantity containing the sum of this quantity and the
        other quantity. radd is called for 2.0 + Length(1.0, 'm'),
        where the left hand side is not a Quantity, and the right hand 
        side is a Quantity. Since (a + b) == (b + a), the add function
        is used for the implementation. Typically, the radd function will 
        lead to a ValueError 
        
        Raises
        ------
        ValueError
            when the other is of a different type than self
        """
        return self.__add__(other)

    def __rmul__(self, other):
        """
        Return a new quantity containing the multiplication of this quantity 
        by the provided factor (where the factor comes first in the
        multiplication). The factor has to be of type float or int. 
        The result of 2.0 * Area(25.0, 'm^2') = Area(50.0, 'm^2).
        
        Raises
        ------
        ValueError
            when the multiplication factor is not a float or an int
        """
        return self.__mul__(other)
    
    def __round__(self) -> Q:
        """
        Return the nearest integer value for the value of this quantity.
        Note that this function works on the display value of the quantity
        and not on the internal si-value. When we want to calculate the
        round(10.4 cm), we expect 10 cm, and not 0 cm (the rounded value of
        0.104 m). 
        """
        return self.instantiate(self.displayvalue.__round__(), self._unit)

    def __rsub__(self, other):
        """
        Return a new quantity containing the difference of the other value
        and this quantity. rsub is called for 2.0 - Length(1.0, 'm'),
        where the left hand side is not a Quantity, and the right hand 
        side is a Quantity. Typically, the rsub function will lead to a
        ValueError 
        
        Raises
        ------
        ValueError
            when the other is of a different type than self
        """
        return self.__add__(other.__neg__())

    def __sub__(self, other):
        """
        Return a new quantity containing the difference of this quantity 
        and the other quantity.
        
        Raises
        ------
        ValueError
            when the two quantities are of different types
        """
        if (self.__class__ != other.__class__):
            raise ValueError("subtracting incompatible quantities")
        return self._val(float(self) - float(other))

    def __truediv__(self, other):
        """
        Return a new quantity containing the division of this quantity 
        by the provided divisor. The factor has to be of type float or int. 
        The result of Area(50.0, 'm^2') / 2 = Area(25.0, 'm^2).
        
        Raises
        ------
        ValueError
            when the divisor is not a float or an int
        """
        if self.__class__ == other.__class__:
            return float(self) / float(other)
        if not (other.__class__ == float or other.__class__ == int):
            raise ValueError("/ operator needs float or int")
        return self._val(float(self) / other)

    def __trunc__(self):
        """
        Return the nearest integer value below the value of this quantity,
        where the direction for negative numbers is towards zero. The trunc 
        of -3.5 is therefore -3, symmetric with the trunc of +3.5.
        Note that this function works on the display value of the quantity
        and not on the internal si-value. When we want to calculate the
        floor of 10.4 cm, we expect 10 cm, and not 0 cm (the nearest integer
        value below 0.104 m is 0 m). 
        """
        return self.instantiate(self.displayvalue.__trunc__(), self._unit)
    
    def __pow__(self, power):
        """
        Return a new quantity containing the value of this quantity to the
        provided power. The power has to be of type float or int. Note that 
        this function works on the display value of the quantity and not
        on the internal si-value.
        The result of Area(5.0, 'km^2') ** 2 = Area(25.0, 'km^2).
        
        Raises
        ------
        ValueError
            when the multiplication factor is not a float or an int
        """
        if not (power.__class__ == float or power.__class__ == int):
            raise ValueError("** operator needs float or int")
        return self.instantiate(self.displayvalue ** power, self._unit)

    def __str__(self):
        """
        Return a string representation of the quantity, where the chosen unit 
        follows the value without a space.
        """
        return str(self.displayvalue) + self.displayunits().get(self._unit,
                self._unit)

    def __repr__(self):
        """
        Return a string representation of the quantity, where the chosen unit 
        follows the value without a space.
        """
        return str(self.displayvalue) + self.displayunits().get(self._unit,
                self._unit)

    @classmethod
    def siunits(cls, div:bool=True, hat:str='', dot:str='') -> str:
        return Quantity._siunits(cls.sisig(), div, hat, dot)
    
    @staticmethod
    def _siunits(sistr: dict[str, int], div:bool=True, hat:str='',
                 dot:str='') -> str:
        s = ""
        t = ""
        for unit in Quantity.__unitlist:
            if unit in sistr:
                v: int = sistr[unit]
                if v > 0 or (v < 0 and not div):
                    if len(s) > 0:
                        s += dot
                    s += unit
                    if v > 1 or v < 0:
                        s += hat + str(v)
        if div:
            for unit in Quantity.__unitlist:
                if unit in sistr:
                    v: int = sistr[unit]
                    if v < 0:
                        if len(t) > 0:
                            t += dot
                        t += unit
                        if v < -1:
                            t += hat + str(-v)
        if len(s) == 0:
            s = "1"
        if len(t) > 0:
            s += "/" + t
        return s


class Duration(Quantity['Duration']):
    __baseunit = 's'
    __units = {'s': 1, 'ms': 1E-3, 'mus': 1E-6, 'ns': 1E-9, 'min': 60,
              'minute': 60, 'hr': 3600, 'hour': 3600, 'h': 3600,
              'day': 24 * 60 * 60, 'd': 24 * 60 * 60, 'w': 7.0 * 86400.0,
              'wk': 7.0 * 86400.0, 'week': 7.0 * 86400.0}
    __displayunits = {'mus': '\u03BCs'}
    __sisig = {'s': 1}

    @classmethod
    def baseunit(cls) -> str:
        return cls.__baseunit
    
    @classmethod
    def units(cls) -> dict[str, float]:
        return cls.__units
    
    @classmethod
    def displayunits(cls) -> dict[str, str]:
        return cls.__displayunits
    
    @classmethod
    def sisig(cls) -> dict[str, int]:
        return cls.__sisig
    
    @classmethod
    def instantiate(cls, value, unit: str=None, **kwargs):
        return Duration(value, unit, **kwargs)


class Length(Quantity['Length']):
    __baseunit = 'm'
    __units = {'m': 1, 'meter': 1, 'nm': 1E-9, 'mum': 1E-6, 'mm': 1E-3,
               'cm': 0.01, 'dm':0.1, 'dam': 10, 'hm':100, 'km':1000,
               'Mm': 1E6, 'Gm': 1E9,
               'in': 0.0254, 'inch': 0.0254, '"': 0.0254,
               'ft': 0.3048, 'foot': 0.3048,
               'yd': 0.9144, 'yard': 0.9144,
               'mi': 1609.344, 'mile': 1609.344}
    __displayunits = {'mum': '\u03BCm'}
    __sisig = {'m': 1}

    @classmethod
    def baseunit(cls) -> str:
        return cls.__baseunit
    
    @classmethod
    def units(cls) -> dict[str, float]:
        return cls.__units

    @classmethod
    def displayunits(cls) -> dict[str, str]:
        return cls.__displayunits
    
    @classmethod
    def sisig(cls) -> dict[str, int]:
        return cls.__sisig

    @classmethod
    def instantiate(cls, value, unit: str=None, **kwargs):
        return Length(value, unit, **kwargs)
    
    def __mul__(self, other):
        if isinstance(other, Length):
            return Area(float(self) * float(other), "m^2")
        else:
            return super().__mul__(other)

    def __truediv__(self, other):
        if isinstance(other, Duration):
            return Speed(float(self) / float(other), "m/s")
        else:
            return super().__truediv__(other)


class Speed(Quantity['Speed']):
    __baseunit = 'm/s'
    __units = {'m/s': 1, 'mm/s': 1E-3, 'cm/s': 0.01, 'dm/s':0.1,
               'mum/s': 1E-6, 'nm/s': 1E-9, 'dam/s': 10,
               'hm/s': 100, 'km/s':1000, 'km/h': 1000.0 / 3600.0,
               'in/s': 0.0254, 'inch/second': 0.0254,
               'ft/s': 0.3048, 'foot/second': 0.3048,
               'yd/s': 0.9144, 'yard/second': 0.9144,
               'mi/s': 1609.344, 'mile/second': 1609.344,
               'mi/h': 0.44704, 'mile/hour': 0.44704}
    __displayunits = {'mum/s': '\u03BCm/s'}
    __sisig = {'m': 1, 's':-1}

    @classmethod
    def baseunit(cls) -> str:
        return cls.__baseunit
    
    @classmethod
    def units(cls) -> dict[str, float]:
        return cls.__units

    @classmethod
    def displayunits(cls) -> dict[str, str]:
        return cls.__displayunits
    
    @classmethod
    def sisig(cls) -> dict[str, int]:
        return cls.__sisig

    @classmethod
    def instantiate(cls, value, unit: str=None, **kwargs):
        return Speed(value, unit, **kwargs)


class Area(Quantity):
    __baseunit = 'm^2'
    __units = {'m^2': 1, 'nm^2': 1E-18, 'mum^2': 1E-12, 'mm^2': 1E-6,
               'cm^2': 1E-4, 'dm^2':0.01, 'dam^2': 100,
               'hm^2': 1E4, 'km^2': 1E6,
               'in^2': 0.0254 * 0.0254,
               'ft^2': 0.3048 * 0.3048,
               'yd^2': 0.9144 * 0.9144,
               'mi^2': 1609.344 * 1609.344}
    __displayunits = {'mum^2': '\u03BCm^2'}
    __sisig = {'m': 2}
    
    @classmethod
    def baseunit(cls) -> str:
        return cls.__baseunit
    
    @classmethod
    def units(cls) -> dict[str, float]:
        return cls.__units

    @classmethod
    def displayunits(cls) -> dict[str, str]:
        return cls.__displayunits
    
    @classmethod
    def sisig(cls) -> dict[str, int]:
        return cls.__sisig

    @classmethod
    def instantiate(cls, value, unit: str=None, **kwargs):
        return Area(value, unit, **kwargs)
