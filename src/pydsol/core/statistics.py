import math
from statistics import NormalDist

from pydsol.core.interfaces import StatEvents, SimulatorInterface, \
    ReplicationInterface, SimStatisticsInterface, StatisticsInterface
from pydsol.core.pubsub import EventProducer, EventListener, Event, \
    TimedEvent, EventType
from pydsol.core.utils import get_module_logger

__all__ = [
    "Counter",
    "Tally",
    "WeightedTally",
    "TimestampWeightedTally",
    "EventBasedCounter",
    "EventBasedTally",
    "EventBasedWeightedTally",
    "EventBasedTimestampWeightedTally",
    "SimCounter",
    "SimTally",
    "SimPersistent",
    ]

logger = get_module_logger('statistics')


class Counter(StatisticsInterface):
    """
    The Counter is a simple statistics object that can count events or
    occurrences. Note that the number of observations is not necessarily
    equal to the value of the counter, since the counter allows any 
    integer as the increment (or decrement) during an observation.
    
    The initialize() method resets the statistics object. The initialize 
    method can, for instance, be called when the warmup period of the 
    simulation experiment has completed. 
    
    Example
    -------
    In simulation, the Counter can be used to count arrivals, the number of
    processed entities in servers, the number of entities in the system, etc.  
    
    Attributes
    ----------
    _name: str
        the name by which the statistics object can be identified
    _n: int
        the number of observations
    _count: int
        the current value of the counter 
    """

    def __init__(self, name: str):
        """
        Construct a new Counter statistics object. The Counter is a simple 
        statistics object that can count events or occurrences. Note that 
        the number of observations is not necessarily equal to the value 
        of the counter, since the counter allows any integer as the 
        increment (or decrement) during an observation.
        
        Parameters
        ----------
        name: str
            The name by which the statistics object can be identified.
            
        Raises
        ------
        TypeError
            when name is not a string
        """
        if not isinstance(name, str):
            raise TypeError("counter name {name} not a str")
        self._name = name
        self.initialize()
        
    def initialize(self):
        """
        Initialize the statistics object, resetting all values to the state 
        where no observations have been made. This method can, for instance, 
        be called when the warmup period of the simulation experiment has
        completed. 
        """
        self._count = 0
        self._n = 0

    @property
    def name(self):
        """
        Return the name of this statistics object.
        
        Returns
        -------
        str
            The name of this statistics object.
        """
        return self._name

    def ingest(self, value: int) -> int:
        """
        Process one observation. The value indicates the increment or 
        decrement of the counter (often 1). 
        
        Parameters
        ----------
        value: int
            The increment or decrement of the Counter.
            
        Returns
        -------
        int
            the value, to use the `ingest` method inside an expression
            
        Raises
        ------
        TypeError
            when value is not an int
        """
        if not isinstance(value, int):
            raise TypeError("ingested value {value} not an int")
        self._count += value
        self._n += 1
        return value

    def count(self):
        """
        Return the current value of the counter statistic.
        
        Returns
        -------
        int
            The current value of the counter statistic.
        """
        return self._count

    def n(self):
        """
        Return the number of observations.
        
        Returns
        -------
        int
            The number of observations.
        """
        return self._n

    def __str__(self):
        return f"Counter[name={self._name}, n={self._n}, count={self._count}]"
    
    def __repr__(self):
        return str(self)
    
    def report_header(self) -> str:
        """
        Return a string representing a header for a textual table with a
        monospaced font that can contain multiple counters.
        """
        return '-' * 72 \
             +f"\n| {'Counter name':<48} | {'n':>6} | {'count':>8} |\n" \
             +'-' * 72
    
    def report_line(self) -> str:
        """
        Return a string representing a line with important statistics values 
        for this statistical object, for a textual table with a monospaced
        font that can contain multiple counters.
        """
        return f"| {self.name:<48} | {self.n():>6} | {self.count():>8} |"

    def report_footer(self) -> str:
        """
        Return a string representing a footer for a textual table with a
        monospaced font that can contain multiple counters.
        """
        return '-' * 72
    

