import os
import re
import warnings
from itertools import combinations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

warnings.filterwarnings("ignore")


class AnovaLab5:
    """
    Класс для выполнения лабораторной работы №5 по теме:
    «Дисперсионный анализ (ANOVA): сравнение нескольких групп».

    По умолчанию класс рассчитан на тот же датасет IT-вакансий, что и в ЛР4:
    salary, monthly_hours, experience, area, employer.

    Основные возможности:
    - групповые статистики;
    - проверка нормальности в группах;
    - проверка гомогенности дисперсий;
    - однофакторный ANOVA;
    - Welch ANOVA при неравенстве дисперсий;
    - post-hoc Tukey HSD;
    - критерий Крускала-Уоллиса;
    - post-hoc Dunn с коррекциями Bonferroni/Holm;
    - двухфакторный ANOVA;
    - график взаимодействия;
    - расчет eta^2, omega^2, Cohen's f;
    - сохранение графиков и таблиц.
    """

    def __init__(self, df, img_dir="img/lab5", table_dir="tables/lab5", alpha=0.05):
        self.df = df.copy()
        self.img_dir = img_dir
        self.table_dir = table_dir
        self.alpha = alpha
        self.results = {}

        os.makedirs(self.img_dir, exist_ok=True)
        os.makedirs(self.table_dir, exist_ok=True)

        # Приведение ключевых переменных к удобному виду.
        for col in ["salary", "monthly_hours", "experience"]:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")

        # experience в этой работе рассматривается как фактор, а не как непрерывная переменная.
        if "experience" in self.df.columns:
            self.df["experience_cat"] = self.df["experience"].astype("category")

        # Основная очищенная таблица для анализа salary.
        if "salary" in self.df.columns:
            self.df_clean = self.df.dropna(subset=["salary"]).copy()
        else:
            self.df_clean = self.df.copy()

        self.num_vars = [col for col in ["salary", "monthly_hours"] if col in self.df.columns]
        self.cat_vars = [col for col in ["experience", "area", "employer"] if col in self.df.columns]

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------
    def _safe_name(self, value):
        """Безопасное имя для файлов."""
        value = str(value)
        value = re.sub(r"[^A-Za-zА-Яа-я0-9_\-]+", "_", value)
        return value[:80]

    def _save_table(self, df, filename):
        """Сохраняет таблицу в CSV."""
        path = os.path.join(self.table_dir, filename)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return path

    def _p(self, p_value):
        """Красивый вывод p-value."""
        if pd.isna(p_value):
            return "nan"
        if p_value < 0.0001:
            return "< 0.0001"
        return f"{p_value:.4f}"

    def _decision(self, p_value, reject_text="H0 отвергается", keep_text="Нет оснований отвергнуть H0"):
        if pd.isna(p_value):
            return "Недостаточно данных"
        return reject_text if p_value < self.alpha else keep_text

    def _require_columns(self, columns):
        missing = [col for col in columns if col not in self.df_clean.columns]
        if missing:
            raise ValueError(f"В датасете нет обязательных столбцов: {missing}")

    def _prepare_factor_data(self, factor, value, top_n=None, min_group_size=2):
        """
        Возвращает датафрейм только с нужными столбцами.
        Если top_n указан, оставляет top_n самых частых категорий фактора.
        """
        self._require_columns([factor, value])
        data = self.df_clean[[factor, value]].dropna().copy()

        if top_n is not None:
            top_values = data[factor].value_counts().head(top_n).index
            data = data[data[factor].isin(top_values)].copy()

        counts = data[factor].value_counts()
        good_groups = counts[counts >= min_group_size].index
        data = data[data[factor].isin(good_groups)].copy()

        return data

    def _get_groups(self, factor, value, top_n=None, min_group_size=2):
        data = self._prepare_factor_data(factor, value, top_n=top_n, min_group_size=min_group_size)
        group_names = list(data[factor].dropna().unique())
        group_names = sorted(group_names, key=lambda x: str(x))
        groups = [data.loc[data[factor] == group, value].dropna().values for group in group_names]
        return data, group_names, groups

    def _group_stats(self, factor="experience", value="salary", top_n=None):
        data = self._prepare_factor_data(factor, value, top_n=top_n, min_group_size=1)

        table = (
            data.groupby(factor)[value]
            .agg(n="count", mean="mean", std="std", median="median", min="min", max="max")
            .reset_index()
        )
        table["sem"] = table["std"] / np.sqrt(table["n"])
        table["ci95_low"] = table["mean"] - 1.96 * table["sem"]
        table["ci95_high"] = table["mean"] + 1.96 * table["sem"]

        total_row = pd.DataFrame({
            factor: ["Всего"],
            "n": [data[value].count()],
            "mean": [data[value].mean()],
            "std": [data[value].std()],
            "median": [data[value].median()],
            "min": [data[value].min()],
            "max": [data[value].max()],
            "sem": [data[value].std() / np.sqrt(data[value].count())],
            "ci95_low": [data[value].mean() - 1.96 * data[value].std() / np.sqrt(data[value].count())],
            "ci95_high": [data[value].mean() + 1.96 * data[value].std() / np.sqrt(data[value].count())],
        })
        table = pd.concat([table, total_row], ignore_index=True)
        return table

    def _check_normality_by_group(self, factor="experience", value="salary", top_n=None):
        data, group_names, groups = self._get_groups(factor, value, top_n=top_n, min_group_size=3)
        rows = []

        for group_name, values in zip(group_names, groups):
            values = pd.Series(values).dropna()
            n = len(values)
            if n < 3:
                stat, p_value, conclusion = np.nan, np.nan, "Недостаточно данных"
            elif n <= 5000:
                stat, p_value = stats.shapiro(values)
                conclusion = "нормально" if p_value > self.alpha else "не нормально"
            else:
                stat, p_value = stats.kstest(values, "norm", args=(values.mean(), values.std(ddof=1)))
                conclusion = "нормально" if p_value > self.alpha else "не нормально"

            rows.append({
                "group": group_name,
                "n": n,
                "test": "Shapiro-Wilk" if n <= 5000 else "Kolmogorov-Smirnov",
                "statistic": stat,
                "p_value": p_value,
                "normality": conclusion,
            })

        return pd.DataFrame(rows)

    def _check_homogeneity(self, factor="experience", value="salary", top_n=None):
        _, group_names, groups = self._get_groups(factor, value, top_n=top_n, min_group_size=2)
        groups = [np.asarray(group, dtype=float) for group in groups if len(group) >= 2]

        if len(groups) < 2:
            return {
                "levene_stat": np.nan,
                "levene_p": np.nan,
                "bartlett_stat": np.nan,
                "bartlett_p": np.nan,
                "equal_var": False,
                "groups_count": len(groups),
            }

        levene_stat, levene_p = stats.levene(*groups, center="median")
        bartlett_stat, bartlett_p = stats.bartlett(*groups)

        return {
            "levene_stat": levene_stat,
            "levene_p": levene_p,
            "bartlett_stat": bartlett_stat,
            "bartlett_p": bartlett_p,
            "equal_var": levene_p > self.alpha,
            "groups_count": len(groups),
        }

    def _anova_manual(self, factor="experience", value="salary", top_n=None):
        data, group_names, groups = self._get_groups(factor, value, top_n=top_n, min_group_size=2)
        groups = [np.asarray(group, dtype=float) for group in groups if len(group) >= 2]

        if len(groups) < 2:
            raise ValueError("Для ANOVA нужно минимум 2 группы с достаточным числом наблюдений.")

        all_values = np.concatenate(groups)
        grand_mean = all_values.mean()
        k = len(groups)
        n_total = len(all_values)

        ss_between = sum(len(group) * (group.mean() - grand_mean) ** 2 for group in groups)
        ss_within = sum(((group - group.mean()) ** 2).sum() for group in groups)
        ss_total = ss_between + ss_within

        df_between = k - 1
        df_within = n_total - k
        df_total = n_total - 1

        ms_between = ss_between / df_between
        ms_within = ss_within / df_within
        f_stat = ms_between / ms_within
        p_value = stats.f.sf(f_stat, df_between, df_within)

        eta_sq = ss_between / ss_total if ss_total != 0 else np.nan
        omega_sq = ((ss_between - df_between * ms_within) / (ss_total + ms_within)) if (ss_total + ms_within) != 0 else np.nan
        omega_sq = max(0, omega_sq) if not pd.isna(omega_sq) else np.nan
        cohen_f = np.sqrt(eta_sq / (1 - eta_sq)) if eta_sq < 1 else np.inf

        table = pd.DataFrame([
            {
                "source": "Межгрупповая / Factor",
                "SS": ss_between,
                "df": df_between,
                "MS": ms_between,
                "F": f_stat,
                "p_value": p_value,
            },
            {
                "source": "Внутригрупповая / Error",
                "SS": ss_within,
                "df": df_within,
                "MS": ms_within,
                "F": np.nan,
                "p_value": np.nan,
            },
            {
                "source": "Общая / Total",
                "SS": ss_total,
                "df": df_total,
                "MS": np.nan,
                "F": np.nan,
                "p_value": np.nan,
            },
        ])

        return {
            "data": data,
            "group_names": group_names,
            "groups": groups,
            "anova_table": table,
            "F": f_stat,
            "p_value": p_value,
            "df_between": df_between,
            "df_within": df_within,
            "ss_between": ss_between,
            "ss_within": ss_within,
            "ss_total": ss_total,
            "ms_between": ms_between,
            "ms_within": ms_within,
            "eta_sq": eta_sq,
            "omega_sq": omega_sq,
            "cohen_f": cohen_f,
        }

    def _welch_anova(self, factor="experience", value="salary", top_n=None):
        _, group_names, groups = self._get_groups(factor, value, top_n=top_n, min_group_size=2)
        clean_groups = []
        clean_names = []

        for name, group in zip(group_names, groups):
            group = np.asarray(group, dtype=float)
            group = group[~np.isnan(group)]
            if len(group) >= 2 and np.var(group, ddof=1) > 0:
                clean_groups.append(group)
                clean_names.append(name)

        if len(clean_groups) < 2:
            return {"F": np.nan, "p_value": np.nan, "df1": np.nan, "df2": np.nan}

        k = len(clean_groups)
        n = np.array([len(group) for group in clean_groups], dtype=float)
        means = np.array([group.mean() for group in clean_groups], dtype=float)
        variances = np.array([group.var(ddof=1) for group in clean_groups], dtype=float)

        weights = n / variances
        weighted_mean = np.sum(weights * means) / np.sum(weights)

        df1 = k - 1
        numerator = np.sum(weights * (means - weighted_mean) ** 2) / df1
        correction_sum = np.sum(((1 - weights / np.sum(weights)) ** 2) / (n - 1))
        denominator = 1 + (2 * (k - 2) / (k ** 2 - 1)) * correction_sum
        f_stat = numerator / denominator
        df2 = (k ** 2 - 1) / (3 * correction_sum) if correction_sum > 0 else np.inf
        p_value = stats.f.sf(f_stat, df1, df2)

        return {
            "F": f_stat,
            "p_value": p_value,
            "df1": df1,
            "df2": df2,
            "groups": clean_names,
        }

    def _tukey_hsd(self, factor="experience", value="salary", top_n=None):
        data = self._prepare_factor_data(factor, value, top_n=top_n, min_group_size=2)

        try:
            from statsmodels.stats.multicomp import pairwise_tukeyhsd
        except ImportError:
            print("  statsmodels не установлен, Tukey HSD не выполнен.")
            return None

        tukey = pairwise_tukeyhsd(
            endog=data[value].astype(float),
            groups=data[factor].astype(str),
            alpha=self.alpha,
        )

        result = pd.DataFrame(
            tukey._results_table.data[1:],
            columns=tukey._results_table.data[0]
        )
        return result

    def _dunn_posthoc(self, factor="experience", value="salary", top_n=None, correction="holm"):
        """
        Реализация post-hoc сравнения Данна после Крускала-Уоллиса.
        correction: 'holm', 'bonferroni' или None.
        """
        data = self._prepare_factor_data(factor, value, top_n=top_n, min_group_size=2)
        data = data[[factor, value]].dropna().copy()
        data["rank"] = stats.rankdata(data[value].astype(float), method="average")

        # Поправка на совпадающие ранги.
        _, tie_counts = np.unique(data[value].astype(float), return_counts=True)
        n_total = len(data)
        tie_correction = 1.0
        if n_total > 1:
            tie_correction -= np.sum(tie_counts ** 3 - tie_counts) / (n_total ** 3 - n_total)
        tie_correction = max(tie_correction, 1e-12)

        grouped = data.groupby(factor).agg(
            n=(value, "count"),
            mean_rank=("rank", "mean"),
            mean_value=(value, "mean"),
        )

        rows = []
        for g1, g2 in combinations(grouped.index, 2):
            n1 = grouped.loc[g1, "n"]
            n2 = grouped.loc[g2, "n"]
            r1 = grouped.loc[g1, "mean_rank"]
            r2 = grouped.loc[g2, "mean_rank"]

            se = np.sqrt((n_total * (n_total + 1) / 12.0) * (1 / n1 + 1 / n2) * tie_correction)
            z_stat = (r1 - r2) / se if se != 0 else np.nan
            p_raw = 2 * stats.norm.sf(abs(z_stat)) if not pd.isna(z_stat) else np.nan

            rows.append({
                "group_1": g1,
                "group_2": g2,
                "mean_rank_1": r1,
                "mean_rank_2": r2,
                "z": z_stat,
                "p_raw": p_raw,
            })

        result = pd.DataFrame(rows)
        if result.empty:
            return result

        p_values = result["p_raw"].values.astype(float)
        m = len(p_values)

        if correction == "bonferroni":
            result["p_adj"] = np.minimum(p_values * m, 1.0)
            result["correction"] = "Bonferroni"
        elif correction == "holm":
            order = np.argsort(p_values)
            adjusted = np.empty(m)
            previous = 0
            for rank, idx in enumerate(order):
                value_adj = (m - rank) * p_values[idx]
                value_adj = max(value_adj, previous)
                adjusted[idx] = min(value_adj, 1.0)
                previous = adjusted[idx]
            result["p_adj"] = adjusted
            result["correction"] = "Holm"
        else:
            result["p_adj"] = p_values
            result["correction"] = "none"

        result["significant"] = result["p_adj"] < self.alpha
        return result

    def _kruskal(self, factor="experience", value="salary", top_n=None):
        _, group_names, groups = self._get_groups(factor, value, top_n=top_n, min_group_size=2)
        groups = [np.asarray(group, dtype=float) for group in groups if len(group) >= 2]

        if len(groups) < 2:
            return {"H": np.nan, "p_value": np.nan, "df": np.nan}

        h_stat, p_value = stats.kruskal(*groups)
        return {
            "H": h_stat,
            "p_value": p_value,
            "df": len(groups) - 1,
            "group_names": group_names,
        }

    def _effect_size_interpretation(self, eta_sq):
        if pd.isna(eta_sq):
            return "нельзя оценить"
        if eta_sq < 0.01:
            return "очень слабое влияние"
        if eta_sq < 0.06:
            return "слабое влияние"
        if eta_sq < 0.14:
            return "среднее влияние"
        return "сильное влияние"

    # ------------------------------------------------------------------
    # Графики
    # ------------------------------------------------------------------
    def _plot_boxplot(self, factor="experience", value="salary", top_n=None, filename=None):
        data = self._prepare_factor_data(factor, value, top_n=top_n, min_group_size=1)
        if filename is None:
            filename = f"boxplot_{self._safe_name(value)}_by_{self._safe_name(factor)}.png"
        path = os.path.join(self.img_dir, filename)

        plt.figure(figsize=(10, 6))
        sns.boxplot(data=data, x=factor, y=value)
        plt.title(f"Распределение {value} по группам {factor}")
        plt.xlabel(factor)
        plt.ylabel(value)
        plt.xticks(rotation=35)
        plt.tight_layout()
        plt.savefig(path, dpi=200)
        plt.close()
        return path

    def _plot_means_ci(self, factor="experience", value="salary", top_n=None, filename=None):
        data = self._prepare_factor_data(factor, value, top_n=top_n, min_group_size=1)
        stats_table = self._group_stats(factor, value, top_n=top_n)
        stats_table = stats_table[stats_table[factor] != "Всего"].copy()

        if filename is None:
            filename = f"means_ci_{self._safe_name(value)}_by_{self._safe_name(factor)}.png"
        path = os.path.join(self.img_dir, filename)

        x = np.arange(len(stats_table))
        y = stats_table["mean"].astype(float).values
        yerr = 1.96 * stats_table["sem"].astype(float).values

        plt.figure(figsize=(10, 6))
        plt.errorbar(x, y, yerr=yerr, fmt="o", capsize=5)
        plt.xticks(x, stats_table[factor].astype(str), rotation=35)
        plt.title(f"Средние значения {value} с 95% доверительными интервалами")
        plt.xlabel(factor)
        plt.ylabel(value)
        plt.tight_layout()
        plt.savefig(path, dpi=200)
        plt.close()
        return path

    def _plot_qq_by_group(self, factor="experience", value="salary", top_n=None, max_groups=6):
        data, group_names, groups = self._get_groups(factor, value, top_n=top_n, min_group_size=3)
        paths = []

        for group_name, values in list(zip(group_names, groups))[:max_groups]:
            values = pd.Series(values).dropna().astype(float)
            if len(values) < 3:
                continue

            filename = f"qq_{self._safe_name(value)}_{self._safe_name(factor)}_{self._safe_name(group_name)}.png"
            path = os.path.join(self.img_dir, filename)

            plt.figure(figsize=(6, 6))
            stats.probplot(values, dist="norm", plot=plt)
            plt.title(f"Q-Q plot: {value}, {factor}={group_name}")
            plt.tight_layout()
            plt.savefig(path, dpi=200)
            plt.close()
            paths.append(path)

        return paths

    def _plot_posthoc_heatmap(self, posthoc_table, filename="posthoc_pvalues_heatmap.png"):
        if posthoc_table is None or posthoc_table.empty:
            return None

        if "p-adj" in posthoc_table.columns:
            g1_col, g2_col, p_col = "group1", "group2", "p-adj"
        elif "p_adj" in posthoc_table.columns:
            g1_col, g2_col, p_col = "group_1", "group_2", "p_adj"
        else:
            return None

        groups = sorted(set(posthoc_table[g1_col].astype(str)) | set(posthoc_table[g2_col].astype(str)))
        matrix = pd.DataFrame(np.nan, index=groups, columns=groups)
        for _, row in posthoc_table.iterrows():
            g1 = str(row[g1_col])
            g2 = str(row[g2_col])
            p = float(row[p_col])
            matrix.loc[g1, g2] = p
            matrix.loc[g2, g1] = p
        np.fill_diagonal(matrix.values, 1.0)

        path = os.path.join(self.img_dir, filename)
        plt.figure(figsize=(9, 7))
        sns.heatmap(matrix, annot=True, fmt=".3f", vmin=0, vmax=1)
        plt.title("Post-hoc p-values")
        plt.tight_layout()
        plt.savefig(path, dpi=200)
        plt.close()
        return path

    def _plot_interaction(self, factor_a="experience", factor_b="area", value="salary", top_n_b=5):
        data = self.df_clean[[factor_a, factor_b, value]].dropna().copy()
        if top_n_b is not None:
            top_b = data[factor_b].value_counts().head(top_n_b).index
            data = data[data[factor_b].isin(top_b)].copy()

        means = data.groupby([factor_a, factor_b])[value].mean().reset_index()
        filename = f"interaction_{self._safe_name(value)}_{self._safe_name(factor_a)}_{self._safe_name(factor_b)}.png"
        path = os.path.join(self.img_dir, filename)

        plt.figure(figsize=(10, 6))
        sns.lineplot(data=means, x=factor_a, y=value, hue=factor_b, marker="o")
        plt.title(f"График взаимодействия: {factor_a} × {factor_b}")
        plt.xlabel(factor_a)
        plt.ylabel(f"Среднее {value}")
        plt.xticks(rotation=25)
        plt.tight_layout()
        plt.savefig(path, dpi=200)
        plt.close()
        return path

    # ------------------------------------------------------------------
    # ЗАДАНИЯ ЛР5
    # ------------------------------------------------------------------
    def zad_1(self, factor="experience", value="salary", top_n=None):
        print("\n" + "=" * 70)
        print("ЗАДАНИЕ 1. Введение в дисперсионный анализ")
        print("=" * 70)

        print("\n1.1. Переменные, которые можно использовать для ANOVA:")
        variables = pd.DataFrame([
            {
                "Категориальная переменная": "experience",
                "Количество категорий": self.df["experience"].nunique() if "experience" in self.df.columns else np.nan,
                "Числовая переменная": "salary",
                "Гипотетический вопрос": "Различается ли средняя зарплата между уровнями опыта?",
            },
            {
                "Категориальная переменная": "area",
                "Количество категорий": self.df["area"].nunique() if "area" in self.df.columns else np.nan,
                "Числовая переменная": "salary",
                "Гипотетический вопрос": "Различается ли средняя зарплата между городами?",
            },
            {
                "Категориальная переменная": "employer",
                "Количество категорий": self.df["employer"].nunique() if "employer" in self.df.columns else np.nan,
                "Числовая переменная": "salary",
                "Гипотетический вопрос": "Различается ли средняя зарплата между работодателями?",
            },
        ])
        print(variables.to_string(index=False))
        self._save_table(variables, "zad1_anova_variables.csv")

        print("\n1.2. Исследовательские вопросы для датасета:")
        questions = [
            "Различается ли средняя salary между уровнями experience?",
            "Различается ли средняя salary между крупнейшими городами area?",
            "Есть ли совместное влияние experience и area на salary?",
        ]
        for idx, question in enumerate(questions, start=1):
            print(f"  {idx}. {question}")

        print(f"\n1.3. Групповые статистики для {value} по фактору {factor}:")
        stats_table = self._group_stats(factor=factor, value=value, top_n=top_n)
        print(stats_table.round(3).to_string(index=False))
        self._save_table(stats_table, "zad1_group_statistics.csv")

        self.results["zad1_group_stats"] = stats_table
        return stats_table

    def zad_2(self, factor="experience", value="salary", top_n=None):
        print("\n" + "=" * 70)
        print("ЗАДАНИЕ 2. Проверка предположений ANOVA")
        print("=" * 70)

        print("\n2.1. Проверка нормальности внутри групп:")
        normality_table = self._check_normality_by_group(factor=factor, value=value, top_n=top_n)
        print(normality_table.round(4).to_string(index=False))
        self._save_table(normality_table, "zad2_normality_by_group.csv")

        qq_paths = self._plot_qq_by_group(factor=factor, value=value, top_n=top_n)
        print(f"  Q-Q plots сохранены: {len(qq_paths)} файл(ов).")

        print("\n2.2. Проверка гомогенности дисперсий:")
        homogeneity = self._check_homogeneity(factor=factor, value=value, top_n=top_n)
        print(f"  H0: дисперсии во всех группах равны")
        print(f"  Levene statistic = {homogeneity['levene_stat']:.4f}, p-value = {self._p(homogeneity['levene_p'])}")
        print(f"  Bartlett statistic = {homogeneity['bartlett_stat']:.4f}, p-value = {self._p(homogeneity['bartlett_p'])}")
        print("  Вывод:", self._decision(
            homogeneity["levene_p"],
            reject_text="дисперсии различаются, лучше использовать Welch ANOVA или непараметрический подход",
            keep_text="нет оснований считать дисперсии различными, можно использовать классический ANOVA",
        ))

        print("\n2.3. Визуальная проверка дисперсий:")
        boxplot_path = self._plot_boxplot(factor=factor, value=value, top_n=top_n)
        print(f"  Boxplot сохранен: {boxplot_path}")

        print("\n2.4. Решение о выборе метода:")
        normal_groups = (normality_table["p_value"] > self.alpha).sum()
        total_groups = normality_table["p_value"].notna().sum()
        normal_ok = normal_groups == total_groups and total_groups > 0
        equal_var = homogeneity["equal_var"]

        decision_rows = [
            {
                "Проверяемое предположение": "Нормальность в группах",
                "Выполняется?": "Да" if normal_ok else "Нет/частично",
                "Если нет, что делаем?": "Используем Крускала-Уоллиса как устойчивую альтернативу" if not normal_ok else "Можно применять ANOVA",
            },
            {
                "Проверяемое предположение": "Гомогенность дисперсий",
                "Выполняется?": "Да" if equal_var else "Нет",
                "Если нет, что делаем?": "Используем Welch ANOVA" if not equal_var else "Классический ANOVA допустим",
            },
            {
                "Проверяемое предположение": "Независимость наблюдений",
                "Выполняется?": "Да, по условию датасета",
                "Если нет, что делаем?": "Для зависимых наблюдений нужен повторный/парный дизайн",
            },
        ]
        decision_table = pd.DataFrame(decision_rows)
        print(decision_table.to_string(index=False))
        self._save_table(decision_table, "zad2_method_decision.csv")

        if equal_var:
            final_method = "Классический one-way ANOVA + проверка Крускала-Уоллиса для сравнения"
        else:
            final_method = "Welch ANOVA + Крускал-Уоллис как непараметрическая альтернатива"
        print(f"\n  Итоговое решение: {final_method}")

        self.results["zad2_normality"] = normality_table
        self.results["zad2_homogeneity"] = homogeneity
        self.results["zad2_decision"] = decision_table
        return normality_table, homogeneity, decision_table

    def zad_3(self, factor="experience", value="salary", top_n=None):
        print("\n" + "=" * 70)
        print("ЗАДАНИЕ 3. Однофакторный дисперсионный анализ (One-way ANOVA)")
        print("=" * 70)

        print("\n3.1. Гипотезы:")
        print(f"  H0: среднее значение {value} одинаково для всех групп фактора {factor}.")
        print(f"  H1: хотя бы одна группа фактора {factor} отличается по среднему {value}.")
        print(f"  Уровень значимости alpha = {self.alpha}")

        result = self._anova_manual(factor=factor, value=value, top_n=top_n)
        anova_table = result["anova_table"]

        print("\n3.2. Таблица ANOVA:")
        print(anova_table.round(4).to_string(index=False))
        self._save_table(anova_table, "zad3_one_way_anova_table.csv")

        print("\n3.3. Интерпретация:")
        print(
            f"  F({result['df_between']:.0f}, {result['df_within']:.0f}) = {result['F']:.4f}, "
            f"p-value = {self._p(result['p_value'])}"
        )
        print("  Решение:", self._decision(
            result["p_value"],
            reject_text=f"H0 отвергается. Средний {value} различается между группами {factor}.",
            keep_text=f"Нет оснований отвергнуть H0. Средний {value} статистически не различается между группами {factor}.",
        ))

        print("\n3.4. Визуализация средних с 95% CI:")
        means_path = self._plot_means_ci(factor=factor, value=value, top_n=top_n)
        print(f"  График сохранен: {means_path}")

        self.results["zad3_anova"] = result
        return result

    def zad_4(self, factor="experience", value="salary", top_n=None):
        print("\n" + "=" * 70)
        print("ЗАДАНИЕ 4. Post-hoc анализ и множественные сравнения")
        print("=" * 70)

        anova = self.results.get("zad3_anova") or self._anova_manual(factor=factor, value=value, top_n=top_n)

        if anova["p_value"] >= self.alpha:
            print("\nANOVA не показал статистически значимых различий, поэтому post-hoc анализ формально не требуется.")
            print("Для демонстрации метод все равно можно выполнить, но интерпретировать его нужно осторожно.")

        print("\n4.1. Tukey HSD для всех попарных сравнений:")
        tukey_table = self._tukey_hsd(factor=factor, value=value, top_n=top_n)
        if tukey_table is not None:
            print(tukey_table.to_string(index=False))
            self._save_table(tukey_table, "zad4_tukey_hsd.csv")
            heatmap_path = self._plot_posthoc_heatmap(tukey_table, filename="zad4_tukey_pvalues_heatmap.png")
            if heatmap_path:
                print(f"  Тепловая карта p-values сохранена: {heatmap_path}")

            if "reject" in tukey_table.columns:
                significant = tukey_table[tukey_table["reject"].astype(str).str.lower().isin(["true", "1"])]
                print("\n4.2. Значимые пары групп:")
                if significant.empty:
                    print("  По Tukey HSD значимых пар не найдено.")
                else:
                    for _, row in significant.iterrows():
                        print(f"  {row['group1']} vs {row['group2']}: p-adj = {row['p-adj']}, diff = {row['meandiff']}")
        else:
            print("  Tukey HSD пропущен из-за отсутствия statsmodels.")

        stats_table = self._group_stats(factor=factor, value=value, top_n=top_n)
        stats_no_total = stats_table[stats_table[factor] != "Всего"].copy()
        if not stats_no_total.empty:
            max_group = stats_no_total.loc[stats_no_total["mean"].idxmax(), factor]
            min_group = stats_no_total.loc[stats_no_total["mean"].idxmin(), factor]
            print("\n4.3. Средние значения по группам:")
            print(f"  Наибольшее среднее: группа {max_group}")
            print(f"  Наименьшее среднее: группа {min_group}")

        self.results["zad4_tukey"] = tukey_table
        return tukey_table

    def zad_5(self, factor="experience", value="salary", top_n=None, correction="holm"):
        print("\n" + "=" * 70)
        print("ЗАДАНИЕ 5. Непараметрическая альтернатива — критерий Крускала-Уоллиса")
        print("=" * 70)

        print("\n5.1. Гипотезы:")
        print(f"  H0: распределения {value} во всех группах {factor} одинаковы.")
        print(f"  H1: хотя бы одно распределение {value} отличается.")

        kruskal_result = self._kruskal(factor=factor, value=value, top_n=top_n)
        print("\n5.2. Результат Крускала-Уоллиса:")
        print(
            f"  H({kruskal_result['df']}) = {kruskal_result['H']:.4f}, "
            f"p-value = {self._p(kruskal_result['p_value'])}"
        )
        print("  Решение:", self._decision(
            kruskal_result["p_value"],
            reject_text=f"H0 отвергается. Распределения {value} по группам {factor} различаются.",
            keep_text=f"Нет оснований отвергнуть H0. Существенных различий распределений не найдено.",
        ))

        print("\n5.3. Сравнение ANOVA и Крускала-Уоллиса:")
        anova = self.results.get("zad3_anova") or self._anova_manual(factor=factor, value=value, top_n=top_n)
        compare_table = pd.DataFrame([
            {
                "Критерий": "ANOVA",
                "Статистика": f"F = {anova['F']:.4f}",
                "p-value": anova["p_value"],
                "Вывод": self._decision(anova["p_value"]),
            },
            {
                "Критерий": "Kruskal-Wallis",
                "Статистика": f"H = {kruskal_result['H']:.4f}",
                "p-value": kruskal_result["p_value"],
                "Вывод": self._decision(kruskal_result["p_value"]),
            },
        ])
        print(compare_table.to_string(index=False))
        self._save_table(compare_table, "zad5_anova_vs_kruskal.csv")

        dunn_table = None
        if kruskal_result["p_value"] < self.alpha:
            print("\n5.4. Post-hoc Dunn с коррекцией p-values:")
            dunn_table = self._dunn_posthoc(factor=factor, value=value, top_n=top_n, correction=correction)
            print(dunn_table.round(4).to_string(index=False))
            self._save_table(dunn_table, "zad5_dunn_posthoc.csv")
            heatmap_path = self._plot_posthoc_heatmap(dunn_table, filename="zad5_dunn_pvalues_heatmap.png")
            if heatmap_path:
                print(f"  Тепловая карта p-values сохранена: {heatmap_path}")
        else:
            print("\n5.4. Post-hoc Dunn не требуется, так как общий критерий незначим.")

        self.results["zad5_kruskal"] = kruskal_result
        self.results["zad5_compare"] = compare_table
        self.results["zad5_dunn"] = dunn_table
        return kruskal_result, compare_table, dunn_table

    def zad_6(self, factor_a="experience", factor_b="area", value="salary", top_n_b=5):
        print("\n" + "=" * 70)
        print("ЗАДАНИЕ 6. Многофакторный дисперсионный анализ (Two-way ANOVA)")
        print("=" * 70)

        self._require_columns([factor_a, factor_b, value])
        data = self.df_clean[[factor_a, factor_b, value]].dropna().copy()
        if top_n_b is not None:
            top_b = data[factor_b].value_counts().head(top_n_b).index
            data = data[data[factor_b].isin(top_b)].copy()

        print("\n6.1. Выбор переменных:")
        print(f"  Зависимая переменная: {value}")
        print(f"  Фактор A: {factor_a}")
        print(f"  Фактор B: {factor_b}")
        print(f"  H0(A): средние {value} по уровням {factor_a} равны.")
        print(f"  H0(B): средние {value} по уровням {factor_b} равны.")
        print(f"  H0(A×B): взаимодействия между {factor_a} и {factor_b} нет.")

        print("\n6.2. Количество наблюдений в ячейках:")
        cell_counts = pd.crosstab(data[factor_a], data[factor_b])
        print(cell_counts.to_string())
        self._save_table(cell_counts.reset_index(), "zad6_cell_counts.csv")

        group_means = data.groupby([factor_a, factor_b])[value].mean().reset_index()
        print("\n6.3. Групповые средние по комбинациям факторов:")
        print(group_means.round(3).to_string(index=False))
        self._save_table(group_means, "zad6_group_means.csv")

        print("\n6.4. Two-way ANOVA:")
        try:
            import statsmodels.api as sm
            from statsmodels.formula.api import ols
        except ImportError:
            print("  statsmodels не установлен, two-way ANOVA не выполнен.")
            self.results["zad6_two_way"] = None
            return None

        # Q("col") позволяет работать даже с названиями столбцов, где есть спецсимволы.
        formula = f'Q("{value}") ~ C(Q("{factor_a}")) * C(Q("{factor_b}"))'
        model = ols(formula, data=data).fit()
        anova_table = sm.stats.anova_lm(model, typ=2).reset_index()
        anova_table = anova_table.rename(columns={"index": "source", "sum_sq": "SS", "df": "df", "F": "F", "PR(>F)": "p_value"})

        # Добавим eta^2 для источников вариации.
        ss_total = anova_table["SS"].sum()
        anova_table["eta_sq"] = anova_table["SS"] / ss_total

        print(anova_table.round(4).to_string(index=False))
        self._save_table(anova_table, "zad6_two_way_anova.csv")

        print("\n6.5. Интерпретация эффектов:")
        for _, row in anova_table.iterrows():
            source = row["source"]
            if source == "Residual":
                continue
            p_value = row["p_value"]
            eta_sq = row["eta_sq"]
            print(
                f"  {source}: F = {row['F']:.4f}, p = {self._p(p_value)}, "
                f"eta^2 = {eta_sq:.4f} ({self._effect_size_interpretation(eta_sq)})"
            )
            print("   ", self._decision(
                p_value,
                reject_text="эффект статистически значим",
                keep_text="эффект статистически не значим",
            ))

        print("\n6.6. График взаимодействия:")
        interaction_path = self._plot_interaction(factor_a=factor_a, factor_b=factor_b, value=value, top_n_b=top_n_b)
        print(f"  График сохранен: {interaction_path}")

        # Простой анализ эффектов: ANOVA по factor_a отдельно внутри каждого уровня factor_b.
        print("\n6.7. Простой анализ эффектов:")
        simple_rows = []
        for b_level in sorted(data[factor_b].dropna().unique(), key=lambda x: str(x)):
            subset = data[data[factor_b] == b_level]
            if subset[factor_a].nunique() < 2:
                continue
            temp = self.__class__(subset, img_dir=self.img_dir, table_dir=self.table_dir, alpha=self.alpha)
            try:
                simple = temp._anova_manual(factor=factor_a, value=value)
                simple_rows.append({
                    factor_b: b_level,
                    "F": simple["F"],
                    "df_between": simple["df_between"],
                    "df_within": simple["df_within"],
                    "p_value": simple["p_value"],
                    "eta_sq": simple["eta_sq"],
                    "Вывод": self._decision(simple["p_value"]),
                })
            except Exception:
                continue

        simple_table = pd.DataFrame(simple_rows)
        if simple_table.empty:
            print("  Недостаточно данных для простого анализа эффектов.")
        else:
            print(simple_table.round(4).to_string(index=False))
            self._save_table(simple_table, "zad6_simple_effects.csv")

        self.results["zad6_two_way"] = anova_table
        self.results["zad6_simple_effects"] = simple_table
        return anova_table, simple_table

    def zad_7(self, factor="experience", value="salary", top_n=None):
        print("\n" + "=" * 70)
        print("ЗАДАНИЕ 7. Размер эффекта и сводная таблица результатов")
        print("=" * 70)

        anova = self.results.get("zad3_anova") or self._anova_manual(factor=factor, value=value, top_n=top_n)
        welch = self._welch_anova(factor=factor, value=value, top_n=top_n)
        kruskal = self.results.get("zad5_kruskal") or self._kruskal(factor=factor, value=value, top_n=top_n)

        print("\n7.1. Размер эффекта для one-way ANOVA:")
        print(f"  eta^2 = {anova['eta_sq']:.4f}")
        print(f"  omega^2 = {anova['omega_sq']:.4f}")
        print(f"  Cohen's f = {anova['cohen_f']:.4f}")
        print(f"  Интерпретация eta^2: {self._effect_size_interpretation(anova['eta_sq'])}")
        print(f"  Фактор {factor} объясняет примерно {anova['eta_sq'] * 100:.2f}% вариации переменной {value}.")

        print("\n7.2. Сравнение статистической и практической значимости:")
        practical = "практически значим" if anova["eta_sq"] >= 0.06 else "практически слабый"
        statistical = "статистически значим" if anova["p_value"] < self.alpha else "статистически не значим"
        print(f"  Результат: {statistical}, эффект {practical}.")

        summary_rows = [
            {
                "Анализ": "One-way ANOVA",
                "Фактор(ы)": factor,
                "F / H": f"F = {anova['F']:.4f}",
                "df": f"{anova['df_between']:.0f}; {anova['df_within']:.0f}",
                "p-value": anova["p_value"],
                "eta^2": anova["eta_sq"],
                "Вывод": self._decision(anova["p_value"]),
            },
            {
                "Анализ": "Welch ANOVA",
                "Фактор(ы)": factor,
                "F / H": f"F = {welch['F']:.4f}",
                "df": f"{welch['df1']:.2f}; {welch['df2']:.2f}",
                "p-value": welch["p_value"],
                "eta^2": np.nan,
                "Вывод": self._decision(welch["p_value"]),
            },
            {
                "Анализ": "Kruskal-Wallis",
                "Фактор(ы)": factor,
                "F / H": f"H = {kruskal['H']:.4f}",
                "df": f"{kruskal['df']:.0f}",
                "p-value": kruskal["p_value"],
                "eta^2": np.nan,
                "Вывод": self._decision(kruskal["p_value"]),
            },
        ]

        two_way = self.results.get("zad6_two_way")
        if isinstance(two_way, pd.DataFrame):
            for _, row in two_way.iterrows():
                if row["source"] == "Residual":
                    continue
                summary_rows.append({
                    "Анализ": "Two-way ANOVA",
                    "Фактор(ы)": row["source"],
                    "F / H": f"F = {row['F']:.4f}",
                    "df": f"{row['df']:.0f}",
                    "p-value": row["p_value"],
                    "eta^2": row["eta_sq"],
                    "Вывод": self._decision(row["p_value"]),
                })

        summary_table = pd.DataFrame(summary_rows)
        print("\n7.3. Сводная таблица результатов:")
        print(summary_table.round(4).to_string(index=False))
        self._save_table(summary_table, "zad7_summary_results.csv")

        self.results["zad7_summary"] = summary_table
        return summary_table

    def run_all(
        self,
        factor="experience",
        value="salary",
        factor_a="experience",
        factor_b="area",
        top_n=None,
        top_n_b=5,
    ):
        """Выполнить все задания лабораторной работы №5 последовательно."""
        self.zad_1(factor=factor, value=value, top_n=top_n)
        self.zad_2(factor=factor, value=value, top_n=top_n)
        self.zad_3(factor=factor, value=value, top_n=top_n)
        self.zad_4(factor=factor, value=value, top_n=top_n)
        self.zad_5(factor=factor, value=value, top_n=top_n)
        self.zad_6(factor_a=factor_a, factor_b=factor_b, value=value, top_n_b=top_n_b)
        self.zad_7(factor=factor, value=value, top_n=top_n)


# Пример использования:
if __name__ == "__main__":
    # Путь можно поменять под свой датасет.
    df = pd.read_csv("data/api/Python.csv", sep=";", encoding="utf-8-sig")

    lab5 = AnovaLab5(
        df,
        img_dir="img/api/Python/lab5",
        table_dir="tables/api/Python/lab5",
        alpha=0.05,
    )

    # Основной однофакторный анализ: salary ~ experience.
    # Двухфакторный анализ: salary ~ experience * area, где area ограничен top-5 городами.
    lab5.run_all(
        factor="experience",
        value="salary",
        factor_a="experience",
        factor_b="area",
        top_n=None,
        top_n_b=5,
    )
