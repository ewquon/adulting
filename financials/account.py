import numpy as np
import pandas as pd

def get_num_periods(compound_on):
    if isinstance(compound_on,int) or compound_on=='MonthEnd':
        N = 12
    else:
        offset = getattr(pd.tseries.offsets,compound_on)
        N = len(pd.date_range('2000-01-01','2000-12-31',freq=offset(1)))
    return N

class Account(object):
    """Account with compounding interest"""
    def __init__(self, name, balance, interest_rate=0,
                 compound_on=1,
                 verbose=True):
        """
        Parameters
        ----------
        name : str
            Identifier for account
        balance : float
            Starting balance
        interest_rate : float
            Fixed interest rate [%]
        compound_on : int or str
            Integer day of month or pandas timeseries offset string
            (e.g., "MonthEnd")--see `pandas.tseries.offsets`
        """
        self.name = name
        self.init_balance = balance
        assert interest_rate >= 0, 'Interest rate [%] should be >= 0.0'
        self.interest_rate = interest_rate
        try:
            self.compound_on_day = int(compound_on)
        except ValueError:
            self.compound_offset = getattr(pd.tseries.offsets, compound_on)
            self.compound_on_day = None
        self.verbose = verbose # DEBUG

    def init(self,tseries):
        self.last_update = tseries[0]
        self.df = pd.DataFrame(index=tseries,
                               columns=['balance','deposit_from','withdrawal_to'])
        self.df.loc[tseries[0],'balance'] = self.init_balance

    def update(self,date):
        if self.interest_rate == 0:
            return
        compound_interest = False
        if self.compound_on_day is None:
            # update based on pandas tseries offset
            target_date = date + self.compound_offset(0)
            if date == target_date:
                compound_interest = True
        elif date.day == self.compound_on_day:
            # update based on integer day
            compound_interest = True
        if compound_interest:
            current_balance = self.df.loc[self.last_update,'balance']
            self.df.loc[date,'balance'] = current_balance*(1+self.interest_rate/100)
            if self.verbose:
                print(date,'update balance of',self.name)
            self.last_update = date

    def finalize(self):
        self.df = self.df.dropna(how='all')


class Savings(Account):
    def __init__(self,name,balance,APY,compound_on=1):
        """
        Parameters
        ----------
        name : str
            Identifier for account
        balance : float
            Starting balance
        APY : float
            Annual percentage yield [%]
        compound_on : int or str
            Integer day of month or pandas timeseries offset string
            (e.g., "MonthEnd")--see `pandas.tseries.offsets`
        """
        N = get_num_periods(compound_on)
        interest_rate = 100 * ((1+APY/100)**(1.0/N) - 1)
        super().__init__(name,balance,interest_rate,compound_on)
        if self.verbose:
            print('calculated annual periods for APY interest rate:',N)
            print(f'calculated interest rate = {self.interest_rate:g}%')


class Loan(Account):
    """Loan with annual percentage rate"""
    def __init__(self,name,balance,interest_rate,compound_on=1):
        """
        Parameters
        ----------
        name : str
            Identifier for account
        balance : float
            Starting balance
        interest_rate : float
            Fixed interest rate [%]
        compound_on : int or str
            Integer day of month or pandas timeseries offset string
            (e.g., "MonthEnd")--see `pandas.tseries.offsets`
        """
        assert balance < 0, 'debt should have a negative balance'
        N = get_num_periods(compound_on)
        interest_rate_per_period = interest_rate / N
        super().__init__(name,balance,interest_rate_per_period,compound_on)

    def init(self,tseries):
        self.last_update = tseries[0]
        self.df = pd.DataFrame(index=tseries,
                               columns=['principal','interest_paid','interest_due','deposit_from'])
        self.df.loc[tseries[0],'principal'] = self.init_balance
        self.df.loc[tseries[0],'interest_due'] = 0.0

    def update(self,date):
        if self.interest_rate == 0:
            return
        compound_interest = False
        if self.compound_on_day is None:
            # update based on pandas tseries offset
            target_date = date + self.compound_offset(0)
            if date == target_date:
                compound_interest = True
        elif date.day == self.compound_on_day:
            # update based on integer day
            compound_interest = True
        if compound_interest:
            current_principal = self.df.loc[self.last_update,'principal']
            self.df.loc[date,'principal'] = current_principal
            self.df.loc[date,'interest_due'] = current_principal*self.interest_rate/100
            if self.verbose:
                print(date,'update interest due for',self.name)
            self.last_update = date
        if self.df.loc[self.last_update,'principal'] >= 0:
            print(date,':',self.name,'paid off!')
            # stop updating
            self.interest_rate = 0
        elif self.df.loc[self.last_update,'principal'] > 0:
            self.df.loc[self.last_update,'principal'] = 0
            if self.verbose:
                print(date,':',self.name,'is already paid off! Zeroing principal')
        