class Tally(StatisticsInterface):
    r"""
    The Tally is a statistics object that calculates descriptive statistics
    for a number of observations, such as mean, variance, minimum, maximum, 
    skewness, etc. 
    
    The initialize() method resets the statistics object. The initialize 
    method can, for instance, be called when the warmup period of the 
    simulation experiment has completed. 
    
    The mean of the Tally is calculated with the formula:
    
    .. math:: \mu = \sum_{i=1}^{n} {x_{i}} / n
    
    where n is the number of observations and :math:`x_{i}` are the observations.
    
    Example
    -------
    In discrete-event simulation, the Tally can be used to calculate 
    statistical values for waiting times in queues, time in system of entities, 
    processing times at a server, and throughput times of partial processes. 
    
    Attributes
    ----------
    _name: str
        the name by which the statistics object can be identified
    _n: int
        the number of observations
    _sum: float
        the sum of the observation values 
    _min: float
        the lowest value in the current observations 
    _max: float
        the highest value in the current observations
    _m1, _m2, _m3, _m4: float
        the 1st to 4th moment of the observations
    """

    def __init__(self, name: str):
        """
        Construct a new Tally statistics object. The Tally is a statistics 
        object that calculates descriptive statistics for a number of 
        observations, such as mean, variance, minimum, maximum, skewness, etc. 
        
        Parameters
        ----------
        name: str
            The name by which the statistics object can be identified.
            
        Raises
        ------
        TypeError
            when name is not a string
        """
        if not isinstance(name, str):
            raise TypeError("tally name {name} not a str")
        self._name = name
        self.initialize()
        
    def initialize(self):
        """
        Initialize the statistics object, resetting all values to the state 
        where no observations have been made. This method can, for instance, 
        be called when the warmup period of the simulation experiment has
        completed. 
        """
        self._n = 0
        self._sum = 0.0
        self._m1 = 0.0
        self._m2 = 0.0
        self._m3 = 0.0
        self._m4 = 0.0
        self._min = math.nan
        self._max = math.nan

    @property
    def name(self):
        """
        Return the name of this statistics object.
        
        Returns
        -------
        str
            The name of this statistics object.
        """
        return self._name

    def ingest(self, value: float) -> float:
        """
        Process one observation value, and calculate all statistics up to
        and including the last value (mean, standard deviation, minimum,
        maximum, skewness, etc.).
        
        Parameters
        ----------
        value: float
            The value of the observation.
            
        Returns
        -------
        float
            the value, to use the `ingest` method inside an expression

        Raises
        ------
        TypeError
            when value is not a number
        ValueError
            when value is NaN
        """
        if not isinstance(value, (int, float)):
            raise TypeError("tally ingested value must be a number")
        if math.isnan(value):
            raise ValueError("tally ingested value cannot be nan")
        if self._n == 0:
            self._min = +math.inf
            self._max = -math.inf
        self._n += 1
        delta = value - self._m1
        oldm2 = self._m2
        oldm3 = self._m3
        n = float(self._n)
        # Eq 4 in https://fanf2.user.srcf.net/hermes/doc/antiforgery/stats.pdf
        # Eq 1.1 in https://prod-ng.sandia.gov/techlib-noauth/access-control.cgi
        #    /2008/086212.pdf
        self._m1 += delta / n
        # Eq 44 in https://fanf2.user.srcf.net/hermes/doc/antiforgery/stats.pdf
        # Eq 1.2 in https://prod-ng.sandia.gov/techlib-noauth/access-control.cgi
        #    /2008/086212.pdf
        self._m2 += delta * (value - self._m1)
        # Eq 2.13 in https://prod-ng.sandia.gov/techlib-noauth/access-control.cgi
        #    /2008/086212.pdf
        self._m3 += (-3 * oldm2 * delta / n + (n - 1) * 
                     (n - 2) * delta * delta * delta / n / n)
        # Eq 2.16 in https://prod-ng.sandia.gov/techlib-noauth/access-control.cgi
        #    /2008/086212.pdf
        self._m4 += (-4 * oldm3 * delta / n + 
            6 * oldm2 * delta * delta / n / n + (n - 1)
            * (n * n - 3 * n + 3) * delta * delta * delta 
            * delta / n / n / n)
        self._sum += value
        if value < self._min:
            self._min = value
        if value > self._max:
            self._max = value
        return value

    def n(self) -> int:
        """
        Return the number of observations.
        
        Returns
        -------
        int
            The number of observations.
        """
        return self._n

    def min(self) -> float:
        """
        Return the observation with the lowest value. When no observations
        were registered, NaN is returned.
        
        Returns
        -------
        float
            The observation with the lowest value, or NaN when no observations
            were registered.
        """
        return self._min

    def max(self) -> float:
        """
        Return the observation with the highest value. When no observations
        were registered, NaN is returned.
        
        Returns
        -------
        float
            The observation with the highest value, or NaN when no observations
            were registered.
        """
        return self._max

    def sample_mean(self) -> float:
        r"""
        Return the sample mean. When no observations were registered, 
        NaN is returned.
        
        The sample mean of the Tally is calculated with the formula:
    
        .. math:: \mu = \sum_{i=1}^{n} {x_{i}} / n
    
        where n is the number of observations and :math:`x_{i}` are the 
        observations.

        Returns
        -------
        float
            The sample mean, or NaN when no observations were registered.
        """
        if self._n > 0:
            return self._m1
        return math.nan

    def population_mean(self) -> float:
        r"""
        Return the population mean, which is for this statistic the same as
        the sample mean. When no observations were registered, NaN is returned.
        
        The population mean of the Tally is calculated with the formula:
    
        .. math:: \mu = \sum_{i=1}^{n} {x_{i}} / n
    
        where n is the number of observations and :math:`x_{i}` are the 
        observations.
        
        Returns
        -------
        float
            The population mean, or NaN when no observations were registered.
        """
        return self.sample_mean()

    def confidence_interval(self, alpha: float) -> tuple[float]:
        r"""
        Return the confidence interval around the sample mean with the
        provided alpha. When less than two observations were registered, 
        (NaN, NaN) is returned.
        
        Parameters
        ----------
        alpha: float
             Alpha is the significance level used to compute the confidence 
             level. The confidence level equals :math:`100 * (1 - alpha)\%`, 
             or in other words, an alpha of 0.05 indicates a 95 percent 
             confidence level.
        
        Returns
        -------
        (float, float)
            The confidence interval around the sample mean, or (NaN, NaN) 
            when less than two observations were registered.
            
        Raises
        ------
        TypeError
            when alpha is not a float
        ValueError
            when alpha is not between 0 and 1, inclusive
        """
        if not isinstance(alpha, float):
            raise TypeError(f"alpha {alpha} not a float")
        if not 0 <= alpha <= 1:
            raise ValueError(f"alpha {alpha} not between 0 and 1")
        sample_mean = self.sample_mean()
        if math.isnan(sample_mean) or math.isnan(self.sample_stdev()):
            return (math.nan, math.nan)
        level = 1.0 - alpha / 2.0
        z = NormalDist(0.0, 1.0).inv_cdf(level)
        confidence = z * math.sqrt(self.sample_variance() / self._n)
        return (max(self._min, sample_mean - confidence),
                min(self._max, sample_mean + confidence))
    
    def sample_stdev(self) -> float:
        r"""
        Return the (unbiased) sample standard deviation of all observations 
        since the initialization. The sample standard deviation is defined 
        as the square root of the sample variance. When less than two 
        observations were registered, NaN is returned.
        
        The formula is:
        
         .. math::
            S = \sqrt{ {\frac{1}{n-1}} \left( \sum{x_{i}^2} - 
            \left( \sum{x_{i}} \right)^2 / n \right) }
        
        Returns
        -------
        float
            The (unbiased) sample standard deviation of all observations 
            since the initialization, or NaN  when less than two observations 
            were registered.
        """
        if self._n > 1:
            return math.sqrt(self.sample_variance())
        return math.nan
    
    def population_stdev(self):
        r"""
        Return the current (biased) population standard deviation of all 
        observations since the initialization. The population standard 
        deviation is defined as the square root of the population variance. 
        When no observations were registered, NaN is returned.
        
        The formula is:
        
         .. math::
            \sigma = \sqrt{ {\frac{1}{n}} \left( \sum{x_{i}^2} - 
            \left( \sum{x_{i}} \right)^2 / n \right) }
        
        Returns
        -------
        float
            The (unbiased) sample standard deviation of all observations 
            since the initialization, or NaN when no observations were 
            registered.
        """
        if self._n > 0:
            return math.sqrt(self.population_variance())
        return math.nan
    
    def sum(self):
        """
        Return the sum of all observations since the statistic initialization.
        
        Returns
        -------
        float
            The sum of the observations.
        """
        return self._sum
    
    def sample_variance(self):
        r"""
        Return the (unbiased) sample variance of all observations since
        the statistic initialization. When less than two observations were 
        registered, NaN is returned.
        
        The formula is:
        
         .. math::
            S^2 = { {\frac{1}{n-1}} \left( \sum{x_{i}^2} - 
            \left( \sum{x_{i}} \right)^2 / n \right) }
        
        Returns
        -------
        float
            The (unbiased) sample variance of all observations since the 
            initialization, or NaN  when less than two observations were 
            registered.
        """
        if self._n > 1:
            return self._m2 / (self._n - 1)
        return math.nan
    
    def population_variance(self):
        r"""
        Return the (biased) sample variance of all observations since
        the statistic initialization. When no observations were registered, 
        NaN is returned.
        
        The formula is:
        
         .. math::
            \sigma^2 = { {\frac{1}{n}} \left( \sum{x_{i}^2} - 
            \left( \sum{x_{i}} \right)^2 / n \right) }
        
        Returns
        -------
        float
            The (biased) sample variance of all observations since the 
            initialization, or NaN when no observations were registered.
        """
        if self._n > 0:
            return self._m2 / (self._n)
        return math.nan
    
    def sample_skewness(self):
        n = float(self._n)
        if n > 2:
            return (self.population_skewness() 
                    * math.sqrt(n * (n - 1)) / (n - 2))
        return math.nan
    
    def population_skewness(self):
        if self._n > 1:
            return (self._m3 / self._n) / self.population_variance() ** 1.5
        return math.nan
    
    def sample_kurtosis(self):
        if self._n > 3:
            svar = self.sample_variance()
            return self._m4 / (self._n - 1) / svar / svar
        return math.nan
    
    def population_kurtosis(self):
        if self._n > 2:
            d2 = (self._m2 / self._n)
            return (self._m4 / self._n) / d2 / d2
        return math.nan
    
    def sample_excess_kurtosis(self):
        n = float(self._n)
        if n > 3:
            g2 = self.population_excess_kurtosis()
            return ((n - 1) / (n - 2) / (n - 3)) * ((n + 1) * g2 + 6)
        return math.nan

    def population_excess_kurtosis(self):
        if self._n > 2:
            # convert kurtosis to excess kurtosis, shift by -3
            return self.population_kurtosis() - 3.0
        return math.nan
     
    def __str__(self):
        return f"Tally[name={self._name}, n={self._n}, mean={self.sample_mean()}]"
    
    def __repr__(self):
        return str(self)

    def report_header(self) -> str:
        """
        Return a string representing a header for a textual table with a
        monospaced font that can contain multiple tallies.
        """
        return '-' * 72 \
             +f"\n| {'Tally name':<48} | {'n':>6} | {'p_mean':>8} |\n" \
             +'-' * 72
    
    def report_line(self) -> str:
        return f"| {self.name:<48} | {self.n():>6} | {self.population_mean():8.2f} |"

    def report_footer(self) -> str:
        return '-' * 72


