import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
import os
from .cleaner import Cleaner
from .analyzer import StatisticAnalyzer
from .visualizer import Visualizer


class Statistic:
    def __init__(self, df: pd.DataFrame, img_dir=""):
        self.df = df
        self.img_dir = img_dir
        if self.img_dir and not os.path.exists(self.img_dir):
            os.makedirs(self.img_dir)
        self.cleaner = Cleaner(self.df)
        self.analyzer = StatisticAnalyzer(self.df)
        self.visualizer = Visualizer(img_dir=img_dir)

    def _save_or_show(self, filename=None):
        """Сохраняет текущий график в img_dir, если задан filename, иначе показывает"""
        if filename and self.img_dir:
            filepath = os.path.join(self.img_dir, filename)
            plt.savefig(filepath, bbox_inches='tight')
            print(f"График сохранён: {filepath}")
        else:
            plt.show()
        plt.close()

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

        skew = self.analyzer.skewness("salary")
        print(f"Асимметрия (salary): {skew:.2f}")
        skew = self.analyzer.skewness("experience")
        print(f"Асимметрия (experience): {skew:.2f}")
        skew = self.analyzer.skewness("monthly_hours")
        print(f"Асимметрия (monthly_hours): {skew:.2f}")

        # Исправлено: одинарные кавычки внутри f-строки
        print(f"Area: {self.df['area'].nunique()}")
        print(f"Employer: {self.df['employer'].nunique()}")

        # Сохраним гистограмму опыта
        self.visualizer.plot_hist(self.df, "experience", filename="experience_hist.png")

    # ---------- Задание 1 ----------
    def zad_1(self):
        """Задание 1: описание переменных и предполагаемые распределения"""
        print("\n" + "=" * 60)
        print("Задание 1.1. Описание датасета")
        print("=" * 60)
        print("Переменные в датасете:")
        for col in self.df.columns:
            dtype = self.df[col].dtype
            nunique = self.df[col].nunique()
            print(f"- {col}: {dtype}, уникальных значений: {nunique}")

        print("\nТаблица с описанием переменных (заполните вручную в отчёте):")
        print("| Название | Тип данных | Краткое описание | Предполагаемый процесс порождения |")
        print("|----------|------------|------------------|-----------------------------------|")
        for col in self.df.columns:
            dtype = self.df[col].dtype
            print(f"| {col} | {dtype} | ... | ... |")

    # ---------- Задание 2 ----------
    def zad_2(self):
        """Задание 2: проверка на нормальность для числовых переменных"""
        print("\n" + "=" * 60)
        print("Задание 2. Проверка на нормальность")
        print("=" * 60)
        candidates = ['salary', 'monthly_hours', 'experience']
        for col in candidates:
            if col not in self.df.columns:
                continue
            data = self.df[col].dropna()
            if len(data) < 10:
                print(f"{col}: недостаточно данных для проверки нормальности")
                continue

            print(f"\n--- {col} ---")

            # Гистограмма
            plt.figure()
            self.df[col].hist(bins=30, edgecolor='black')
            plt.title(f'Гистограмма {col}')
            plt.xlabel(col)
            plt.ylabel('Частота')
            self._save_or_show(filename=f"zad2_hist_{col}.png")

            # Среднее и медиана
            mean_val = data.mean()
            median_val = data.median()
            print(f"Среднее: {mean_val:.2f}, Медиана: {median_val:.2f}")

            # Асимметрия
            skew_val = self.analyzer.skewness(col)
            print(f"Асимметрия: {skew_val:.2f}")

            # Q-Q plot
            plt.figure()
            stats.probplot(data, dist="norm", plot=plt)
            plt.title(f'Q-Q plot для {col}')
            self._save_or_show(filename=f"zad2_qq_{col}.png")

            # Тест на нормальность
            if len(data) <= 5000:
                stat, p = stats.shapiro(data)
                print(f"Тест Шапиро-Уилка: статистика={stat:.4f}, p-value={p:.4f}")
            else:
                stat, p = stats.normaltest(data)
                print(f"Тест Д'Агостино: статистика={stat:.4f}, p-value={p:.4f}")
            if p < 0.05:
                print("Распределение значимо отличается от нормального")
            else:
                print("Нет оснований отвергать нормальность")

    # ---------- Задание 3 ----------
    def zad_3(self):
        exp_counts = self.df['experience'].value_counts().sort_index()
        print(exp_counts)

        plt.bar(exp_counts.index, exp_counts.values, width=0.8, edgecolor='black')
        plt.xlabel('Уровень опыта (код)')
        plt.ylabel('Количество вакансий')
        plt.title('Распределение вакансий по уровням опыта')
        self._save_or_show(filename="zad3_experience_counts.png")

        mean_exp = exp_counts.mean()
        var_exp = exp_counts.var()
        print(f"Среднее = {mean_exp:.2f}, Дисперсия = {var_exp:.2f}")

        index = var_exp / mean_exp
        print(f"Индекс дисперсии = {index:.3f}")

        lambda_pois = mean_exp
        print(f"λ = {lambda_pois:.3f}")

        total_vacancies = exp_counts.sum()
        k_vals = exp_counts.index
        empirical_freq = exp_counts.values
        empirical_prob = empirical_freq / total_vacancies

        poisson_probs = stats.poisson.pmf(k_vals, mu=lambda_pois)
        theoretical_freq = poisson_probs * total_vacancies

        comparison = pd.DataFrame({
            'k': k_vals,
            'Эмпирическая частота': empirical_freq,
            'Эмпирическая вероятность': empirical_prob,
            'Пуассоновская вероятность': poisson_probs,
            'Теоретическая частота': theoretical_freq
        })
        print(comparison)

    # ---------- Задание 4 ----------
    def zad_4(self):
        # Очистка от нулей и отрицательных
        salary_clean = self.df['salary'].dropna()
        salary_clean = salary_clean[salary_clean > 0]
        if len(salary_clean) == 0:
            print("Нет положительных значений зарплаты")
            return

        plt.hist(salary_clean, bins=50, edgecolor='black')
        plt.title('Распределение зарплат')
        plt.xlabel('Зарплата (руб.)')
        plt.ylabel('Частота')
        self._save_or_show(filename="zad4_salary_hist.png")

        plt.hist(np.log(salary_clean), bins=50, edgecolor='black')
        plt.title('Распределение логарифма зарплат')
        plt.xlabel('ln(Зарплата)')
        plt.ylabel('Частота')
        self._save_or_show(filename="zad4_log_salary_hist.png")

        stats.probplot(np.log(salary_clean), dist="norm", plot=plt)
        plt.title('Q-Q plot для ln(salary)')
        self._save_or_show(filename="zad4_qq_log_salary.png")

        stat, p = stats.shapiro(np.log(salary_clean))
        print(f'Статистика Шапиро-Уилка = {stat}, p-value = {p}')

        log_salary = np.log(salary_clean)
        mu = log_salary.mean()
        sigma = log_salary.std()
        print(f'μ = {mu:.3f}, σ = {sigma:.3f}')

    # ---------- Задание 5 ----------
    def cat_summary(self, var):
        counts = self.df[var].value_counts()
        n_total = len(self.df)
        mode_val = counts.idxmax()
        mode_freq = counts.max()
        mode_pct = mode_freq / n_total * 100

        rare_cats = counts[counts / n_total < 0.05]

        print(f"\n--- {var} ---")
        print(f"Количество категорий: {len(counts)}")
        print(f"Мода: {mode_val} (частота = {mode_freq} / {mode_pct:.1f}%)")
        if len(rare_cats) > 0:
            print(f"Редкие категории (<5%): {len(rare_cats)} шт., примеры: {rare_cats.head(3).index.tolist()}")
        else:
            print("Редкие категории (<5%): нет")

    def zad_5(self):
        for var in ['area', 'employer', 'experience']:
            self.cat_summary(var)

        # Проверка равномерности для experience
        obs_exp = self.df['experience'].value_counts().sort_index()
        n_cats = len(obs_exp)
        expected = np.full(n_cats, len(self.df) / n_cats)
        chi2, pval = stats.chisquare(obs_exp, expected)
        print(f"\n--- Проверка равномерности для experience ---")
        print(f"χ² = {chi2:.2f}, p-value = {pval:.4f}")
        if pval < 0.05:
            print("Вердикт: НЕ равномерное")
        else:
            print("Вердикт: равномерное")

        # Гистограмма для experience
        plt.figure(figsize=(8, 5))
        counts = self.df['experience'].value_counts().sort_index()
        plt.bar(counts.index.astype(str), counts.values, edgecolor='black')
        plt.xlabel('Уровень опыта (код)')
        plt.ylabel('Частота')
        plt.title('Распределение опыта (порядковая шкала)')
        self._save_or_show(filename="zad5_exp_bar.png")

        # Boxplots
        plt.figure(figsize=(8, 5))
        sns.boxplot(x='experience', y='salary', data=self.df)
        plt.title('Зарплата по уровню опыта')
        self._save_or_show(filename="zad5_salary_by_exp_box.png")

        top_cities = self.df['area'].value_counts().head(5).index
        df_top = self.df[self.df['area'].isin(top_cities)]
        plt.figure(figsize=(10, 5))
        sns.boxplot(x='area', y='salary', data=df_top)
        plt.xticks(rotation=45)
        plt.title('Зарплата по крупнейшим городам')
        self._save_or_show(filename="zad5_salary_by_city_box.png")

    # ---------- Задание 6 ----------
    def zad_6(self, variable='salary'):
        # Очистка данных
        data = self.df[variable].dropna()
        data = data[data > 0]
        if len(data) == 0:
            print(f"Переменная {variable} не содержит положительных значений")
            return

        print(f"\n=== Детальный анализ переменной: {variable} ===")
        print(f"Количество наблюдений: {len(data)}")

        # Параметры
        log_data = np.log(data)
        mu_log = log_data.mean()
        sigma_log = log_data.std()

        # Гамма
        a_gamma, loc_gamma, scale_gamma = stats.gamma.fit(data, floc=0)

        # Экспоненциальное
        loc_exp, scale_exp = stats.expon.fit(data, floc=0)

        # Визуализация плотностей
        plt.figure(figsize=(12, 6))
        plt.hist(data, bins=50, density=True, alpha=0.5, label='Эмпирические данные')
        x = np.linspace(data.min(), data.max(), 1000)

        plt.plot(x, stats.lognorm.pdf(x, s=sigma_log, scale=np.exp(mu_log)),
                 label='Логнормальное', lw=2)
        plt.plot(x, stats.gamma.pdf(x, a=a_gamma, scale=scale_gamma),
                 label='Гамма', lw=2)
        plt.plot(x, stats.expon.pdf(x, scale=scale_exp),
                 label='Экспоненциальное', lw=2)

        plt.title(f'Сравнение плотностей распределений для {variable}')
        plt.xlabel(variable.capitalize())
        plt.ylabel('Плотность')
        plt.legend()
        plt.xlim(0, data.quantile(0.99))
        self._save_or_show(filename=f"zad6_{variable}_pdf_comparison.png")

        # Вероятности превышения
        median = data.median()
        p90 = data.quantile(0.9)
        p99 = data.quantile(0.99)

        print(f"\nПороги: медиана = {median:.2f}, 90-й перц. = {p90:.2f}, 99-й перц. = {p99:.2f}")

        ln_median = stats.lognorm.sf(median, s=sigma_log, scale=np.exp(mu_log))
        ln_p90 = stats.lognorm.sf(p90, s=sigma_log, scale=np.exp(mu_log))
        ln_p99 = stats.lognorm.sf(p99, s=sigma_log, scale=np.exp(mu_log))

        gamma_median = stats.gamma.sf(median, a=a_gamma, scale=scale_gamma)
        gamma_p90 = stats.gamma.sf(p90, a=a_gamma, scale=scale_gamma)
        gamma_p99 = stats.gamma.sf(p99, a=a_gamma, scale=scale_gamma)

        exp_median = stats.expon.sf(median, scale=scale_exp)
        exp_p90 = stats.expon.sf(p90, scale=scale_exp)
        exp_p99 = stats.expon.sf(p99, scale=scale_exp)

        table_probs = pd.DataFrame({
            'Распределение': ['Эмпирическое', 'Логнормальное', 'Гамма', 'Экспоненциальное'],
            'P(X > медиана)': [0.5, ln_median, gamma_median, exp_median],
            'P(X > 90-й перц.)': [0.1, ln_p90, gamma_p90, exp_p90],
            'P(X > 99-й перц.)': [0.01, ln_p99, gamma_p99, exp_p99]
        })
        print("\nВероятности превышения порогов:")
        print(table_probs.round(4))

        # Критерий Колмогорова-Смирнова
        ks_lognorm = stats.kstest(data, 'lognorm', args=(sigma_log, 0, np.exp(mu_log)))
        ks_gamma = stats.kstest(data, 'gamma', args=(a_gamma, 0, scale_gamma))
        ks_expon = stats.kstest(data, 'expon', args=(0, scale_exp))

        ks_results = pd.DataFrame({
            'Распределение': ['Логнормальное', 'Гамма', 'Экспоненциальное'],
            'Статистика D': [ks_lognorm.statistic, ks_gamma.statistic, ks_expon.statistic],
            'p-value': [ks_lognorm.pvalue, ks_gamma.pvalue, ks_expon.pvalue]
        })
        print("\nКритерий Колмогорова-Смирнова:")
        print(ks_results.round(4))

        # Итоговый вывод
        best = ks_results.loc[ks_results['p-value'].idxmax()]
        print("\n=== ИТОГОВЫЙ ВЫВОД ===")
        print(f"Наилучшее распределение: {best['Распределение']}")
        print(f"Статистика D = {best['Статистика D']:.4f}, p-value = {best['p-value']:.4f}")
        if best['Распределение'] == 'Логнормальное':
            print("Логарифм переменной близок к нормальному распределению, что подтверждается Q-Q plot и тестом Шапиро-Уилка (см. zad_4).")
        elif best['Распределение'] == 'Гамма':
            print("Гамма-распределение гибко и часто используется для моделирования положительных величин с правым скосом.")
        else:
            print("Экспоненциальное распределение является частным случаем гамма-распределения, но редко точно описывает реальные данные.")
        print(f"Практический смысл: распределение {variable} важно для прогнозирования вероятностей превышения ключевых порогов.")
        print("Ограничения: модель предполагает независимость и однородность данных; в реальности могут влиять стратифицирующие факторы (город, опыт и т.д.)")
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