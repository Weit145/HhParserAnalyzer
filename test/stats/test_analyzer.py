import pytest 
import pandas as pd
import numpy as np
from contextlib import nullcontext
from src.stats.analyzer import StatisticAnalyzer 


class TestStatisticAnalyzer:
        
    @pytest.fixture
    def sample_df(self):
        np.random.seed(42)
        n = 50
        data = {
            'num1': np.random.randn(n),
            'num2': np.random.randn(n) * 2 + 1,
            'cat1': np.random.choice(['A', 'B', 'C', 'D', 'E'] * 10, size=n),
            'cat2': np.random.choice(['X', 'Y', 'Z'] * 17, size=n),
            'target': np.random.randn(n)
        }
        data['num1'][0] = np.nan
        data['num2'][5] = np.nan
        return pd.DataFrame(data)

    def test_init(self, sample_df):
        result = StatisticAnalyzer(sample_df)
        pd.testing.assert_frame_equal(result.df, sample_df)
    
    @pytest.fixture
    def init_class(self, sample_df):
        return StatisticAnalyzer(sample_df)

    @pytest.mark.parametrize(
        "col , expec",
        [
            ("num1",nullcontext()),
            ("num2",nullcontext()),
            ("cat1",pytest.raises(TypeError)),
            ("cat2",pytest.raises(TypeError)),
            ("target",nullcontext()),
            ("trap",pytest.raises(KeyError)),
        ]
    )
    def test_skewness(self, col, expec, init_class):
        with expec:
            init_class.skewness(col)
        

    @pytest.mark.parametrize(
        "col , expec",
        [
            ("num1",nullcontext()),
            ("num2",nullcontext()),
            ("cat1",pytest.raises(TypeError)),
            ("cat2",pytest.raises(TypeError)),
            ("target",nullcontext()),
            ("trap",pytest.raises(KeyError)),
        ]
    )

    def test_kurtosis(self, init_class, col, expec):
        with expec:
            init_class.kurtosis(col)
    
    @pytest.mark.parametrize(
        "data , cor",
        [
            (pd.DataFrame({"cat1":np.array(["a","s"]), "cat2":np.array(["a","s"])}),(0, 0)),
            (pd.DataFrame({"cat1":np.array([2,1]), "cat2":np.array([2,1])}),(2, 2)),
        ]
    )
    def test_correlation_matrix(self, data, cor):
        result = StatisticAnalyzer(data)
        assert result.correlation_matrix().shape == cor
    
    @pytest.mark.parametrize(
        "group_col , target_col, expec",
        [
            ("num1", "num2", nullcontext()),
            ("num2", "cat1", pytest.raises(TypeError)),
            ("cat1", "cat2", pytest.raises(TypeError)),
            ("cat2", "target", nullcontext()),
            ("target", "trap", pytest.raises(KeyError)),
            ("trap", "trap", pytest.raises(KeyError)),
        ]
    )
    def test_group_stats(self,init_class, group_col, target_col,expec):
        with expec:
            init_class.group_stats(group_col,target_col)
    
    @pytest.mark.parametrize(
        "row_var , col_var, expec",
        [
            ("num1", "num2", nullcontext()),
            ("num2", "cat1", nullcontext()),
            ("cat1", "cat2", nullcontext()),
            ("cat2", "target", nullcontext()),
            ("target", "trap", pytest.raises(KeyError)),
            ("trap", "trap", pytest.raises(KeyError)),
        ]
    )
    def test_cross_tab(self, init_class, row_var, col_var,expec):
        with expec:
            init_class.cross_tab(row_var,col_var)