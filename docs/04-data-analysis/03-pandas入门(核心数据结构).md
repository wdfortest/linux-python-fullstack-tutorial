# 第 3 章 · pandas 入门（核心数据结构）

> 本章配套代码：`projects/data-analysis-lab/03_pandas_basics.py`
> 建议学习时长：约 4 小时

## 学习目标

学完本章，你能够：

1. 说清 Series / DataFrame 的内部构成（ndarray + Index），知道为什么「列是 Series」；
2. 用 5 种常见方式创建 DataFrame，用 head / info / describe / value_counts 四件套给数据做体检；
3. 区分 loc（标签）与 iloc（位置）两条取数路径，并用一步到位的 `.loc` 掩码赋值避开链式赋值陷阱；
4. 用布尔掩码与 query 两种写法完成同一筛选；
5. 解释 axis=0 / axis=1 到底指哪根轴；
6. 熟练使用 read_csv 的 encoding / usecols / dtype / chunksize，以及 read_sql（参数绑定）、read_excel 与 to_* 导出全家桶。

## 3.1 前置知识 / 本章地位

第 1、2 章解决了「把数据从库里问出来」，本章开始「在内存里加工数据」。pandas 是 Python 数据分析的事实标准，本篇第 4~7 章的清洗、聚合、可视化全部建立在它的两个数据结构上。实测环境：pandas 2.3.3 + numpy 2.3.5（API 以 pandas 2.x 为准，3.0 的主要变化是默认启用 Copy-on-Write，会在 3.4 节标注差异）。

本章实验全程使用**真实数据** `projects/book-insight/data/books.csv`——爬虫篇采集的 1000 本图书（books.toscrape.com，练习站点）。运行方式：

```bash
source ~/opt/jjyv/bin/activate
python projects/data-analysis-lab/03_pandas_basics.py
```

下文所有输出均来自这次真实运行。

## 3.2 Series 与 DataFrame：内部结构

**Series** = 一列数据（numpy ndarray）+ 一条索引（Index）。索引是「行标签」，可以是整数、字符串、时间——这是 pandas 与 numpy 最本质的区别：numpy 数组只有位置（0,1,2...），Series 的每一行还有名字。

```python
import pandas as pd

s = pd.Series([226, 196, 203, 179, 196], index=[1, 2, 3, 4, 5], name="book_count")
```

预期输出：

```text
1    226
2    196
3    203
4    179
5    196
Name: book_count
```

**DataFrame** = 一组共享同一条 Index 的 Series（每列一条）。所以「取一列得到 Series」：

```python
df5 = pd.read_csv(CSV_PATH)
print(type(df5["price"]).__name__, type(df5["price"].to_numpy()).__name__)
```

预期输出：

```text
Series ndarray
```

心智模型：DataFrame 是「字典的列」，`df[col]` 拿 Series，`df[[c1, c2]]`（注意双层括号）拿子表；行方向则统一走 3.4 节的 loc / iloc。Index 不是「第几行」而是「行名」——它不保证连续、不保证唯一，切片时这一区别会反复出现。

### 创建 DataFrame 的 5 种常见方式

```python
df1 = pd.DataFrame({"rating": [1, 2, 3], "count": [226, 196, 203]})   # [1] 字典
df2 = pd.DataFrame([{"title": "A Light in the Attic", "price": 51.77},
                    {"title": "Tipping the Velvet", "price": 53.74}])  # [2] 记录列表
arr = pd.DataFrame([[1, 226], [2, 196]], columns=["rating", "count"])  # [3] 二维数组
s = pd.Series({...})                                                    # [4] 由 Series 组成
df5 = pd.read_csv(CSV_PATH)                                             # [5] 读文件（主线）
```

日常分析里 95% 的 DataFrame 来自第 5 种（read_csv / read_sql / read_excel），前 4 种用于构造小样例与测试。

## 3.3 查看全家桶：head / info / describe / value_counts

拿到任何新数据，第一件事是四件套体检（以真实图书数据为例）：

```python
df5 = pd.read_csv(CSV_PATH)
print(df5.shape)          # (行数, 列数)
df5.head(3)               # 前 3 行（默认 5）
df5.info()                # 各列类型与非空计数
df5[["price", "availability", "rating"]].describe()   # 数值列五数概括
df5["rating"].value_counts()                          # 类别频次
```

`head(3)` 预期输出（节选 4 列）：

```text
               title  price  rating           category
A Light in the Attic  51.77       3             Poetry
  Tipping the Velvet  53.74       1 Historical Fiction
          Soumission  50.10       1            Fiction
```