class WeightedTally(StatisticsInterface):
    
    def __init__(self, name: str):
        if not isinstance(name, str):
            raise TypeError("weighted tally name {name} not a str")
        self._name = name
        self.initialize()
        
    def initialize(self):
        """
        Initialize the statistics object, resetting all values to the state 
        where no observations have been made. This method can, for instance, 
        be called when the warmup period of the simulation experiment has
        completed. 
        """
        self._n = 0
        self._sum_of_weights = 0.0
        self._weighted_mean = 0.0
        self._weight_times_variance = 0.0
        self._weighted_sum = 0.0
        self._min = math.nan
        self._max = math.nan

    @property
    def name(self):
        """
        Return the name of this statistics object.
        
        Returns
        -------
        str
            The name of this statistics object.
        """
        return self._name

    def ingest(self, weight: float, value:float) -> float:
        """
        Process one observation value and a corresponding weight, and 
        calculate all statistics up to and including the last weight-value 
        pair (mean, standard deviation, minimum, maximum, skewness, etc.).
        Weight has to be >= 0.
        
        Parameters
        ----------
        weight: float
            The weight of this observation (has to be >= 0).
        value: float
            The value of the observation.
            
        Returns
        -------
        float
            the value, to use the `ingest` method inside an expression
            
        Raises
        ------
        TypeError
            when weight or value is not a number
        ValueError
            when weight or value is NaN
        ValueError
            when weight < 0
        """
        if not isinstance(weight, (int, float)):
            raise TypeError("weight should be a number")
        if not isinstance(value, (int, float)):
            raise TypeError("value should be a number")
        if math.isnan(value):
            raise ValueError("tally ingested value cannot be nan")
        if math.isnan(weight):
            raise ValueError("tally weight cannot be nan")
        if weight < 0:
            raise ValueError("tally weight cannot be < 0")
        if weight == 0.0:
            return value
        if self._n == 0:
            self._min = +math.inf
            self._max = -math.inf
        self._n += 1
        # Eq 47 in https://fanf2.user.srcf.net/hermes/doc/antiforgery/stats.pdf
        self._sum_of_weights += weight;
        prev_weighted_mean = self._weighted_mean;
        # Eq 53 in https://fanf2.user.srcf.net/hermes/doc/antiforgery/stats.pdf
        self._weighted_mean += (weight / self._sum_of_weights 
                * (value - prev_weighted_mean))
        # Eq 68 in https://fanf2.user.srcf.net/hermes/doc/antiforgery/stats.pdf
        self._weight_times_variance += (weight * (value - prev_weighted_mean) 
                * (value - self._weighted_mean))
        self._weighted_sum += weight * value;
        if value < self._min:
            self._min = value
        if value > self._max:
            self._max = value
        return value

    def n(self):
        """
        Return the number of observations.
        
        Returns
        -------
        int
            The number of observations.
        """
        return self._n

    def min(self):
        return self._min

    def max(self):
        return self._max

    def weighted_sample_mean(self):
        if self._n > 0:
            return self._weighted_mean
        return math.nan

    def weighted_population_mean(self):
        return self.weighted_sample_mean()
    
    def weighted_sample_stdev(self):
        if self._n > 1:
            return math.sqrt(self.weighted_sample_variance())
        return math.nan
    
    def weighted_population_stdev(self):
        return math.sqrt(self.weighted_population_variance())
    
    def weighted_sample_variance(self):
        if self._n > 1:
            return self.weighted_population_variance() * self._n / (self._n - 1)
        return math.nan

    def weighted_population_variance(self):
        if self._n > 0:
            return self._weight_times_variance / self._sum_of_weights
        return math.nan

    def weighted_sum(self):
        return self._weighted_sum

    def __str__(self):
        return f"WeightedTally[name={self._name}, n={self._n}, "\
            +f"weighted mean={self.weighted_population_mean()}]"
            
    def __repr__(self):
        return str(self)

    def report_header(self) -> str:
        """
        Return a string representing a header for a textual table with a
        monospaced font that can contain multiple weighted tallies.
        """
        return '-' * 72 \
             +f"\n| {'Weighted Tally name':<48} | {'n':>6} | "\
             +f"{'p_mean':>8} |\n" \
             +'-' * 72
    
    def report_line(self) -> str:
        return f"| {self.name:<48} | {self.n():>6} | "\
            +f"{self.weighted_population_mean():8.2f} |"

    def report_footer(self) -> str:
        return '-' * 72


