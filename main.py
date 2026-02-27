import pandas as pd
from statictic import Statistic
from parser import Parser


def main():
    # parser = Parser("Python", mx=3000)
    # df = parser.run()
    # parser.write_csv(df)

    df = pd.read_csv("data/vacancies.csv", sep=';', encoding='utf-8-sig')
    st = Statistic(df, img_dir="img")
    st()
    st.run(metric='salary', group_col='experience', scatter_x='salary', 
        scatter_y='responses', scatter_hue='experience')
if __name__ == "__main__":
    main()