`info()` 预期输出——重点看两处：每列的 Non-Null Count（找缺失）与 Dtype（找类型错误）：

```text
RangeIndex: 1000 entries, 0 to 999
 #   Column          Non-Null Count  Dtype  
---  ------          --------------  -----  
 0   id              1000 non-null   int64  
 3   price           1000 non-null   float64
 9   num_reviews     1000 non-null   int64  
 10  description     998 non-null    object 
dtypes: float64(3), int64(4), object(7)
memory usage: 109.5+ KB
```

`description` 只有 998 非空——真实数据确实带 2 处缺失，第 7 章会处理它。

`describe()` 预期输出（四舍五入到 2 位）：

```text
         price  availability   rating
count  1000.00       1000.00  1000.00
mean     35.07          8.59     2.92
std      14.45          5.65     1.43
min      10.00          1.00     1.00
25%      22.11          3.00     2.00
50%      35.98          7.00     4.00
max      59.99         22.00     5.00
```

`value_counts()` 预期输出：

```text
rating
1    226
2    196
3    203
4    179
5    196
```

两处值得注意的真实结论：价格中位数 35.98 与均值 35.07 接近（分布不算偏）；评分五档 179~226 本几乎均匀——这不是真实市场的形态，而是练习站的人造特性（第 7 章把它写进可信度声明）。`value_counts(normalize=True)` 可改输出占比；对连续列（如 price）要用第 6 章的直方图而非 value_counts。

## 3.4 loc / iloc：标签路径与位置路径（重点）

pandas 有两条取行路径：**loc 按标签（label）**，**iloc 按位置（integer location）**。把书名设为索引后对比最直观：

```python
books = df5.set_index("title")
books.loc["A Light in the Attic", ["price", "rating"]]   # 标签：行名 + 列名
df5.iloc[0, [3, 7]]                                      # 位置：第 0 行第 3、7 列
```

预期输出：

```text
loc[按标签] = {'price': 51.77, 'rating': 3}
iloc[按位置] = [51.77, 3] （第 0 行第 3、7 列：price、rating）
```

记忆：**loc 的「l」是 label**。二者切片语义不同——`loc["a":"c"]` 闭区间（含端点），`iloc[0:3]` 左闭右开（同 Python 列表）。当 Index 恰好是 0,1,2... 时两种写法结果碰巧一致，这正是混淆的温床：一旦删过行或 set_index，两者立刻分道扬镳。

### 链式赋值陷阱（必读）

先用布尔索引取出片段、再对片段赋值，中间会产生副本，赋值可能落在副本上——pandas 会发出 `SettingWithCopyWarning`，你的修改「可能生效也可能没生效」，这是 pandas 最著名的坑。脚本真实复现了它：

```python
frag = df5[df5["category"] == "Poetry"]
frag["price"] = 0.0        # ❌ 反面案例：链式取片段后直接赋值
```

预期输出（警告被截断示意）：

```text
触发警告: SettingWithCopyWarning - A value is trying to be set on a copy of a slice from a Dat ...
```

正确写法是**一步到位**的 `.loc` 掩码赋值——「改哪些行、哪些列、改成什么」在同一条语句里说完：

```python
fixed = df5.copy()
fixed.loc[fixed["category"] == "Poetry", "price"] = 0.0   # ✅ 正确
```

> pandas 3.0 起默认启用 Copy-on-Write（写时复制），链式赋值会直接**报错**而不是警告——本教程按 2.x 行为教学，但「永远一步到位用 .loc」的习惯两种版本下都正确。

## 3.5 布尔掩码与 query：两种等价写法

**布尔掩码**是 pandas 筛选的地基：比较表达式产生一列 True/False，塞进方括号只留下 True 的行。多条件用 `&`（与）、`|`（或），**每个条件必须加括号**（因为 `&` 优先级高于 `==`）：

```python
mask = (df5["rating"] == 5) & (df5["price"] < 15)
q = df5.query("rating == 5 and price < 15")     # 等价的 query 写法
print(len(df5[mask]), len(q), df5[mask].equals(q))
```

预期输出：

```text
[布尔掩码] 5 星且 <15 英镑: 23 本
[query]   5 星且 <15 英镑: 23 本
两者结果一致: True
```

其中 3 本（真实输出）：

```text
                                                                            title  price       category
Princess Jellyfish 2-in-1 Omnibus, Vol. 01 (Princess Jellyfish 2-in-1 Omnibus #1)  13.61 Sequential Art
                                 Princess Between Worlds (Wide-Awake Princess #5)  13.34        Fantasy
                           The Third Wave: An Entrepreneur’s Vision of the Future  12.61       Business
```

