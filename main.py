import pandas as pd
from statictic import Statistic
from parser import Parser
from hh_api import HHParserApi


def main():
    # parser = Parser("Python", mx=3000)
    # df = parser.run()
    # parser.write_csv(df)

    # df = pd.read_csv("Python.csv", sep=';', encoding='utf-8-sig')
    # st = Statistic(df, img_dir="img")
    # st()
    # st.run(metric='salary', group_col='experience', scatter_x='salary', 
    #     scatter_y='responses', scatter_hue='experience')


    # parser = HHParserApi("Python")
    # df = parser.run()
    # parser.write_csv(df)

    df = pd.read_csv("Python.csv", sep=';', encoding='utf-8-sig')
    st = Statistic(df, img_dir="img")
    st()
    st.run(metric='salary', group_col='experience', scatter_x='salary', 
        scatter_y='experience', scatter_hue='monthly_hours')




if __name__ == "__main__":
    main()