class TimestampWeightedTally(WeightedTally):
        
    def __init__(self, name: str):
        super().__init__(name)
        self.initialize()
        
    def initialize(self):
        """
        Initialize the statistics object, resetting all values to the state 
        where no observations have been made. This method can, for instance, 
        be called when the warmup period of the simulation experiment has
        completed. 
        """
        super().initialize()
        self._start_time = math.nan
        self._last_timestamp = math.nan
        self._last_value = 0.0
        self._active = True

    def isactive(self) -> bool:
        return self._active

    def end_observations(self, timestamp: float):
        self.ingest(timestamp, self._last_value)
        self._active = False
        
    def last_value(self) -> float:
        return self._last_value
        
    def ingest(self, timestamp: float, value:float) -> float:
        if math.isnan(value):
            raise ValueError("tally ingested value cannot be nan")
        if math.isnan(timestamp):
            raise ValueError("tally timestamp cannot be nan")
        if timestamp < self._last_timestamp:
            raise ValueError("tally timestamp before last timestamp")
        # only calculate when the time interval is larger than 0, 
        # and when the TimestampWeightedTally is active
        if (math.isnan(self._last_timestamp) 
                or timestamp > self._last_timestamp) and self._active:
            if math.isnan(self._start_time):
                self._start_time = timestamp
            else:
                deltatime = max(0.0, timestamp - self._last_timestamp)
                super().ingest(deltatime, self._last_value)
            self._last_timestamp = timestamp
        self._last_value = value
        return value

