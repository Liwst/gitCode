# 写入CSV文件,并读取
import csv
data = [
    ["姓名", "年龄", "分数"],
    ["张三", 18, 95],
    ["李四", 19, 92]
]

with open("students.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(data)

# 读取并统计
with open("students.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)  # 跳过标题
    total = 0
    for row in reader:
        total += int(row[2])
    print(f"平均分：{total/2}")  # 输出平均分
