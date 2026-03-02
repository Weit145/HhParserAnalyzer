import pandas as pd
import test
from .stats import Statistic
from .parsers.html_parser import Parser
from .parsers.api_parser import HHParserApi
from tests.test_api import test


def main():
    # parser = Parser("Python", mx=3000)
    # df = parser.run()
    # parser.write_csv(df)

    # df = pd.read_csv("Python.csv", sep=';', encoding='utf-8-sig')
    # st = Statistic(df, img_dir="img")
    # st()
    # st.run(metric='salary', group_col='experience', scatter_x='salary', 
    #     scatter_y='responses', scatter_hue='experience')


    # parser = HHParserApi("Python","data/api/test/")
    # df = parser.run()
    # df.shape
    # parser.write_csv(df)

    df = pd.read_csv("data/api/test/Python.csv", sep=';', encoding='utf-8-sig')
    st = Statistic(df, img_dir="img/api/test")
    st()
    st.run(metric='salary', group_col='experience', scatter_x='salary', 
        scatter_y='monthly_hours', scatter_hue='experience')

    # test()


if __name__ == "__main__":
    main()