#----------------------------------------------------------------------------
# EVENT-BASED STATISTICS
#----------------------------------------------------------------------------


class EventBasedCounter(EventProducer, EventListener, Counter):
    
    def __init__(self, name: str):
        EventProducer.__init__(self)
        Counter.__init__(self, name)
 
    def initialize(self):
        """
        Initialize the statistics object, resetting all values to the state 
        where no observations have been made. This method can, for instance, 
        be called when the warmup period of the simulation experiment has
        completed. 
        """
        Counter.initialize(self)
        self.fire_initialized()
    
    def fire_initialized(self):
        """Separate method to allow easy overriding of firing the 
        INITIALIZED_EVENT as a TimedEvent."""
        self.fire(StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: Event):
        if not event.event_type == StatEvents.DATA_EVENT:
            raise ValueError(f"notification {event.event_type} for counter " + \
                             "is not a DATA_EVENT")
        if not isinstance(event.content, int):
            raise TypeError(f"notification {event.content} for counter " + \
                            "is not an int")
        self.ingest(event.content)
            
    def ingest(self, value: int):
        super().ingest(value)
        if self.has_listeners():
            self.fire_events(value)

    def fire_events(self, value: float):
        """Separate method to allow easy overriding of firing the statistics
        events as TimedEvent."""
        self.fire(StatEvents.OBSERVATION_ADDED_EVENT, value)
        self.fire(StatEvents.N_EVENT, self.n())
        self.fire(StatEvents.COUNT_EVENT, self.count())


class EventBasedTally(EventProducer, EventListener, Tally):
    
    def __init__(self, name: str):
        EventProducer.__init__(self)
        Tally.__init__(self, name)
 
    def initialize(self):
        """
        Initialize the statistics object, resetting all values to the state 
        where no observations have been made. This method can, for instance, 
        be called when the warmup period of the simulation experiment has
        completed. 
        """
        Tally.initialize(self)
        self.fire_initialized()
    
    def fire_initialized(self):
        """Separate method to allow easy overriding of firing the 
        INITIALIZED_EVENT as a TimedEvent."""
        self.fire(StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: Event):
        if not event.event_type == StatEvents.DATA_EVENT:
            raise ValueError(f"notification {event.event_type} for tally " + \
                             "is not a DATA_EVENT")
        if not (isinstance(event.content, float) or 
                isinstance(event.content, int)):
            raise TypeError(f"notification {event.content} for tally " + \
                            "is not a float or int")
        self.ingest(float(event.content))

    def ingest(self, value: float):
        super().ingest(value)
        if self.has_listeners():
            self.fire_events(value)

    def fire_events(self, value: float):
        self.fire(StatEvents.OBSERVATION_ADDED_EVENT, value)
        self.fire(StatEvents.N_EVENT, self.n())
        self.fire(StatEvents.MIN_EVENT, self.min())
        self.fire(StatEvents.MAX_EVENT, self.max())
        self.fire(StatEvents.SUM_EVENT, self.sum())
        self.fire(StatEvents.POPULATION_MEAN_EVENT, self.population_mean())
        self.fire(StatEvents.POPULATION_STDEV_EVENT, self.population_stdev())
        self.fire(StatEvents.POPULATION_VARIANCE_EVENT, self.population_variance())
        self.fire(StatEvents.POPULATION_SKEWNESS_EVENT, self.population_skewness())
        self.fire(StatEvents.POPULATION_KURTOSIS_EVENT, self.population_kurtosis())
        self.fire(StatEvents.POPULATION_EXCESS_K_EVENT, self.population_excess_kurtosis())
        self.fire(StatEvents.SAMPLE_MEAN_EVENT, self.sample_mean())
        self.fire(StatEvents.SAMPLE_STDEV_EVENT, self.sample_stdev())
        self.fire(StatEvents.SAMPLE_VARIANCE_EVENT, self.sample_variance())
        self.fire(StatEvents.SAMPLE_SKEWNESS_EVENT, self.sample_skewness())
        self.fire(StatEvents.SAMPLE_KURTOSIS_EVENT, self.sample_kurtosis())
        self.fire(StatEvents.SAMPLE_EXCESS_K_EVENT, self.sample_excess_kurtosis())


