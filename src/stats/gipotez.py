import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os
import warnings
warnings.filterwarnings('ignore')

class Gipotez:
    """
    Класс для выполнения лабораторной работы №4 по проверке статистических гипотез.
    """
    def __init__(self, df, img_dir="img"):
        self.df = df.copy()
        self.img_dir = img_dir
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
        
        # Предварительная обработка
        # salary: пропуски заменяем на NaN, потом будем удалять при необходимости
        self.df['salary'] = pd.to_numeric(self.df['salary'], errors='coerce')
        # Оставим только строки с salary для числовых тестов (если нужно)
        self.df_clean = self.df.dropna(subset=['salary']).copy()
        
        # Определим типы переменных
        self.num_vars = ['salary', 'monthly_hours']
        self.cat_vars = ['area', 'employer', 'experience']
        self.bin_vars = []  # создадим позже
        
        # Для удобства преобразуем experience в категориальный (но это уже int)
        self.df['experience_cat'] = self.df['experience'].astype('category')
        self.df_clean['experience_cat'] = self.df_clean['experience'].astype('category')
        
        # Добавим бинарную переменную: опыт > 0
        self.df['exp_binary'] = (self.df['experience'] > 0).astype(int)
        self.df_clean['exp_binary'] = (self.df_clean['experience'] > 0).astype(int)
        self.bin_vars = ['exp_binary']
        
        # Уровень значимости
        self.alpha = 0.05
        
    def _check_normality(self, variable, group=None):
        """
        Проверка нормальности распределения переменной.
        Возвращает (статистика, p-value, нормально ли на уровне alpha)
        """
        if group is not None:
            data = self.df_clean[self.df_clean[group[0]] == group[1]][variable].dropna()
        else:
            data = self.df_clean[variable].dropna()
        if len(data) < 3:
            return np.nan, np.nan, False
        # Используем тест Шапиро-Уилка (для выборок до 5000)
        if len(data) <= 5000:
            stat, p = stats.shapiro(data)
        else:
            # для больших выборок используем Колмогорова-Смирнова против нормального распределения
            stat, p = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
        normal = p > self.alpha
        return stat, p, normal
    
    def _check_homogeneity(self, group_col, value_col):
        """
        Проверка равенства дисперсий (Левен) для групп.
        """
        groups = [self.df_clean[self.df_clean[group_col]==cat][value_col].dropna().values 
                  for cat in self.df_clean[group_col].unique()]
        groups = [g for g in groups if len(g) > 1]
        if len(groups) < 2:
            return np.nan, np.nan, False
        stat, p = stats.levene(*groups)
        equal = p > self.alpha
        return stat, p, equal
    
    # ========================== ZADANIE 1 ==========================
    def zad_1(self):
        print("\n" + "="*60)
        print("ЗАДАНИЕ 1. Введение в проверку статистических гипотез")
        print("="*60)
        
        # 1.1 Классификация типов гипотез (примеры на основе данных)
        print("\n1.1. Примеры гипотез для данного датасета:")
        examples = {
            "О среднем значении": "Средняя зарплата (salary) равна 80000 руб.",
            "О равенстве средних в двух группах": "Средняя зарплата в Москве и в регионах различается.",
            "О равенстве распределений": "Распределение зарплаты для опыта 0 и опыта 3 одинаково.",
            "О независимости": "Город (area) и уровень опыта (experience) независимы.",
            "О пропорциях": "Доля вакансий с опытом > 0 равна 0.7.",
            "О равенстве пропорций": "Доля вакансий с зарплатой выше медианы в Москве и в Питере одинакова."
        }
        for t, ex in examples.items():
            print(f"  {t}: {ex}")
        
        # 1.2 Исследовательские вопросы
        print("\n1.2. Исследовательские вопросы (формулировка H0 и H1):")
        questions = [
            ("Влияет ли опыт на зарплату?",
             "H0: Средняя зарплата для всех уровней опыта одинакова.",
             "H1: Средняя зарплата различается хотя бы для двух уровней опыта."),
            ("Связаны ли зарплата и количество часов в месяц?",
             "H0: Коэффициент корреляции Пирсона между salary и monthly_hours равен 0.",
             "H1: Коэффициент корреляции отличен от 0."),
            ("Различается ли зарплата в двух самых популярных городах?",
             "H0: Средняя зарплата в г. А и г. Б равна.",
             "H1: Средняя зарплата различается."),
            ("Соответствует ли распределение зарплаты нормальному?",
             "H0: Распределение зарплаты нормальное.",
             "H1: Распределение не является нормальным.")
        ]
        for q, h0, h1 in questions:
            print(f"  Вопрос: {q}\n    {h0}\n    {h1}")
        
        # 1.3 Анализ распределений переменных
        print("\n1.3. Проверка нормальности числовых переменных:")
        table_data = []
        for var in self.num_vars:
            stat, p, normal = self._check_normality(var)
            distrib = "нормальное" if normal else "не нормальное"
            param_ok = "Да" if normal else "Нет (использовать непараметрические)"
            table_data.append([var, "числовая", distrib, param_ok])
            print(f"  {var}: {distrib} (p={p:.4f})")
        
        # Дополнительно проверим распределение опыта как категориальной
        exp_counts = self.df['experience'].value_counts()
        print(f"\n  Распределение опыта (experience):\n{exp_counts}")
        
        # Сохраним гистограммы
        for var in self.num_vars:
            plt.figure(figsize=(8,4))
            sns.histplot(self.df_clean[var].dropna(), kde=True, bins=30)
            plt.title(f'Распределение {var}')
            plt.savefig(os.path.join(self.img_dir, f'zad1_hist_{var}.png'))
            plt.close()
        
        print("\nГрафики сохранены в", self.img_dir)
        
    # ========================== ZADANIE 2 ==========================
    def zad_2(self):
        print("\n" + "="*60)
        print("ЗАДАНИЕ 2. Одновыборочные тесты")
        print("="*60)
        
        # 2.1 Одновыборочный t-тест
        print("\n2.1. Одновыборочный t-тест (средняя зарплата = 80000)")
        mu0 = 80000
        salary_data = self.df_clean['salary'].dropna()
        if len(salary_data) > 1:
            t_stat, p_value = stats.ttest_1samp(salary_data, mu0)
            print(f"  H0: средняя зарплата = {mu0}")
            print(f"  t-статистика = {t_stat:.4f}, p-value = {p_value:.4f}")
            if p_value < self.alpha:
                print(f"  Решение: отвергаем H0. Средняя зарплата значимо отличается от {mu0}.")
            else:
                print(f"  Решение: нет оснований отвергнуть H0. Средняя зарплата может быть равна {mu0}.")
            effect_size = (salary_data.mean() - mu0) / salary_data.std()
            print(f"  Размер эффекта (Cohen's d) = {effect_size:.3f}")
        else:
            print("  Недостаточно данных для t-теста.")
        
        # 2.2 Критерий знаков
        print("\n2.2. Критерий знаков (медиана зарплаты = 70000)")
        m0 = 70000
        n_above = (salary_data > m0).sum()
        n_below = (salary_data < m0).sum()
        n_total = n_above + n_below
        # ИСПРАВЛЕНО:
        binom_res = stats.binomtest(n_above, n_total, p=0.5, alternative='two-sided')
        p_binom = binom_res.pvalue
        print(f"  H0: медиана = {m0}")
        print(f"  Наблюдений выше {m0}: {n_above}, ниже: {n_below}")
        print(f"  p-value (биномиальный тест) = {p_binom:.4f}")
        if p_binom < self.alpha:
            print(f"  Решение: отвергаем H0. Медиана значимо отличается от {m0}.")
        else:
            print(f"  Решение: нет оснований отвергнуть H0. Медиана может быть равна {m0}.")
        
        # 2.3 Проверка пропорции
        print("\n2.3. Биномиальный тест для пропорции (доля вакансий с опытом > 0 = 0.7)")
        p0 = 0.7
        successes = self.df['exp_binary'].sum()
        n = len(self.df['exp_binary'].dropna())
        observed_prop = successes / n
        # ИСПРАВЛЕНО:
        binom_prop = stats.binomtest(successes, n, p=p0, alternative='two-sided')
        p_binom_prop = binom_prop.pvalue
        print(f"  H0: доля = {p0}")
        print(f"  Наблюдаемая доля: {observed_prop:.3f} ({successes}/{n})")
        print(f"  p-value = {p_binom_prop:.4f}")
        if p_binom_prop < self.alpha:
            print(f"  Решение: отвергаем H0. Доля значимо отличается от {p0}.")
        else:
            print(f"  Решение: нет оснований отвергнуть H0.")
    
    # ========================== ZADANIE 3 ==========================
    def zad_3(self):
        print("\n" + "="*60)
        print("ЗАДАНИЕ 3. Гипотезы о сравнении двух групп")
        print("="*60)
        
        # Выберем два города с наибольшим количеством вакансий
        top_areas = self.df_clean['area'].value_counts().head(2).index.tolist()
        if len(top_areas) >= 2:
            area1, area2 = top_areas[0], top_areas[1]
            print(f"\n3.1. Сравнение средних зарплат в городах: {area1} vs {area2}")
            data1 = self.df_clean[self.df_clean['area']==area1]['salary'].dropna()
            data2 = self.df_clean[self.df_clean['area']==area2]['salary'].dropna()
            if len(data1)>1 and len(data2)>1:
                # Проверка равенства дисперсий
                stat_levene, p_levene, equal_var = self._check_homogeneity('area', 'salary')
                print(f"  Равенство дисперсий (Levene): p={p_levene:.4f}, равны={equal_var}")
                # t-тест (Стьюдента или Уэлча)
                t_stat, p_val = stats.ttest_ind(data1, data2, equal_var=equal_var)
                print(f"  t-статистика = {t_stat:.4f}, p-value = {p_val:.4f}")
                if p_val < self.alpha:
                    print(f"  Решение: отвергаем H0. Средние зарплаты различаются.")
                else:
                    print(f"  Решение: нет оснований отвергнуть H0.")
                # Размер эффекта Коэна d
                pooled_std = np.sqrt((np.var(data1, ddof=1) + np.var(data2, ddof=1))/2)
                cohen_d = (data1.mean() - data2.mean()) / pooled_std
                print(f"  Cohen's d = {cohen_d:.3f}")
                
                # 3.2 Непараметрический тест Манна-Уитни
                print("\n3.2. Тест Манна-Уитни (сравнение распределений)")
                u_stat, p_mw = stats.mannwhitneyu(data1, data2, alternative='two-sided')
                print(f"  U-статистика = {u_stat:.1f}, p-value = {p_mw:.4f}")
                if p_mw < self.alpha:
                    print("  Решение: распределения различаются значимо.")
                else:
                    print("  Решение: нет значимых различий в распределениях.")
            else:
                print("  Недостаточно данных для сравнения.")
        else:
            print("  Недостаточно городов для сравнения двух групп.")
        
        # 3.3 Парный тест (если есть естественные пары – в данном датасете нет)
        print("\n3.3. Парный тест: в датасете нет явных парных наблюдений (до/после, одинаковые объекты).")
        print("  Поэтому парный t-тест не выполняется.")
        
        # 3.4 Сравнение двух пропорций (бинарная переменная exp_binary по городам)
        if len(top_areas) >= 2:
            print(f"\n3.4. Сравнение долей опыта >0 между {area1} и {area2}")
            # Таблица сопряженности
            cross = pd.crosstab(self.df[self.df['area'].isin([area1, area2])]['area'], 
                                self.df[self.df['area'].isin([area1, area2])]['exp_binary'])
            if cross.shape == (2,2):
                chi2, p_chi, dof, expected = stats.chi2_contingency(cross)
                print(f"  Таблица сопряженности:\n{cross}")
                print(f"  χ² = {chi2:.4f}, p-value = {p_chi:.4f}")
                if p_chi < self.alpha:
                    print("  Решение: доли значимо различаются.")
                else:
                    print("  Решение: нет оснований считать доли различными.")
                # Мера связи V Крамера
                n_total = cross.sum().sum()
                cramer_v = np.sqrt(chi2 / (n_total * (min(cross.shape)-1)))
                print(f"  V Крамера = {cramer_v:.3f}")
    
    # ========================== ZADANIE 4 ==========================
    def zad_4(self):
        print("\n" + "="*60)
        print("ЗАДАНИЕ 4. Связь между переменными")
        print("="*60)
        
        # 4.1 Корреляция между salary и monthly_hours
        print("\n4.1. Связь между зарплатой и месячными часами")
        data_corr = self.df_clean[['salary', 'monthly_hours']].dropna()
        if len(data_corr) > 2:
            # Пирсон
            r_pearson, p_pearson = stats.pearsonr(data_corr['salary'], data_corr['monthly_hours'])
            print(f"  Корреляция Пирсона: r = {r_pearson:.4f}, p-value = {p_pearson:.4f}")
            if p_pearson < self.alpha:
                print("  Связь статистически значима.")
                if abs(r_pearson) < 0.3: strength = "слабая"
                elif abs(r_pearson) < 0.7: strength = "умеренная"
                else: strength = "сильная"
                print(f"  Сила связи: {strength}")
            else:
                print("  Связь статистически не значима.")
            # Спирмен
            r_spearman, p_spearman = stats.spearmanr(data_corr['salary'], data_corr['monthly_hours'])
            print(f"  Корреляция Спирмена: ρ = {r_spearman:.4f}, p-value = {p_spearman:.4f}")
            # Диаграмма рассеяния
            plt.figure(figsize=(8,6))
            sns.scatterplot(data=data_corr, x='monthly_hours', y='salary')
            plt.title('Зависимость зарплаты от месячных часов')
            plt.savefig(os.path.join(self.img_dir, 'zad4_scatter.png'))
            plt.close()
        else:
            print("  Недостаточно данных для корреляционного анализа.")
        
        # 4.2 Связь между категориальной (experience) и непрерывной (salary) – ANOVA
        print("\n4.2. ANOVA: зависимость зарплаты от уровня опыта")
        exp_groups = [self.df_clean[self.df_clean['experience']==lev]['salary'].dropna().values 
                      for lev in sorted(self.df_clean['experience'].unique())]
        exp_groups = [g for g in exp_groups if len(g) > 0]
        if len(exp_groups) >= 2:
            f_stat, p_anova = stats.f_oneway(*exp_groups)
            print(f"  F-статистика = {f_stat:.4f}, p-value = {p_anova:.4f}")
            if p_anova < self.alpha:
                print("  Результат: средние зарплаты для разных уровней опыта значимо различаются.")
                # Размер эффекта η²
                ss_between = sum(len(g)*(g.mean() - self.df_clean['salary'].mean())**2 for g in exp_groups)
                ss_total = sum((self.df_clean['salary'] - self.df_clean['salary'].mean())**2)
                eta_sq = ss_between / ss_total
                print(f"  η² (эта-квадрат) = {eta_sq:.3f}")
            else:
                print("  Нет значимых различий средних зарплат по опыту.")
        else:
            print("  Недостаточно групп для ANOVA.")
        
        # 4.3 Связь между двумя категориальными переменными (area и experience)
        print("\n4.3. χ²-тест независимости между городом (area) и опытом (experience)")
        # Ограничимся топ-5 городов для наглядности
        top_areas = self.df_clean['area'].value_counts().head(5).index
        data_cat = self.df_clean[self.df_clean['area'].isin(top_areas)]
        cross = pd.crosstab(data_cat['area'], data_cat['experience'])
        if cross.shape[0] > 1 and cross.shape[1] > 1:
            chi2, p_chi, dof, expected = stats.chi2_contingency(cross)
            print(f"  Таблица {cross.shape[0]}x{cross.shape[1]}")
            print(f"  χ² = {chi2:.4f}, p-value = {p_chi:.4f}")
            if p_chi < self.alpha:
                print("  Переменные зависимы (связаны) статистически значимо.")
                # V Крамера
                n_total = cross.sum().sum()
                cramer_v = np.sqrt(chi2 / (n_total * (min(cross.shape)-1)))
                print(f"  V Крамера = {cramer_v:.3f}")
            else:
                print("  Нет оснований отвергнуть независимость.")
        else:
            print("  Недостаточно категорий для построения таблицы сопряженности.")
        
        # Сохраним тепловую карту корреляции
        corr_matrix = self.df_clean[['salary', 'monthly_hours']].corr()
        plt.figure(figsize=(6,5))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
        plt.title('Корреляционная матрица')
        plt.savefig(os.path.join(self.img_dir, 'zad4_corr_heatmap.png'))
        plt.close()
    
    # ========================== ZADANIE 5 ==========================
    def zad_5(self):
        print("\n" + "="*60)
        print("ЗАДАНИЕ 5. Сравнение распределений и проверка однородности")
        print("="*60)
        
        # 5.1 Сравнение распределений зарплаты в двух группах (по опыту: 0 и 3)
        print("\n5.1. Сравнение распределений зарплаты для опыта 0 и опыта 3")
        exp0 = self.df_clean[self.df_clean['experience']==0]['salary'].dropna()
        exp3 = self.df_clean[self.df_clean['experience']==3]['salary'].dropna()
        if len(exp0)>1 and len(exp3)>1:
            # Визуализация: ящики с усами
            plt.figure(figsize=(8,5))
            data_box = [exp0, exp3]
            plt.boxplot(data_box, labels=['Опыт 0', 'Опыт 3'])
            plt.title('Сравнение зарплат по опыту')
            plt.ylabel('Зарплата')
            plt.savefig(os.path.join(self.img_dir, 'zad5_salary_by_exp_box.png'))
            plt.close()
            
            # Критерий Колмогорова-Смирнова
            ks_stat, p_ks = stats.ks_2samp(exp0, exp3)
            print(f"  KS-статистика = {ks_stat:.4f}, p-value = {p_ks:.4f}")
            if p_ks < self.alpha:
                print("  Распределения значимо различаются (по форме).")
            else:
                print("  Нет значимых различий в распределениях.")
            
            # Сравнение с t-тестом и Манна-Уитни
            t_stat, p_t = stats.ttest_ind(exp0, exp3)
            u_stat, p_mw = stats.mannwhitneyu(exp0, exp3)
            print(f"  t-тест p={p_t:.4f}, Mann-Whitney p={p_mw:.4f}")
        else:
            print("  Недостаточно данных для сравнения групп опыта 0 и 3.")
        
        # 5.2 Сравнение с теоретическим распределением (нормальное для зарплаты)
        print("\n5.2. Сравнение распределения зарплаты с нормальным")
        salary_all = self.df_clean['salary'].dropna()
        if len(salary_all) > 5:
            # Критерий Колмогорова-Смирнова против нормального распределения с параметрами выборки
            ks_stat, p_ks = stats.kstest(salary_all, 'norm', args=(salary_all.mean(), salary_all.std()))
            print(f"  KS-тест против нормального: статистика = {ks_stat:.4f}, p-value = {p_ks:.4f}")
            if p_ks < self.alpha:
                print("  Распределение значимо отличается от нормального.")
            else:
                print("  Нет оснований отвергать нормальность.")
            # Дополнительно: критерий Андерсона-Дарлинга
            anderson_res = stats.anderson(salary_all, dist='norm')
            print(f"  Андерсона-Дарлинга: статистика = {anderson_res.statistic:.3f}")
            print(f"  Критические значения: {anderson_res.critical_values}")
            print(f"  Уровни значимости: {anderson_res.significance_level}")
            # Гистограмма с нормальной кривой
            plt.figure(figsize=(8,5))
            sns.histplot(salary_all, kde=True, stat='density', bins=30, label='Эмпирическая')
            x = np.linspace(salary_all.min(), salary_all.max(), 100)
            plt.plot(x, stats.norm.pdf(x, salary_all.mean(), salary_all.std()), 'r-', label='Нормальное')
            plt.legend()
            plt.title('Сравнение с нормальным распределением')
            plt.savefig(os.path.join(self.img_dir, 'zad5_norm_comparison.png'))
            plt.close()
        
        # Построим bar chart для experience (как в примере пользователя)
        print("\n  Построение bar chart для experience:")
        exp_counts = self.df['experience'].value_counts().sort_index()
        plt.figure(figsize=(8,5))
        exp_counts.plot(kind='bar', color='skyblue')
        plt.title('Распределение уровня опыта')
        plt.xlabel('Опыт (0 - без опыта, 3 - более 3 лет)')
        plt.ylabel('Частота')
        plt.xticks(rotation=0)
        plt.savefig(os.path.join(self.img_dir, 'zad5_exp_bar.png'))
        plt.close()
        # Также ящик с усами по городам (топ-5)
        top_cities = self.df_clean['area'].value_counts().head(5).index
        data_city_box = [self.df_clean[self.df_clean['area']==city]['salary'].dropna() for city in top_cities]
        plt.figure(figsize=(10,6))
        plt.boxplot(data_city_box, labels=top_cities)
        plt.title('Зарплата по городам')
        plt.ylabel('Зарплата')
        plt.xticks(rotation=45)
        plt.savefig(os.path.join(self.img_dir, 'zad5_salary_by_city_box.png'))
        plt.close()
        print("  Графики сохранены.")
    
    # ========================== ZADANIE 6 ==========================
    def zad_6(self):
        print("\n" + "="*60)
        print("ЗАДАНИЕ 6. Формулирование гипотез и выбор критерия")
        print("="*60)
        
        # 6.1 Алгоритм выбора критерия для исследовательских вопросов (из zad1)
        print("\n6.1. Алгоритм выбора критерия для ранее сформулированных вопросов:")
        questions = [
            ("Влияет ли опыт на зарплату?", "числовая (salary)", "категориальная (experience, 4 группы)", "независимые", "ANOVA (если нормальность и гомогенность) иначе Крускала-Уоллиса"),
            ("Связаны ли зарплата и часы?", "числовая", "числовая", "-", "корреляция Пирсона/Спирмена"),
            ("Различается ли зарплата в двух городах?", "числовая", "категориальная (2 города)", "независимые", "t-тест или Манна-Уитни"),
            ("Соответствует ли зарплата нормальному распределению?", "числовая", "-", "-", "Колмогорова-Смирнова, Андерсона-Дарлинга")
        ]
        for q, var1, var2, dep, test in questions:
            print(f"  Вопрос: {q}\n    Переменные: {var1}, {var2}\n    Зависимость: {dep}\n    Рекомендуемый критерий: {test}\n")
        
        # 6.2 Сравнение нескольких групп (ANOVA) уже выполнено в zad4, но повторим с post-hoc
        print("\n6.2. Дисперсионный анализ (ANOVA) с post-hoc (Тьюки)")
        exp_groups = [self.df_clean[self.df_clean['experience']==lev]['salary'].dropna().values 
                      for lev in sorted(self.df_clean['experience'].unique())]
        exp_groups = [g for g in exp_groups if len(g) > 1]
        if len(exp_groups) >= 3:
            f_stat, p_anova = stats.f_oneway(*exp_groups)
            print(f"  ANOVA: F={f_stat:.4f}, p={p_anova:.4f}")
            if p_anova < self.alpha:
                print("  H0 отвергается. Проведём post-hoc Тьюки:")
                # Подготовка данных для pairwise_tukeyhsd (нужна библиотека statsmodels)
                try:
                    from statsmodels.stats.multicomp import pairwise_tukeyhsd
                    data_long = []
                    groups_long = []
                    for lev in sorted(self.df_clean['experience'].unique()):
                        vals = self.df_clean[self.df_clean['experience']==lev]['salary'].dropna()
                        data_long.extend(vals)
                        groups_long.extend([lev]*len(vals))
                    tukey = pairwise_tukeyhsd(data_long, groups_long, alpha=self.alpha)
                    print(tukey)
                except ImportError:
                    print("  statsmodels не установлен, post-hoc не выполнен.")
            else:
                print("  ANOVA не показал различий, post-hoc не требуется.")
        else:
            print("  Недостаточно групп для полноценного ANOVA (нужно >=3).")
        
        # 6.3 Непараметрическая альтернатива (Крускала-Уоллиса)
        print("\n6.3. Критерий Крускала-Уоллиса (непараметрический аналог ANOVA)")
        if len(exp_groups) >= 3:
            h_stat, p_kw = stats.kruskal(*exp_groups)
            print(f"  H-статистика = {h_stat:.4f}, p-value = {p_kw:.4f}")
            if p_kw < self.alpha:
                print("  Распределения зарплат по уровням опыта значимо различаются.")
            else:
                print("  Нет значимых различий.")
        else:
            print("  Недостаточно групп.")
        
        # 6.4 Создание шпаргалки
        print("\n6.4. Шпаргалка по выбору критериев для предметной области (IT-вакансии):")
        cheat_sheet = """
        | Задача                                    | Тип данных                          | Критерий                           |
        |-------------------------------------------|-------------------------------------|------------------------------------|
        | Средняя зарплата = константе              | числовая, нормальная                | Одновыборочный t-тест              |
        | Медиана зарплаты = константе               | числовая, любая                     | Критерий знаков                    |
        | Доля вакансий с опытом >0 = 0.7            | бинарная                            | Биномиальный тест                  |
        | Сравнение зарплат в двух городах           | числовая, независимые группы        | t-тест (Уэлча) или Манна-Уитни     |
        | Влияет ли опыт на зарплату? (>=3 групп)    | числовая + категориальная            | ANOVA или Крускала-Уоллиса         |
        | Связь зарплаты и часов                     | две числовые                        | Корреляция Пирсона/Спирмена        |
        | Связь города и опыта                       | две категориальные                  | χ²-тест, V Крамера                 |
        | Распределение зарплаты нормальное?         | числовая                            | KS-тест, Андерсона-Дарлинга        |
        """
        print(cheat_sheet)
        
        print("\n  Чаще всего используемые критерии: t-тест, Манна-Уитни, ANOVA, корреляция Пирсона, χ².")
        print("  Перед применением параметрических тестов проверять нормальность и гомогенность дисперсий.")
        print("  При нарушении предположений использовать непараметрические аналоги.")
    
    # Если нужно выполнить все задания последовательно
    def run_all(self):
        self.zad_1()
        self.zad_2()
        self.zad_3()
        self.zad_4()
        self.zad_5()
        self.zad_6()

# Пример использования:
if __name__ == "__main__":
    # Загрузка данных (предполагается, что файл Python.csv лежит в data/api/)
    df = pd.read_csv("data/api/Python.csv", sep=';', encoding='utf-8-sig')
    st = Statistic(df, img_dir="img/api/Python")
    st.run_all()