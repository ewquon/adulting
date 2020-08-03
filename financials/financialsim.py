import pandas as pd

class RegularTransfer(object):
    def __init__(self,from_acct,to_acct,amount,interval,
                 biweekly_offset=0,biweekly_day=0):
        self.from_acct = from_acct
        self.to_acct = to_acct
        self.amount = amount
        try:
            interval = int(interval)
        except ValueError:
            if interval == 'biweekly':
                assert biweekly_offset in (0,1)
                self.biweekly_offset = biweekly_offset
                assert biweekly_day in range(7)
                self.biweekly_day = biweekly_day
            else:
                interval = getattr(pd.tseries.offsets, interval)
        self.interval = interval

    def update(self,date):
        make_payment = False
        if self.interval == 'biweekly':
            if (date.dayofweek == self.biweekly_day) and (date.week % 2 == self.biweekly_offset):
                make_payment = True
        elif isinstance(self.interval,int):
            if date.day == self.interval:
                make_payment = True
        else:
            target_date = date + self.compound_offset(0)
            if date == target_date:
                make_payment = True
        if make_payment:
            print(date,'transfer',self.amount)
            if not isinstance(self.from_acct,str):
                self.from_acct.withdraw(date,self.amount,self.to_acct)
            if not isinstance(self.to_acct,str):
                self.to_acct.deposit(date,self.amount,self.from_acct)
        

class FinancialSimulation(object):
    """Container class for accounts"""
    def __init__(self,*accts):
        acctnames = [acct.name for acct in accts]
        assert len(acctnames) == len(set(acctnames)), \
                'Names given to accounts not unique: '+str(acctnames)
        self.accounts = {acct.name: acct for acct in accts}
        self.scheduled_payments = []

    def regular_transfer(self,from_acct,to_acct,amount,interval,
                         biweekly_offset=0,biweekly_day=0):
        """
        Parameters
        ----------
        from_acct,to_acct : str
            Account names associated with an Account class instance
        amount : float
            Amount to transfer
        interval : int or str
            Integer day of month, pandas timeseries offset string (e.g.,
            "MonthEnd"--see `pandas.tseries.offsets`), or "biweekly"
        biweekly_offset : int, optional
            If interval is "biweekly", this allows specifying even
            (default) or odd weeks with 0 or 1, respectively
        biweekly_day : int, optional
            If interval is "biweekly", this allows specifying the day of
            th week (0 is monday)
        """
        if from_acct in self.accounts.keys():
            from_acct = self.accounts[from_acct]
        if to_acct in self.accounts.keys():
            to_acct = self.accounts[to_acct]
        self.scheduled_payments.append(
            RegularTransfer(from_acct,to_acct,
                            amount,interval,
                            biweekly_offset,biweekly_day)
        )

    def run(self,years=30,cleanup=True):
        startdate = pd.to_datetime('now').round('D')
        enddate = startdate + pd.to_timedelta(years*365,unit='D')
        tseries = pd.date_range(startdate,enddate,freq='D',name='date')
        self.t = tseries
        for name, acct in self.accounts.items():
            acct.init(self.t)
        # loop over all times
        for date in self.t:
            # first, update all accounts
            for name, acct in self.accounts.items():
                acct.update(date)
            # second, make all scheduled transfers
            for transfer in self.scheduled_payments:
                transfer.update(date)
        # clean up dataframes
        if cleanup:
            for name, acct in self.accounts.items():
                acct.finalize()