class EventBasedWeightedTally(EventProducer, EventListener, WeightedTally):
    
    def __init__(self, name: str):
        EventProducer.__init__(self)
        WeightedTally.__init__(self, name)
 
    def initialize(self):
        """
        Initialize the statistics object, resetting all values to the state 
        where no observations have been made. This method can, for instance, 
        be called when the warmup period of the simulation experiment has
        completed. 
        """
        WeightedTally.initialize(self)
        self.fire_initialized()
    
    def fire_initialized(self):
        """Separate method to allow easy overriding of firing the 
        INITIALIZED_EVENT as a TimedEvent."""
        self.fire(StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: Event):
        if not event.event_type == StatEvents.WEIGHT_DATA_EVENT:
            raise ValueError(f"notification {event.event_type} for " + \
                             "weighted tally is not a WEIGHT_DATA_EVENT")
        if not (isinstance(event.content, tuple)):
            raise TypeError(f"notification {event.content} for weighted " + \
                            "tally is not a tuple")
        if not len(event.content) == 2:
            raise TypeError(f"notification {event.content} for weighted " + \
                            "tally is not a tuple of length 2")
        if not (isinstance(event.content[0], float) or 
                isinstance(event.content[0], int)):
            raise TypeError(f"notification {event.content} for weighted " + \
                            "tally: weight is not a float or int")
        if not (isinstance(event.content[1], float) or 
                isinstance(event.content[1], int)):
            raise TypeError(f"notification {event.content} for weighted " + \
                            "tally: value is not a float or int")
        self.ingest(float(event.content[0]), float(event.content[1]))

    def ingest(self, weight: float, value: float):
        super().ingest(weight, value)
        if self.has_listeners():
            self.fire_events(value)  

    def fire_events(self, value: float):
        self.fire(StatEvents.OBSERVATION_ADDED_EVENT, value)
        self.fire(StatEvents.N_EVENT, self.n())
        self.fire(StatEvents.MIN_EVENT, self.min())
        self.fire(StatEvents.MAX_EVENT, self.max())
        self.fire(StatEvents.WEIGHTED_SUM_EVENT, self.weighted_sum())
        self.fire(StatEvents.WEIGHTED_POPULATION_MEAN_EVENT,
                  self.weighted_population_mean())
        self.fire(StatEvents.WEIGHTED_POPULATION_STDEV_EVENT,
                  self.weighted_population_stdev())
        self.fire(StatEvents.WEIGHTED_POPULATION_VARIANCE_EVENT,
                  self.weighted_population_variance())
        self.fire(StatEvents.WEIGHTED_SAMPLE_MEAN_EVENT,
                  self.weighted_sample_mean())
        self.fire(StatEvents.WEIGHTED_SAMPLE_STDEV_EVENT,
                  self.weighted_sample_stdev())
        self.fire(StatEvents.WEIGHTED_SAMPLE_VARIANCE_EVENT,
                  self.weighted_sample_variance())


