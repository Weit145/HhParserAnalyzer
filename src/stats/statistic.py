import pandas as pd
from .cleaner import Cleaner
from .analyzer import StatisticAnalyzer
from .visualizer import Visualizer

class Statistic:
    def __init__(self, df: pd.DataFrame, img_dir=""):
        self.df = df
        self.cleaner = Cleaner(self.df)
        self.analyzer = StatisticAnalyzer(self.df)
        self.visualizer = Visualizer(img_dir=img_dir)

    def __call__(self):
        print(f"Размерность: {self.df.shape}")
        print("\nТипы данных и пропуски:")
        info = pd.DataFrame({
            'Тип': self.df.dtypes,
            'Не пропущено': self.df.count(),
            'Пропущено': self.df.isnull().sum(),
            'Доля пропусков %': (self.df.isnull().sum() / len(self.df) * 100).round(2)
        }) 
        print(info)
        
        print("\nОписательная статистика (числовые переменные):")
        desc = self.df.describe(percentiles=[.01, .05, .1, .25, .5, .75, .9, .95, .99])
        print(desc.round(2))
    
    def run(self, metric:str, group_col:str, scatter_x:str, scatter_y:str, scatter_hue:str, row_var:str, col_var:str):
        print("--- 1. Очистка данных ---")
        self.df = self.cleaner.clean_col_dup(metric)
        self.df = self.cleaner.to_numeric([scatter_x, scatter_y, scatter_hue])
        self.df = self.cleaner.remove_outliers_iqr(metric)
        print("Данные очищены.\n")

        print("--- 2. Статистический анализ ---")
        
        skew = self.analyzer.skewness(metric)
        kurt = self.analyzer.kurtosis(metric)
        print(f"Асимметрия ({metric}): {skew:.2f}")
        print(f"Эксцесс ({metric}): {kurt:.2f}\n")

        print("Корреляционная матрица:")
        corr = self.analyzer.correlation_matrix()
        print(corr.round(2), "\n")

        if group_col:
            print(f"Группировка по {group_col} для {metric}:")
            group_stats = self.analyzer.group_stats(group_col, metric)
            print(group_stats, "\n")
            
        if row_var and col_var:
            print(f"Кросс-табуляция для {row_var} и {col_var}:")
            cross_tab_data = self.analyzer.cross_tab(row_var, col_var)
            print(cross_tab_data, "\n")

        print("--- 3. Визуализация ---")

        self.visualizer.plot_hist(self.df, metric, filename=f"{metric}_hist.png")
        print(f"Гистограмма для '{metric}' сохранена.")

        if group_col:
            self.visualizer.plot_box(self.df, group_col, metric, filename=f"salary_box_by_{group_col}.png")
            print(f"Box plot для '{metric}' по '{group_col}' сохранен.")

        self.visualizer.plot_heatmap(corr, filename="correlation_heatmap.png")
        print("Тепловая карта корреляции сохранена.")

        if scatter_x and scatter_y:
            self.visualizer.plot_scatter(self.df, scatter_x, scatter_y, scatter_hue, filename=f"scatter_{scatter_y}_vs_{scatter_x}.png")
            print(f"Scatter plot для '{scatter_y}' vs '{scatter_x}' сохранен.")
            
        self.visualizer.plot_kde(self.df, metric, filename="KDE.png")
        print(f"KDE plot для '{metric}' сохранен.")

        self.visualizer.plot_violin(self.df, metric, filename="ViolinPlot.png")
        print(f"Violin plot для '{metric}' сохранен.")

        self.visualizer.plot_ecdf(self.df, metric, filename="ECDF.png")
        print(f"ECDF plot для '{metric}' сохранен.")

        if group_col:
            self.visualizer.plot_count(self.df, group_col, filename="CountPlot.png")
            print(f"Count plot для '{group_col}' сохранен.")

        if group_col:
            self.visualizer.plot_pie_chart(self.df, group_col, filename="PieChart.png")
            print(f"Круговая диаграмма для '{group_col}' сохранена.")

        if scatter_x and scatter_y:
            self.visualizer.plot_joint(self.df, scatter_x, scatter_y, filename="Joint.png")
            print(f"Joint plot для '{scatter_y}' vs '{scatter_x}' сохранен.")

        if scatter_x and scatter_y:
            self.visualizer.plot_hexbin(self.df, scatter_x, scatter_y, filename="HexbinPlot.png")
            print(f"Hexbin plot для '{scatter_y}' vs '{scatter_x}' сохранен.")
            
        if row_var and col_var:
            self.visualizer.plot_crosstab_heatmap(cross_tab_data, filename="CrosstabHeatmap.png")
            print(f"Тепловая карта кросс-табуляции для '{row_var}' и '{col_var}' сохранена.")
            
        print("\n--- Анализ завершен ---")