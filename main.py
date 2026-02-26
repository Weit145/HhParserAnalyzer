import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from parser import Parser


def main():
    parser = Parser("Python", mx=3000)
    df = parser.run()
    parser.write_csv(df)

    # df = pd.read_csv("vacancies.csv", sep=';', encoding='utf-8-sig')
    # print(df.head())
    # pd.set_option('display.float_format', '{:.2f}'.format)
    # print(df.shape)
    # print(df.describe())

    # plt.figure(figsize=(8,4))
    # sns.boxplot(x=df['experience'], y=df['salary'])
    # plt.title('Распределение зарплат (boxplot)')
    # plt.savefig('salary_boxplot.png', dpi=300, bbox_inches='tight')

    # plt.figure(figsize=(10,5))
    # plt.hist(df['salary'], bins=50, edgecolor='black')
    # plt.title('Гистограмма зарплат')
    # plt.xlabel('Зарплата')
    # plt.ylabel('Частота')
    # plt.savefig('salary_hist.png')

if __name__ == "__main__":
    main()