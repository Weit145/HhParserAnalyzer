import pandas as pd


class Cleaner:
    def __init__(self, df: pd.DataFrame):
        self.df = df
    
    def clean_col_dup(self, column: str = None) -> pd.DataFrame:
        if column is not None:
            self.df = self.df.dropna(subset=[column])
        self.df = self.df.drop_duplicates()
        return self.df

    def to_numeric(self, columns: list) -> pd.DataFrame:
        for col in columns:
            if col and col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
        return self.df
    
    def remove_outliers_iqr(self, column: str) -> pd.DataFrame:
        Q1 = self.df[column].quantile(0.25)
        Q3 = self.df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        return self.df[(self.df[column] >= lower) & (self.df[column] <= upper)]