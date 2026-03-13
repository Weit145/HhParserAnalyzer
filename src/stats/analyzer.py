import pandas as pd
import numpy as np


class StatisticAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def skewness(self, col: str):
        return self.df[col].skew()

    def kurtosis(self, col: str):
        return self.df[col].kurtosis()

    def correlation_matrix(self):
        numeric = self.df.select_dtypes(include=[np.number])
        return numeric.corr()

    def group_stats(self, group_col: str, target_col: str):
        return (self.df.groupby(group_col)[target_col].agg(["mean", "median", "std", "count"]).round(2))

    def cross_tab(self, row_var:str, col_var:str ):
        df = self.df
        top_var = df[row_var].value_counts().head(10).index
        top_col = df[col_var].value_counts().head(10).index
        df_top = df[df[row_var].isin(top_var) & df[col_var].isin(top_col)]
        ctab = pd.crosstab(
            df_top[row_var], 
            df_top[col_var], 
            normalize='index',
        ) * 100
        
        print(f"Кросс-табуляция: {row_var} × {col_var}")
        print(ctab.round(2))
        return ctab