class EventBasedTimestampWeightedTally(EventProducer, EventListener,
                                       TimestampWeightedTally):
    
    def __init__(self, name: str):
        EventProducer.__init__(self)
        TimestampWeightedTally.__init__(self, name)
 
    def initialize(self):
        """
        Initialize the statistics object, resetting all values to the state 
        where no observations have been made. This method can, for instance, 
        be called when the warmup period of the simulation experiment has
        completed. 
        """
        TimestampWeightedTally.initialize(self)
        self.fire_initialized()
    
    def fire_initialized(self):
        """Separate method to allow easy overriding of firing the 
        INITIALIZED_EVENT as a TimedEvent."""
        self.fire(StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: TimedEvent):
        if not isinstance(event, TimedEvent):
            raise TypeError(f"event notification {event} for " + \
                            "timestamped tally is not timestamped")
        if not event.event_type == StatEvents.TIMESTAMP_DATA_EVENT:
            raise ValueError(f"notification {event.event_type} for " + \
                             "timestamped tally is not a TIMESTAMP_DATA_EVENT")
        if not (isinstance(event.content, float) or 
                isinstance(event.content, int)):
            raise TypeError(f"notification {event.content} for " + \
                            "timestamped tally: value is not a float or int")
        # float(...) will turn a Duration timestamp into its si-value
        self.ingest(float(event.timestamp), float(event.content))

    def ingest(self, timestamp: float, value: float):
        super().ingest(timestamp, value)
        if self.has_listeners():
            self.fire_events(timestamp, value)  

    def fire_events(self, timestamp: float, value: float):
        self.fire_timed(timestamp, StatEvents.OBSERVATION_ADDED_EVENT, value)
        self.fire_timed(timestamp, StatEvents.N_EVENT, self.n())
        self.fire_timed(timestamp, StatEvents.MIN_EVENT, self.min())
        self.fire_timed(timestamp, StatEvents.MAX_EVENT, self.max())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_SUM_EVENT,
                  self.weighted_sum())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_POPULATION_MEAN_EVENT,
                  self.weighted_population_mean())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_POPULATION_STDEV_EVENT,
                  self.weighted_population_stdev())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_POPULATION_VARIANCE_EVENT,
                  self.weighted_population_variance())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_SAMPLE_MEAN_EVENT,
                  self.weighted_sample_mean())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_SAMPLE_STDEV_EVENT,
                  self.weighted_sample_stdev())
        self.fire_timed(timestamp, StatEvents.WEIGHTED_SAMPLE_VARIANCE_EVENT,
                  self.weighted_sample_variance())

#----------------------------------------------------------------------------
# SIMULATION SPECIFIC STATISTICS
#----------------------------------------------------------------------------


class SimCounter(EventBasedCounter, SimStatisticsInterface):
    
    def __init__(self, key: str, name: str, simulator: SimulatorInterface, *,
                 producer: EventProducer=None, event_type: EventType=None):
        if not isinstance(key, str):
            raise TypeError(f"key {key} is not a str")
        if not isinstance(simulator, SimulatorInterface):
            raise TypeError(f"simulator {simulator} is not a simulator")
        self._simulator = simulator
        EventBasedCounter.__init__(self, name)
        simulator.add_listener(ReplicationInterface.WARMUP_EVENT, self)
        self._key = key
        simulator.model.add_output_statistic(key, self)
        if producer != None or event_type != None:
            self.listen_to(producer, event_type)
        else:
            self._event_type = None

    def listen_to(self, producer: EventProducer, event_type: EventType):
        """
        Avoid chicken-and-egg problem and allow for later registration of
        events to listen to.
        """
        if not isinstance(producer, EventProducer):
            raise TypeError(f"producer {producer} not an EventProducer")
        if not isinstance(event_type, EventType):
            raise TypeError(f"event_type {event_type} not an EventType")
        self._event_type = event_type
        producer.add_listener(event_type, self)

    @property
    def key(self) -> str:
        return self._key
    
    @property
    def simulator(self) -> SimulatorInterface:
        return self._simulator

    def fire_initialized(self):
        self.fire_timed(self.simulator.simulator_time,
                        StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: Event):
        if event.event_type == StatEvents.DATA_EVENT:
            super().notify(event)
        elif event.event_type == self._event_type:
            super().notify(Event(StatEvents.DATA_EVENT, event.content))
        elif event.event_type == ReplicationInterface.WARMUP_EVENT:
            self.initialize()
            
    def fire_events(self, value: float):
        self.fire_timed(self.simulator.simulator_time,
                        StatEvents.OBSERVATION_ADDED_EVENT, value)
        self.fire_timed(self.simulator.simulator_time,
                        StatEvents.N_EVENT, self.n())
        self.fire_timed(self.simulator.simulator_time,
                        StatEvents.COUNT_EVENT, self.count())


