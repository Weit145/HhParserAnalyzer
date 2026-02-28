import pandas as pd
from .stats import Statistic
from .parsers.html_parser import Parser
from .parsers.api_parser import HHParserApi


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
    # df.shape
    # parser.write_csv(df)

    df = pd.read_csv("data/api/Python.csv", sep=';', encoding='utf-8-sig')
    st = Statistic(df, img_dir="img/api")
    st()
    st.run(metric='salary', group_col='experience', scatter_x='salary', 
        scatter_y='monthly_hours', scatter_hue='experience')




if __name__ == "__main__":
    main()