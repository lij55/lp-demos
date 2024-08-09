import streamlit as st
from schedule import solve_schedule
import pandas as pd


st.set_page_config(
     page_title='Nurse demo',
     #layout="wide",
)

args = {}

st.header('护士APN排班示例')
st.info('周排班，每个护士5个班次， 每天最多一个班次，夜班尽可能平均')
num_nurses = st.number_input('护士人数', format="%d", value=15, step=1, min_value=1, max_value=30)

group_shift = st.container(border=True)
col1, col2, col3 = group_shift.columns(3)
shift = col1.selectbox('班次', [3], )


args["num_workday_n"] = col2.number_input(f'N班人数', format="%d", value=2, step=1, min_value=1, max_value=10)
args["num_workday_a"] = col2.number_input(f'A班最少人数', format="%d", value=4, step=1, min_value=1, max_value=10)
args["num_workday_p"] = col2.number_input(f'P班最少人数', format="%d", value=3, step=1, min_value=1, max_value=10)

args["num_weekend_n"] = col3.number_input(f'周末N班人数', format="%d", value=2, step=1, min_value=1, max_value=10)
args["num_weekend_a"] = col3.number_input(f'周末A班人数', format="%d", value=2, step=1, min_value=1, max_value=10)
args["num_weekend_p"] = col3.number_input(f'周末P班人数', format="%d", value=2, step=1, min_value=1, max_value=10)

# st.data_editor('Edit data', data)

group_rest = st.container(border=True)
c_rest = group_rest.checkbox('休息班次')

if c_rest:
    args["extra_rest_constrain"] = True
    args["extra_rest_n"] = group_rest.number_input(f'N班后休息班数', format="%d", value=4, step=1, min_value=1, max_value=5)
    args["extra_rest_a"] = group_rest.number_input(f'A班后休息班数', format="%d", value=1, step=1, min_value=1, max_value=5)
    args["extra_rest_p"] = group_rest.number_input(f'P班后休息班数', format="%d", value=1, step=1, min_value=1, max_value=5)


def int_to_name(v):
    if v == 0:
        return ""
    if v == 1:
        return "N"
    if v == 10:
        return "A"
    if v == 100:
        return "P"
    if v == 11:
        return "N+A"
    if v == 110:
        return "A+P"
    if v == 101:
        return "N+P"
    if v == 111:
        return "N+A+P"
    print(v)


result = solve_schedule(num_nurses, args)
if result is not None:
    #st.write(result)
    df = pd.DataFrame(result, columns=['一','二','三','四','五','六','日',]).map(int_to_name)
    st.dataframe(df,use_container_width=True)
    df1 = pd.DataFrame()

    for c in df.columns:
        df1[c] = df[c].value_counts()
    st.write(df1)
else:
    st.warning('无法满足条件')
st.button('重新计算')