class SimTally(EventBasedTally, SimStatisticsInterface):
    
    def __init__(self, key: str, name: str, simulator: SimulatorInterface, *,
                 producer: EventProducer=None, event_type: EventType=None):
        if not isinstance(key, str):
            raise TypeError(f"key {key} is not a str")
        if not isinstance(simulator, SimulatorInterface):
            raise TypeError(f"simulator {simulator} is not a simulator")
        self._simulator = simulator
        EventBasedTally.__init__(self, name)
        simulator.add_listener(ReplicationInterface.WARMUP_EVENT, self)
        self._key = key
        simulator.model.add_output_statistic(key, self)
        if producer != None or event_type != None:
            self.listen_to(producer, event_type)
        else:
            self._event_type = None

    def listen_to(self, producer: EventProducer, event_type: EventType):
        """
        Avoid chicken-and-egg problem and allow for later registration of
        events to listen to.
        """
        if not isinstance(producer, EventProducer):
            raise TypeError(f"producer {producer} not an EventProducer")
        if not isinstance(event_type, EventType):
            raise TypeError(f"event_type {event_type} not an EventType")
        self._event_type = event_type
        producer.add_listener(event_type, self)

    @property
    def key(self) -> str:
        return self._key
    
    @property
    def simulator(self) -> SimulatorInterface:
        return self._simulator

    def fire_initialized(self):
        self.fire_timed(self.simulator.simulator_time,
                        StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: Event):
        if event.event_type == StatEvents.DATA_EVENT:
            super().notify(event)
        elif event.event_type == self._event_type:
            super().notify(Event(StatEvents.DATA_EVENT, event.content))
        elif event.event_type == ReplicationInterface.WARMUP_EVENT:
            self.initialize()
            
    def fire_events(self, value: float):
        t = self.simulator.simulator_time
        self.fire_timed(t, StatEvents.OBSERVATION_ADDED_EVENT, value)
        self.fire_timed(t, StatEvents.N_EVENT, self.n())
        self.fire_timed(t, StatEvents.MIN_EVENT, self.min())
        self.fire_timed(t, StatEvents.MAX_EVENT, self.max())
        self.fire_timed(t, StatEvents.SUM_EVENT, self.sum())
        self.fire_timed(t, StatEvents.POPULATION_MEAN_EVENT,
                        self.population_mean())
        self.fire_timed(t, StatEvents.POPULATION_STDEV_EVENT,
                        self.population_stdev())
        self.fire_timed(t, StatEvents.POPULATION_VARIANCE_EVENT,
                        self.population_variance())
        self.fire_timed(t, StatEvents.POPULATION_SKEWNESS_EVENT,
                        self.population_skewness())
        self.fire_timed(t, StatEvents.POPULATION_KURTOSIS_EVENT,
                        self.population_kurtosis())
        self.fire_timed(t, StatEvents.POPULATION_EXCESS_K_EVENT,
                        self.population_excess_kurtosis())
        self.fire_timed(t, StatEvents.SAMPLE_MEAN_EVENT,
                        self.sample_mean())
        self.fire_timed(t, StatEvents.SAMPLE_STDEV_EVENT,
                        self.sample_stdev())
        self.fire_timed(t, StatEvents.SAMPLE_VARIANCE_EVENT,
                        self.sample_variance())
        self.fire_timed(t, StatEvents.SAMPLE_SKEWNESS_EVENT,
                        self.sample_skewness())
        self.fire_timed(t, StatEvents.SAMPLE_KURTOSIS_EVENT,
                        self.sample_kurtosis())
        self.fire_timed(t, StatEvents.SAMPLE_EXCESS_K_EVENT,
                        self.sample_excess_kurtosis())


class SimPersistent(EventBasedTimestampWeightedTally, SimStatisticsInterface):
    
    def __init__(self, key: str, name: str, simulator: SimulatorInterface, *,
                 producer: EventProducer=None, event_type: EventType=None):
        if not isinstance(key, str):
            raise TypeError(f"key {key} is not a str")
        if not isinstance(simulator, SimulatorInterface):
            raise TypeError(f"simulator {simulator} is not a simulator")
        self._simulator = simulator
        EventBasedTimestampWeightedTally.__init__(self, name)
        simulator.add_listener(ReplicationInterface.WARMUP_EVENT, self)
        simulator.add_listener(ReplicationInterface.END_REPLICATION_EVENT, self)
        self._key = key
        simulator.model.add_output_statistic(key, self)
        if producer != None or event_type != None:
            self.listen_to(producer, event_type)
        else:
            self._event_type = None

    def listen_to(self, producer: EventProducer, event_type: EventType):
        """
        Avoid chicken-and-egg problem and allow for later registration of
        events to listen to.
        """
        if not isinstance(producer, EventProducer):
            raise TypeError(f"producer {producer} not an EventProducer")
        if not isinstance(event_type, EventType):
            raise TypeError(f"event_type {event_type} not an EventType")
        self._event_type = event_type
        producer.add_listener(event_type, self)

    @property
    def key(self) -> str:
        return self._key
    
    @property
    def simulator(self) -> SimulatorInterface:
        return self._simulator

    def fire_initialized(self):
        self.fire_timed(self.simulator.simulator_time,
                        StatEvents.INITIALIZED_EVENT, self)
        
    def notify(self, event: Event):
        if event.event_type == StatEvents.TIMESTAMP_DATA_EVENT:
            super().notify(event)
        elif event.event_type == self._event_type:
            super().notify(TimedEvent(self.simulator.simulator_time,
                    StatEvents.TIMESTAMP_DATA_EVENT, event.content))
        elif event.event_type == ReplicationInterface.WARMUP_EVENT:
            self.initialize()
        elif event.event_type == ReplicationInterface.END_REPLICATION_EVENT:
            self.end_observations(self.simulator.simulator_time)
