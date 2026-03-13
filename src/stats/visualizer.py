import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

class Visualizer:

    def __init__(self, img_dir=""):
        self.img_dir = img_dir

        if img_dir and not os.path.exists(img_dir):
            os.makedirs(img_dir)

    def _save(self, filename):
        plt.savefig(os.path.join(self.img_dir, filename), dpi=300)
        plt.close()
    

    def plot_hist(self, df: pd.DataFrame, col: str, filename: str = "hist.png"):
        plt.figure(figsize=(10,6))
        sns.histplot(df[col], kde=True)
        
        mean_val = df[col].mean()
        median_val = df[col].median()
        plt.axvline(mean_val, color='red', linestyle='--', label=f'Среднее: {mean_val:.0f}')
        plt.axvline(median_val, color='green', linestyle='-', label=f'Медиана: {median_val:.0f}')
        
        plt.title(f'Распределение {col}')
        plt.xlabel(col)
        
        plt.ylabel('Частота')
        plt.legend()
        plt.tight_layout()
        self._save(f"{col}_{filename}")
    
    def plot_box(self, df: pd.DataFrame, x: str, y: str, filename: str = "box.png"):
        plt.figure(figsize=(10,6))
        sns.boxplot(x=x, y=y, data=df)
        plt.title(f'Распределение {y} по {x}')
        plt.tight_layout()
        self._save(f"{y}_{x}_{filename}")

    def plot_heatmap(self, corr: pd.DataFrame, filename: str = "heatmap.png"):
        plt.figure(figsize=(10,6))
        sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, square=True, fmt='.2f')
        plt.title('Корреляционная матрица')
        plt.tight_layout()
        self._save(f"{filename}")

    def plot_scatter(self, df: pd.DataFrame, x: str, y: str, hue: str, filename: str = "scatter.png"):
        plt.figure(figsize=(10,6))
        sns.scatterplot(x=x, y=y, hue=hue, data=df, palette='viridis', alpha=0.6)
        plt.title(f'{y} от {x} (цвет — {hue})')
        plt.legend(title=hue)
        plt.tight_layout()
        self._save(f"{filename}")

    def plot_kde(self, df: pd.DataFrame,col:str , filename: str = "KDE.png"):
        plt.figure(figsize=(10,6))
        sns.kdeplot(df[col], fill=True)
        plt.title('Ядерная оценка плотности')
        plt.tight_layout()
            
        
    def plot_violin(self, df: pd.DataFrame,col:str , filename: str = "ViolinPlot.png"):
        plt.figure(figsize=(10,6))
        sns.violinplot(x=df[col])
        plt.title('Violin Plot')
        plt.tight_layout()
        self._save(f"{filename}")
        
    def plot_ecdf(self, df: pd.DataFrame,col:str , filename: str = "ECDF.png"):
        plt.figure(figsize=(10,6))
        sns.ecdfplot(df[col])
        plt.title('ECDF')
        plt.tight_layout()
        self._save(f"{filename}")
    
    def plot_count(self, df: pd.DataFrame,col:str , filename: str = "CountPlot.png", mx: int = 5):
        top_col = df[col].value_counts().head(mx).index
        df_top = df[ df[col].isin(top_col)]
        plt.figure(figsize=(10,6))
        sns.countplot(y=df_top[col])
        plt.title('CountPlot ')
        plt.tight_layout()
        self._save(f"{filename}")
    
    def plot_pie_chart(self, df: pd.DataFrame,col:str , filename: str = "PieChart.png", mx: int = 5):
        top_col = df[col].value_counts().head(mx).index
        df_top = df[ df[col].isin(top_col)]
        plt.figure(figsize=(10,6))
        df_top[col].value_counts().plot.pie()
        plt.title('PieChart')
        plt.tight_layout()
        self._save(f"{filename}")
    
    def plot_word_cloud(self, df: pd.DataFrame,col:str , filename: str = "PieChart.png", mx: int = 5):
        top_col = df[col].value_counts().head(mx).index
        df_top = df[ df[col].isin(top_col)]
        plt.figure(figsize=(10,6))
        df_top[col].value_counts().plot.pie()
        plt.title('PieChart')
        plt.tight_layout()
        self._save(f"{filename}")
        
    def plot_joint(self, df: pd.DataFrame,col1:str,col2:str, filename: str = "Joint.png"):
        plt.figure(figsize=(10,6))
        sns.jointplot(x=col1, y=col2, data=df, kind='scatter')
        plt.title('Joint')
        plt.tight_layout()
        self._save(f"{filename}")
        
    def plot_hexbin(self, df: pd.DataFrame,col1:str,col2:str, filename: str = "HexbinPlot.png"):
        plt.figure(figsize=(10,6))
        df.plot.hexbin(x=col1, y=col2, gridsize=20)
        plt.title('HexbinPlot')
        plt.tight_layout()
        self._save(f"{filename}")
    
    def plot_line(self, df: pd.DataFrame,time:str,value:str, filename: str = "LinePlot.png"):
        plt.figure(figsize=(10,6))
        sns.lineplot(x=time, y=value, data=df)
        plt.title('LinePlot')
        plt.tight_layout()
        self._save(f"{filename}")
        
    def plot_crosstab_heatmap(self, ctab, filename: str = "CrosstabHeatmap.png"):
        plt.figure(figsize=(12, max(6, len(ctab)//2)))
        sns.heatmap(ctab, annot=True, fmt='.1f', cmap='YlOrRd')
        plt.savefig(os.path.join(self.img_dir, filename), dpi=300, bbox_inches='tight')