两种写法怎么选：掩码通用（条件可复用、可组合变量），query 胜在接近 SQL 的可读性（列名直接写，外部变量用 `@var` 引用，如 `df.query("price < @limit")`）。

## 3.6 axis 概念：0 沿行往下、1 沿列横着

`axis` 参数决定聚合**沿着哪个方向**压过去，容易背反。记「**指定的是被消灭的方向**」：`axis=0` 每列各自算——行方向被压缩掉；`axis=1` 每行各自算——列被压缩掉：

```python
mini = df5[["price", "availability"]].head(3)
mini.sum(axis=0)   # 每列合计
mini.sum(axis=1)   # 每行合计
```

预期输出：

```text
   price  availability
0  51.77            22
1  53.74            20
2  50.10            20
sum(axis=0)（每列合计）: {'price': 155.61, 'availability': 62.0}
sum(axis=1)（每行合计）: [73.77, 73.74, 70.1]
```

`drop(axis=1)` 删列、`mean(axis=0)` 算列均值，全是同一个逻辑。

## 3.7 IO 全家桶

### read_csv 的关键参数

```python
# 只读 3 列 + 把 rating 压成 int8（列多数据大时省内存明显）
slim = pd.read_csv(CSV_PATH, usecols=["title", "price", "rating"], dtype={"rating": "int8"})

# 分块读取：一次 200 行，返回迭代器（处理超出内存的大文件）
total_rows = sum(len(chunk) for chunk in pd.read_csv(CSV_PATH, chunksize=200))
```

预期输出：

```text
[usecols+dtype] 列: ['title', 'price', 'rating'] | rating 内存类型: int8
[chunksize=200] 分 5 块读完，总行数 = 1000
```

**encoding 是中文数据的第一大坑**：本仓库爬虫写出的是 `utf-8-sig`（带 BOM），读取时 `encoding="utf-8-sig"` 或默认 `utf-8` 都能读；但拿到 GBK 编码的文件时默认 utf-8 会直接报 `UnicodeDecodeError`，要显式 `encoding="gbk"`。其他常用参数：`nrows=N` 只读前 N 行先看看、`na_values=[...]` 自定义缺失标记、`parse_dates=["col"]` 读入时顺手转日期。

### read_sql：参数绑定照旧

第 2 章 2.8 节已预告，这里给出 sqlite3 DBAPI 版本（`?` 占位符；SQLAlchemy 连接则用 `:name`）：

```python
import sqlite3

conn = sqlite3.connect(DB_PATH)
sql_df = pd.read_sql(
    "SELECT title, price, category FROM books WHERE rating >= ? AND price <= ? LIMIT 3",
    conn,
    params=(5, 20.0),
)
conn.close()
```

预期输出：

```text
                                                     title  price     category
                                               Set Me Free  17.46  Young Adult
The Four Agreements: A Practical Guide to Personal Freedom  17.66 Spirituality
                                            Sophie's World  15.94   Philosophy
```

> ⚠️ `read_sql` 的 SQL 同样禁止拼接：把 `rating` 用 f-string 塞进查询字符串，就是第 1 章 1.9 节反面案例的 pandas 版。**占位符 + params 是唯一正确姿势。**

### read_excel 与 to_* 导出

读写 Excel 需要 `openpyxl` 包（jjyv 环境已装）：

```python
df5.head(20)[["title", "price", "rating", "category"]].to_excel("output/03_books_sample.xlsx", index=False)
back = pd.read_excel("output/03_books_sample.xlsx")
```

预期输出：

```text
[to_excel/read_excel] 往返一致: True -> 03_books_sample.xlsx
```

`to_*` 系列常用三个：`to_csv`（交付 Excel 用户时加 `encoding="utf-8-sig"` 防乱码）、`to_excel`、`to_json`（`orient="records"` 输出记录数组、`force_ascii=False` 保留中文）。`index=False` 几乎总是要写——除非对方真的需要行索引：

```python
df5.head(1)[["title", "price"]].to_json(orient="records", force_ascii=False)
```

预期输出：

```text
[{"title":"A Light in the Attic","price":51.77}]
```

## 常见坑与排查（Troubleshooting）

