import sys
from unittest.mock import MagicMock


def _passthrough(func=None, **kw):
    # handles both @st.cache_resource (no parens) and @st.cache_data(ttl=300)
    if func is not None:
        return func
    return lambda f: f


st_mock = MagicMock()
st_mock.cache_data = _passthrough
st_mock.cache_resource = _passthrough
sys.modules.setdefault("streamlit", st_mock)
