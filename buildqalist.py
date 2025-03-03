import pandas as pd

# 读取Excel文件
excel_file = "qalist.xlsx"  # Excel文件路径
df = pd.read_excel(excel_file)

# 保存为CSV文件
csv_file = "qalist.csv"  # CSV文件路径
df.to_csv(csv_file, index=False)  # index=False表示不保存行索引

# data = {
#     "question": ["霄云里8号的建筑高度是49.5米?", "梅赛德斯-奔驰如何接管布朗GP车队？"],
#     "answer": [
#         "霄云里8号的建筑高度是49.5米。",
#         "梅赛德斯-奔驰通过收购布朗GP 75.1%的股份接管了车队。",
#     ],
# }

# df = pd.DataFrame(data)

# df.to_csv("example.csv", index=False)
