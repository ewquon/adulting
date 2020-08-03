import pandas as pd

class FinancialSimulation(object):
    """Container class for accounts"""
    def __init__(self,*accts):
        acctnames = [acct.name for acct in accts]
        assert len(acctnames) == len(set(acctnames)), \
                'Names given to accounts not unique: '+str(acctnames)
        self.accounts = {acct.name: acct for acct in accts}

    def run(self,years=30,cleanup=True):
        startdate = pd.to_datetime('now').round('D')
        enddate = startdate + pd.to_timedelta(years*365,unit='D')
        tseries = pd.date_range(startdate,enddate,freq='D',name='date')
        self.t = tseries
        for name, acct in self.accounts.items():
            acct.init(self.t)
        # loop over all times
        for date in self.t:
            for name, acct in self.accounts.items():
                acct.update(date)
        # clean up dataframes
        if cleanup:
            for name, acct in self.accounts.items():
                acct.finalize()