| 报错/现象 | 原因 | 解决办法 |
|---|---|---|
| `UnicodeDecodeError` 读 CSV | 文件不是 UTF-8（常见 GBK） | `encoding="gbk"` 或先 `file 文件名` 查编码 |
| `KeyError: 'price'` | 列名带空格/大小写不符 | `df.columns` 核对；`df.columns = df.columns.str.strip()` |
| 赋值后数据没变 + `SettingWithCopyWarning` | 链式赋值落在副本上 | 一步到位 `df.loc[mask, col] = v`（见 3.4） |
| `&` 报 `TypeError` 或结果错 | 布尔条件没加括号 | 每个条件加括号；`and/or` 在掩码里无效（要用 `&/|`） |
| `df[col][row] = v` 时灵时不灵 | 混用两条取数路径 | 统一 `.loc[行, 列]` 或 `.iloc[行, 列]` |
| describe() 里没出现某些列 | 非数值列被默认排除 | `describe(include="all")` 或单独 `value_counts()` |
| loc 切片结果比预期多/少一行 | loc 闭区间、iloc 左闭右开 | 确认走的是哪条路径再数端点 |
| 读大文件内存爆掉 | 全量读入 | `usecols` 只取需要的列、`dtype` 压类型、`chunksize` 分块 |
| `read_sql` 报占位符错误 | SQLite 用 `?`、SQLAlchemy 用 `:name` 混用 | 按连接类型选占位符，params 与之配对 |
| Excel 打开 CSV 中文乱码 | 无 BOM | 导出用 `encoding="utf-8-sig"`（第 03 篇第 4 章同款问题） |

## 动手练习

（用真实数据 `books.csv`，跑 `03_pandas_basics.py` 后在 Python 交互环境完成）

1. **体检报告**：对 `availability` 列输出 describe 与 value_counts（bins 分箱可用 `value_counts(bins=5)`）。（验收：均值 8.59、中位数 7.0；最小 1、最大 22；五箱中最密的 1~5 本一箱有 420 种）
2. **掩码筛选**：找出「Romance 分类、库存不超过 3 本」的书，按价格降序输出前 3 行书名与价格。（验收：共 14 行符合条件，首行 `Listen to Me (Fusion #1)  58.99`）
3. **loc/iloc 对抗赛**：先 `df.drop(index=0)` 再分别用 loc 与 iloc 取「原第 0 行」，观察 loc 报 KeyError 而 iloc 正常——用一句话解释原因。
4. **IO 往返**：把 5 星书导出为 `utf-8-sig` 的 CSV，再读回来验证行数一致（应为 196 行）。

<details>
<summary>练习 2 提示</summary>

`df5.query("category == 'Romance' and availability <= 3").sort_values("price", ascending=False).head(3)[["title", "price"]]`——注意字符串条件在 query 里用单引号包住；掩码写法为 `df5[(df5["category"] == "Romance") & (df5["availability"] <= 3)]`。
</details>

## 小结与自检清单

- [ ] 能画出 Series / DataFrame 的内部结构图（ndarray + Index），解释「列即 Series」；
- [ ] 拿到新 DataFrame 会先跑 head / info / describe / value_counts 四件套，并说得出每个命令看什么；
- [ ] 能背出 loc 标签、iloc 位置，以及两者切片的端点差异；
- [ ] 遇到赋值不生效先检查链式赋值，能用一步 .loc 掩码赋值改写；
- [ ] 能用掩码与 query 各写一遍多条件筛选，记得加括号与 & |
- [ ] axis=0/1 不再背反：指定的是「被压缩的方向」；
- [ ] read_csv 会用 encoding / usecols / dtype / chunksize 四个关键参数；
- [ ] read_sql 全程占位符 + params，不做任何 SQL 拼接；
- [ ] to_csv 给 Excel 用户时记得 `encoding="utf-8-sig"` 与 `index=False`。

## 延伸阅读

- [pandas 官方文档：10 minutes to pandas](https://pandas.pydata.org/docs/user_guide/10min.html) —— 官方入门教程，本章节骨架的官方版；
- [pandas User Guide: Indexing and selecting data](https://pandas.pydata.org/docs/user_guide/indexing.html) —— loc/iloc/链式赋值/.loc 掩码赋值的完整规则（3.4 节的权威版）；
- [pandas User Guide: IO tools](https://pandas.pydata.org/docs/user_guide/io.html) —— read_csv 全部参数与 read_sql 各连接形态；
- [pandas: Copy-on-Write](https://pandas.pydata.org/docs/user_guide/copy_on_write.html) —— 3.0 的默认行为变化，提前了解可少踩未来的坑；
- 下一章：[第 4 章 pandas 数据清洗实战](04-pandas数据清洗实战.md)——四件套体检之后，数据脏了怎么洗。
