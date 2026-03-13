import pandas as pd
from .stats.statistic import Statistic
from .hh_parser.parsers.html_parser import Parser
from .hh_parser.parsers.api_parser import HHParserApi


def main():
    # parser = Parser("Python", mx=3000)
    # df = parser.run()
    # parser.write_csv(df)

    # df = pd.read_csv("Python.csv", sep=';', encoding='utf-8-sig')
    # st = Statistic(df, img_dir="img")
    # st()
    # st.run(metric='salary', group_col='experience', scatter_x='salary', 
    #     scatter_y='responses', scatter_hue='experience')


    # parser = HHParserApi("1с","data/api/")
    # df = parser.run()
    # df.shape
    # parser.write_csv(df)
    
    df = pd.read_csv("data/api/Python.csv", sep=';', encoding='utf-8-sig')
    st = Statistic(df, img_dir="img/api/Python")
    st()
    st.run(metric='salary', group_col='experience', scatter_x='salary', 
        scatter_y='monthly_hours', scatter_hue='experience', row_var='area', col_var='experience')


if __name__ == "__main__":
    main()