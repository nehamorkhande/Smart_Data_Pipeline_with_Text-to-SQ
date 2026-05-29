
# import pandas as pd
# from cleaner import clean_dataframe

# data = {
#     'Date'          : ['2024-01-01', '2024-01-02', None],
#     'Customer Name' : ['rahul sharma', 'PRIYA PATEL', 'Amit'],
#     'Product'       : ['Laptop', 'Mouse', 'Keyboard'],
#     'Qty'           : [2, 5, None],
#     'Total Amount'  : [90000, 2500, 1200]
# }
# df = pd.DataFrame(data)
# result = clean_dataframe(df, 'test.xlsx')
# print('Success     :', result['success'])
# print('Final rows  :', result['final_rows'])
# print('Missing fixed:', result['missing_fixed'])
# print(result['dataframe'][['sale_date','customer_name','quantity']].to_string())


import pandas as pd
from pipeline.cleaner import clean_dataframe
from pipeline.normalizer import normalize_and_load

data = {
    'Date'          : ['2024-01-01', '2024-01-02'],
    'Customer Name' : ['Rahul Sharma', 'Priya Patel'],
    'Product'       : ['Laptop', 'Mouse'],
    'Category'      : ['Electronics', 'Electronics'],
    'Qty'           : [2, 5],
    'Total Amount'  : [90000, 2500]
}
df = pd.DataFrame(data)
cleaned = clean_dataframe(df, 'test.xlsx')
result  = normalize_and_load(cleaned['dataframe'], 1)
print('New rows    :', result['new_rows'])
print('Skipped     :', result['skipped'])
print('Customers   :', result['customers'])
print('Products    :', result['products'])
print('Categories  :', result['categories'])
