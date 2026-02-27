import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

class Statistic:
    def __init__(self, df: pd.DataFrame, img_dir: str = ""):

        self.original_df = df.copy()
        self.img_dir = img_dir
        if img_dir and not os.path.exists(img_dir):
            os.makedirs(img_dir, exist_ok=True)

    def __call__(self):
        print(f"Размерность: {self.original_df.shape}")
        print("\nТипы данных и пропуски:")
        info = pd.DataFrame({
            'Тип': self.original_df.dtypes,
            'Не пропущено': self.original_df.count(),
            'Пропущено': self.original_df.isnull().sum(),
            'Доля пропусков %': (self.original_df.isnull().sum() / len(self.original_df) * 100).round(2)
        })
        print(info)

    def run(self, metric: str, group_col: str = "", scatter_x: str = "", 
            scatter_y: str = "", scatter_hue: str = ""):
        df = self.clean(metric)
        df = self.to_numeric(df, ['salary', 'experience', 'responses'])
        df = self.remove_outliers_iqr(df, metric)


        skew = self.skewness(df, metric)
        kurt = self.kurtosis(df, metric)
        print(f"\nАсимметрия {metric}: {skew:.2f}")
        print(f"Эксцесс {metric}: {kurt:.2f}")

        corr = self.correlation_matrix(df)

        self.plot_hist(df, metric, f"{metric}_hist.png")
        if group_col!="":
            self.plot_box(df, group_col, metric, f"{metric}_box_by_{group_col}.png")
        self.plot_heatmap(corr, "correlation_heatmap.png")
        if scatter_x!="" and scatter_y!="" and scatter_hue!="":
            self.plot_scatter(df, scatter_x, scatter_y, scatter_hue, f"scatter_{scatter_x}_{scatter_y}.png")
    

    def clean(self, metric: str) -> pd.DataFrame:
        df = self.original_df.copy()
        df = df.dropna(subset=[metric])
        df = df.drop_duplicates()
        return df


    def to_numeric(self, df:pd.DataFrame, columns: list)->pd.DataFrame:
        for col in columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    
    def remove_outliers_iqr(self, df: pd.DataFrame, col: str) -> pd.DataFrame:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        return df[(df[col] >= lower) & (df[col] <= upper)]

    def group_stats(self, df: pd.DataFrame, group_col: str, target_col: str) -> pd.DataFrame:
                return df.groupby(group_col)[target_col].agg(['mean', 'median', 'std', 'count']).round(2)
    

    def skewness(self, df: pd.DataFrame, col: str) -> float:
        return df[col].skew()

    def kurtosis(self, df: pd.DataFrame, col: str) -> float:
        return df[col].kurtosis()
    
    def correlation_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        numeric = df.select_dtypes(include=[np.number]).columns
        return df[numeric].corr()

    
    def plot_hist(self, df: pd.DataFrame, col: str, filename: str = "hist.png"):
        plt.figure(figsize=(10,5))
        sns.histplot(df[col], kde=True, bins=30, color='skyblue', edgecolor='black')
        mean_val = df[col].mean()
        median_val = df[col].median()
        plt.axvline(mean_val, color='red', linestyle='--', label=f'Среднее: {mean_val:.0f}')
        plt.axvline(median_val, color='green', linestyle='-', label=f'Медиана: {median_val:.0f}')
        plt.title(f'Распределение {col}')
        plt.xlabel(col)
        plt.ylabel('Частота')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(self.img_dir, filename), dpi=300)
        plt.close()

    def plot_box(self, df: pd.DataFrame, x: str, y: str, filename: str = "box.png"):
        plt.figure(figsize=(8,5))
        sns.boxplot(x=x, y=y, data=df)
        plt.title(f'Распределение {y} по {x}')
        plt.tight_layout()
        plt.savefig(os.path.join(self.img_dir, filename), dpi=300)
        plt.close()

    def plot_heatmap(self, corr: pd.DataFrame, filename: str = "heatmap.png"):
        plt.figure(figsize=(8,6))
        sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, square=True, fmt='.2f')
        plt.title('Корреляционная матрица')
        plt.tight_layout()
        plt.savefig(os.path.join(self.img_dir, filename), dpi=300)
        plt.close()
    
    def plot_scatter(self, df: pd.DataFrame, x: str, y: str, hue: str, filename: str = "scatter.png"):
        plt.figure(figsize=(10,6))
        sns.scatterplot(x=x, y=y, hue=hue, data=df, palette='viridis', alpha=0.6)
        plt.title(f'{y} от {x} (цвет — {hue})')
        plt.legend(title=hue)
        plt.tight_layout()
        plt.savefig(os.path.join(self.img_dir, filename), dpi=300)
        plt.close()