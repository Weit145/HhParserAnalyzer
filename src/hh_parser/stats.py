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
        
        print("\nОписательная статистика (числовые переменные):")
        desc = self.original_df.describe(percentiles=[.01, .05, .1, .25, .5, .75, .9, .95, .99])
        print(desc.round(2))
    
    def cross_tab(self, df: pd.DataFrame = None, row_var:str = "area", col_var:str = "experience", plot:bool = True,filename: str = "cross_tab"):
        if df is None:
            df = self.original_df
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
        
        if plot:
            plt.figure(figsize=(12, max(6, len(ctab)//2)))
            sns.heatmap(ctab, annot=True, fmt='.1f', cmap='YlOrRd')
            plt.title(f'{row_var} vs {col_var} (%)')
            plt.ylabel(row_var)
            plt.xlabel(col_var)
            plt.savefig(os.path.join(self.img_dir, filename), dpi=300, bbox_inches='tight')
        
        
    def categorical_cols(self, df: pd.DataFrame = None):
        if df is None:
            df = self.original_df
        categor_cols = df.select_dtypes(include=["object"]).columns
        for col in categor_cols:
            print(f"\n=== {col} ===")
            print(f"Уникальных значений: {df[col].nunique()}")
            print(f"Самые частые значения (топ-5):")
            print(df[col].value_counts().head())
            print(f"Доля самого частого значения: {(df[col].value_counts().iloc[0] / len(df)) * 100:.2f}%")


    
    def check_null(self,df: pd.DataFrame = None ,missing:str = "salary", where: str = "area"):
        if df is None:
            df = self.original_df
        mis = df[df[missing].isnull()]
        print(f"{where} с пропущенной {missing}: ")
        print(mis[where].value_counts(normalize=True))
        print(f"Все {where}: ")
        print(df[where].value_counts(normalize=True))
        

    def run(self, metric: str, group_col: str = "", scatter_x: str = "", 
            scatter_y: str = "", scatter_hue: str = ""):
        df = self.clean(metric)
        df = self.to_numeric(df, [scatter_x, scatter_y, scatter_hue])
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


    # def clean(self, metric: str) -> pd.DataFrame:
    #     df = self.original_df.copy()
    #     df = df.dropna(subset=[metric])
    #     df = df.drop_duplicates()
    #     return df


    # def to_numeric(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
    #     for col in columns:
    #         if col and col in df.columns:
    #             df[col] = pd.to_numeric(df[col], errors="coerce")
    #     return df
    
    # def remove_outliers_iqr(self, df: pd.DataFrame, col: str) -> pd.DataFrame:
    #     Q1 = df[col].quantile(0.25)
    #     Q3 = df[col].quantile(0.75)
    #     IQR = Q3 - Q1
    #     lower = Q1 - 1.5 * IQR
    #     upper = Q3 + 1.5 * IQR
    #     return df[(df[col] >= lower) & (df[col] <= upper)]

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
        
    def plot_kde(self, df: pd.DataFrame,col:str , filename: str = "KDE.png"):
        plt.figure(figsize=(10,6))
        sns.kdeplot(df[col], fill=True)
        plt.title('Ядерная оценка плотности')
        plt.tight_layout()
        plt.savefig(os.path.join(self.img_dir, filename), dpi=300)
        plt.close()
        
    def plot_violin(self, df: pd.DataFrame,col:str , filename: str = "ViolinPlot.png"):
        plt.figure(figsize=(10,6))
        sns.violinplot(x=df[col])
        plt.title('Violin Plot')
        plt.tight_layout()
        plt.savefig(os.path.join(self.img_dir, filename), dpi=300)
        plt.close()
    
    def plot_ecdf(self, df: pd.DataFrame,col:str , filename: str = "ECDF.png"):
        plt.figure(figsize=(10,6))
        sns.ecdfplot(df[col])
        plt.title('ECDF')
        plt.tight_layout()
        plt.savefig(os.path.join(self.img_dir, filename), dpi=300)
        plt.close()
    
    def plot_count(self, df: pd.DataFrame,col:str , filename: str = "CountPlot.png", mx: int = 5):
        top_col = df[col].value_counts().head(mx).index
        df_top = df[ df[col].isin(top_col)]
        plt.figure(figsize=(10,6))
        sns.countplot(y=df_top[col])
        plt.title('CountPlot ')
        plt.tight_layout()
        plt.savefig(os.path.join(self.img_dir, filename), dpi=300)
        plt.close()
        
    def plot_pie_chart(self, df: pd.DataFrame,col:str , filename: str = "PieChart.png", mx: int = 5):
        top_col = df[col].value_counts().head(mx).index
        df_top = df[ df[col].isin(top_col)]
        plt.figure(figsize=(10,6))
        df_top[col].value_counts().plot.pie()
        plt.title('PieChart')
        plt.tight_layout()
        plt.savefig(os.path.join(self.img_dir, filename), dpi=300)
        plt.close()
    
    def plot_word_cloud(self, df: pd.DataFrame,col:str , filename: str = "PieChart.png", mx: int = 5):
        top_col = df[col].value_counts().head(mx).index
        df_top = df[ df[col].isin(top_col)]
        plt.figure(figsize=(10,6))
        df_top[col].value_counts().plot.pie()
        plt.title('PieChart')
        plt.tight_layout()
        plt.savefig(os.path.join(self.img_dir, filename), dpi=300)
        plt.close()
    
    def plot_joint(self, df: pd.DataFrame,col1:str,col2:str, filename: str = "Joint.png"):
        plt.figure(figsize=(10,6))
        sns.jointplot(x=col1, y=col2, data=df, kind='scatter')
        plt.title('Joint')
        plt.tight_layout()
        plt.savefig(os.path.join(self.img_dir, filename), dpi=300)
        plt.close()
    
    def plot_hexbin(self, df: pd.DataFrame,col1:str,col2:str, filename: str = "HexbinPlot.png"):
        plt.figure(figsize=(10,6))
        df.plot.hexbin(x=col1, y=col2, gridsize=20)
        plt.title('HexbinPlot')
        plt.tight_layout()
        plt.savefig(os.path.join(self.img_dir, filename), dpi=300)
        plt.close()
        
    def plot_line(self, df: pd.DataFrame,time:str,value:str, filename: str = "LinePlot.png"):
        plt.figure(figsize=(10,6))
        sns.lineplot(x=time, y=value, data=df)
        plt.title('LinePlot')
        plt.tight_layout()
        plt.savefig(os.path.join(self.img_dir, filename), dpi=300)
        plt.close()