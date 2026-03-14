import pytest 
import pandas as pd
import numpy as np
from contextlib import nullcontext
from src.stats.cleaner import Cleaner

class TestCleaner:
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
        result = Cleaner(sample_df)
        pd.testing.assert_frame_equal(result.df, sample_df)
        
    @pytest.fixture
    def init_class(self, sample_df):
        return Cleaner(sample_df)
    
    @pytest.mark.parametrize(
        "col , expec",
        [
            ("num1",nullcontext()),
            ("num2",nullcontext()),
            ("cat1",pytest.raises(AssertionError)),
            ("cat2",pytest.raises(AssertionError)),
            ("target",nullcontext()),
            ("trap",pytest.raises(KeyError)),
        ]
    )
    def test_clean_col_dup(self, init_class, col, expec):
        with expec:
            result = init_class.clean_col_dup(column=col)
            assert result[col].duplicated().sum() == 0
            assert result[col].isna().sum() == 0
    
    
    @pytest.mark.parametrize(
        "col , expec",
        [
            ("num1",nullcontext()),
            ("num2",nullcontext()),
            ("cat1",nullcontext()),
            ("cat2",nullcontext()),
            ("target",nullcontext()),
            ("trap",pytest.raises(KeyError)),
        ]
    )
    def test_to_numeric(self, init_class, col, expec):
        with expec:
            result = init_class.to_numeric(columns=[col])
            assert pd.api.types.is_numeric_dtype(result[col])
            
    
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
    def test_remove_outliers_iqr(self, init_class, col, expec):
        with expec:
            result = init_class.remove_outliers_iqr(column=col)
            Q1 = init_class.df[col].quantile(0.25)
            Q3 = init_class.df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            assert result[(result[col] < lower) | (result[col] > upper)].empty