# 第 2 章 · SQLAlchemy 2.0：ORM 与数据库连接

> 本章配套代码：`projects/data-analysis-lab/02_sqlalchemy_orm.py`
> 建议学习时长：约 3.5 小时

## 学习目标

学完本章，你能够：

1. 判断一个场景该用 ORM 还是该用原生 SQL，说清两者的边界；
2. 分清 SQLAlchemy 的 Core / ORM 两个层次与 Engine / Connection / Session 三个对象的职责；
3. 用 2.0 风格（`DeclarativeBase` / `Mapped` / `mapped_column`）写出与真实表对齐的模型，完成增删改查；
4. 用事务回滚保护写操作，理解「未 commit 的修改随时可丢弃」；
5. 写出不含明文密码的 MySQL 连接串（密码走环境变量）；
6. 用 `text()` 执行原生 SQL 并完成 `:name` 参数绑定——本仓库硬规范。

## 2.1 前置知识 / 本章地位

第 1 章用裸 SQL 问数据，本章把 SQL 包进 Python 对象。SQLAlchemy 是 Python 生态事实上的数据库工具标准：向下（Core 层）提供连接池与 SQL 表达式语言，向上（ORM 层）提供「类 ↔ 表、对象 ↔ 行」的映射。它是第 06 篇 FastAPI 数据库集成的指定工具（FastAPI 官方教程也用它），也是第 3~5 章 pandas `read_sql` 最常见的连接来源。

实测环境：SQLAlchemy 2.0.50。**本教程统一 2.0 风格**——`DeclarativeBase` 基类 + `Mapped`/`mapped_column` 类型注解；网上大量 1.x 的 `declarative_base()` / `Query` 风格代码请勿照抄，2.0 起旧写法已逐步淘汰。

## 2.2 ORM 何时用、何时别用

ORM 解决的问题是「Python 对象与关系表的翻译」：把「写 SQL → 拿行元组 → 手工转对象」的样板代码收敛成对对象属性的直接操作。它不是「不会 SQL 的挡箭牌」——第 1 章的功力直接决定你写的 ORM 查询质量（生成的 SQL 依然要能看懂）。

| 场景 | 建议 | 理由 |
|---|---|---|
| Web 后端的常规增删改查、多表对象图 | ORM | 类型安全、可组合、防注入天然成立 |
| 复杂报表（多层聚合、窗口函数、DBA 调优过的 SQL） | 原生 SQL（`text()`） | ORM 表达这些要么写不出、要么生成的 SQL 更难懂 |
| 一次性脚本 / pandas 交互分析 | 直接 DBAPI 或 `read_sql` | 杀鸡不必用牛刀 |
| 亿级数据批量 ETL | 数据库原生工具（LOAD DATA 等） | ORM 逐行对象化开销大 |

一句话：**对象图复杂、业务规则多 → ORM；查询本身是难点 → 原生 SQL**。两者在同一项目混用是常态，SQLAlchemy 对此完全支持。

## 2.3 Core 与 ORM：同一个库的两个层次

```mermaid
flowchart TB
    subgraph ORM["ORM 层（第 2.5 节）"]
        S["Session<br/>工作单元/身份映射"] --> M["模型类 Book<br/>DeclarativeBase"]
    end
    subgraph Core["Core 层（第 2.4 节）"]
        E["Engine<br/>连接池 + 方言"] --> C["Connection<br/>一次物理连接"]
        C --> T["text() / select()<br/>SQL 表达式"]
    end
    S --> E
    M --> E
```

- **Core**：Engine 管连接池，Connection 代表一次连接，SQL 用 `text()`（原生字符串）或表达式语言（`select()`）描述；
- **ORM**：Session 建立在 Engine 之上，追踪对象变化（工作单元 Unit of Work），`flush()` 时才把变更翻译成 SQL。

第 07 章实战会同时用到两层：pandas 抽取走 Core 的 Connection，FastAPI 侧的业务模型走 ORM。

## 2.4 Engine 与 Connection：连接怎么来

Engine 全局**只建一次**（内部是连接池），URL 格式 `dialect+driver://user:password@host:port/dbname`：

```python
from sqlalchemy import create_engine

# SQLite：三个斜杠是相对/绝对路径，四个斜杠是绝对路径（/ 开头）
engine = create_engine("sqlite:///data/lab02.db")

# MySQL（部署见 Ubuntu 篇第 8 章；密码绝不能写进代码，见 2.8 节）
# engine = create_engine("mysql+pymysql://bookuser:<your-password>@127.0.0.1:3306/books")
```

Connection 用完即关（`with` 块退出时归还连接池）：

```python
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(
        text("SELECT title, price FROM books WHERE rating >= :r AND price <= :p ORDER BY price DESC LIMIT :n"),
        {"r": 4, "p": 30.0, "n": 3},
    )
    for row in result:
        print(row)
```

预期输出（脚本 `02_sqlalchemy_orm.py` 真实运行）：

```text
   ('Frostbite (Vampire Academy #2)', 29.99)
   ('At The Existentialist Café: Freedom, Being, and apricot cocktails with: Jean-Paul Sartre, Simone de Beauvoir, Albert Camus, Martin Heidegger, Edmund Husserl, Karl Jaspers, Maurice Merleau-Ponty and others', 29.93)
   ('All the Light We Cannot See', 29.87)
   5 星书: {'n': 196, 'avg_price': 35.37}
```

> ⚠️ **硬规范在这里同样生效**：`text()` 里的 `:r / :p / :n` 是绑定参数（Bind Parameter），值放在第二个参数的字典里。拼接进 `text()` 字符串 = 第 1 章 1.9 节的同款反面案例，评审一律打回。参数名前不加冒号值、`LIMIT :n` 这类位置也可以绑定（MySQL 侧同理）。

## 2.5 Session 与 2.0 风格模型

### 2.5.1 定义模型

2.0 风格的核心是类型注解：`Mapped[...]` 声明 Python 类型，`mapped_column()` 补充约束。实验脚本里的 `Book` 模型与本仓库爬虫项目 `projects/book-insight/api/models.py` 完全对齐（那张真实的 `books` 表）：

```python
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    upc: Mapped[str | None] = mapped_column(String(32), unique=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    price: Mapped[float | None]          # 简写：类型即可推断列类型
    availability: Mapped[int | None]
    rating: Mapped[int | None]
    category: Mapped[str | None] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)
    # ...其余列见脚本
```

三个细节：`str | None` 表示该列可为 NULL——**模型类型注解与表结构一致**是 2.0 风格的精髓；`Mapped[float | None]` 不写 `mapped_column` 时 SQLAlchemy 按类型自动推断；模型对齐已有表时**不要**加 `Base.metadata.create_all()` 建表语句（表已存在，建表是爬虫项目的事，ORM 只做映射）。

### 2.5.2 Session 查询

Session 是 ORM 的工作台，2.0 风格统一用 `select()` 语句：

```python
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

with Session(engine) as session:
    stmt = select(Book).where(Book.rating >= 5).order_by(desc(Book.price)).limit(3)
    for book in session.scalars(stmt):
        print(book)
```

预期输出（`__repr__` 由脚本自定义）：

```text
   Book(id=565, title='The Barefoot Contessa Cookbook', price=59.92, rating=5)
   Book(id=817, title='Life Without a Recipe', price=59.04, rating=5)
   Book(id=642, title='Approval Junkie: Adventures in Caring Too Much', price=58.81, rating=5)
```

**常用查询对照表**（左边是你要的语义，右边是 2.0 写法）：

| 语义 | 2.0 写法 |
|---|---|
| 条件过滤 | `select(Book).where(Book.rating == 5, Book.price < 20)`（多个条件逗号分隔即 AND） |
| 模糊匹配 | `where(Book.title.like("%Python%"))` / `ilike` 忽略大小写 |
| 排序截取 | `.order_by(desc(Book.price)).limit(3)` |
| 计数聚合 | `func.count()` / `func.avg(Book.price)` |
| 分组 | `.group_by(Book.category)` |
| 只取一列 | `session.scalars(select(Book.title))` |

**聚合 + 分组**（等价于第 1 章 1.5 节的 SQL）：

```python
from sqlalchemy import func

stmt = (
    select(Book.category, func.count().label("n"), func.avg(Book.price).label("avg_price"))
    .group_by(Book.category)
    .order_by(desc("n"))
    .limit(3)
)
for row in session.execute(stmt):
    print(row.category, row.n, round(row.avg_price, 2))
```

预期输出：

```text
   Default 152 34.39
   Nonfiction 110 34.26
   Sequential Art 75 34.57
```

**相关标量子查询**（「价格高于本分类均价」）用 `scalar_subquery()` 表达，ORM 生成与你手写等价的 SQL：

```python
sub = select(func.avg(Book.price)).where(Book.category == Book.category).scalar_subquery()
stmt = select(Book.title, Book.price).where(Book.price > sub).limit(3)
```

预期输出：

```text
   ('A Light in the Attic', 51.77)
   ('Tipping the Velvet', 53.74)
   ('Soumission', 50.1)
```

## 2.6 CRUD 与事务回滚

ORM 的写操作围绕 Session 的生命周期：`add()` 进入暂存 → `flush()` 生成 SQL 但不提交 → `commit()` 提交事务。脚本 `02_sqlalchemy_orm.py` 在 `books` 表的**副本库**上完整走了一遍（源库只读）：

**Create**——构造对象、add、flush 拿自增主键：

```python
new_book = Book(upc="teach000000001", title="SQLAlchemy 2.0 入门（演示行）",
                price=9.99, rating=5, category="Default",
                detail_url="https://books.toscrape.com/catalogue/teaching-row/index.html")
session.add(new_book)
session.flush()          # 生成 INSERT，new_book.id 可用，但事务未提交
session.commit()         # 落库
print("commit 后 id =", new_book.id)
```

预期输出：

```text
flush 后（事务内可见）: Book(id=1005, title='SQLAlchemy 2.0 入门（演示行）', price=9.99, rating=5)
commit 后 id = 1005
```

**Update**——改对象属性即改行（默认在下次 flush 时生成 UPDATE）：

```python
with Session(engine) as s2:
    obj = s2.scalar(select(Book).where(Book.upc == "teach000000001"))
    obj.price = 15.0
    s2.rollback()        # 反悔了：未 commit 的修改整体丢弃
    s2.refresh(obj)      # 从数据库重新加载，回到已提交状态
    print("rollback + refresh 后 price =", obj.price)
```

预期输出：

```text
rollback + refresh 后 price = 12.49
```

（12.49 是上一步 commit 过的值——rollback 只撤销 15.0 这次未提交的修改，这正是事务的意义：**commit 之前的一切都可以整批反悔**。）

**Delete**——`session.delete(obj)` + `commit()`：

```python
s2.delete(obj)
s2.commit()
print("delete + commit 后再查:", s2.scalar(select(Book).where(Book.upc == "teach000000001")))
```

预期输出：

```text
delete + commit 后再查: None
```

Session 生命周期守则：**短事务**（随用随开、用完即关）；一个请求一个 Session（FastAPI 依赖注入时天然如此）；只在 Session 内修改它的对象。

## 2.7 MySQL 连接串与密码安全

连接 MySQL（Ubuntu 服务器部署见 [Ubuntu 篇第 8 章](../02-linux-ubuntu/08-MySQL部署与数据库运维.md)）时，URL 里嵌着账号密码——**把密码写进代码或配置文件再提交进 git 是本仓库红线**。标准做法是密码从环境变量读，URL 用 `URL.create()` 结构化构造（它负责转义密码里的特殊字符，比手工拼 URL 安全）：

```python
import os
from sqlalchemy import URL

mysql_url = URL.create(
    drivername="mysql+pymysql",          # MySQL 方言 + pymysql 驱动
    username="bookuser",
    password=os.environ["MYSQL_PASSWORD"],  # 从环境变量取，不在代码中出现
    host="127.0.0.1",
    port=3306,
    database="books",
)
engine = create_engine(mysql_url)
```

配合 `.env` + `.gitignore` 方案（本仓库密钥管理规范，见第 03 篇第 6 章）：`.env` 里写 `MYSQL_PASSWORD=<your-password>` 并加入 `.gitignore`，代码里用 `python-dotenv` 加载。验证 URL 时用 `render_as_string(hide_password=True)` 打印，脚本真实输出形如：

```text
MySQL URL 写法示例: mysql+pymysql://bookuser:***@127.0.0.1:3306/books
```

连不上 MySQL 时按三步排查：服务是否启动（`systemctl status mysql`）→ 账号能否本机登录（`mysql -u bookuser -p`）→ 驱动是否安装（`pip install pymysql`）。

## 2.8 pandas 结合预告：read_sql 同样参数绑定

`pandas.read_sql` 接受 SQLAlchemy Connection（第 3 章正式展开），条件同样必须走绑定参数——`:name` 占位符 + `params` 字典：

```python
import pandas as pd

with engine.connect() as conn:
    df = pd.read_sql(
        text("SELECT category, price, rating FROM books WHERE rating >= :r"),
        conn,
        params={"r": 5},
    )
print(df.groupby("category").size().sort_values(ascending=False).head(3).to_string())
```

预期输出（脚本真实运行）：

```text
category
Default       29
Nonfiction    20
Fiction       17
```

这是第 07 章全流程实战的标准抽取姿势：SQLAlchemy 管连接与安全，pandas 管分析。

## 常见坑与排查（Troubleshooting）

| 报错/现象 | 原因 | 解决办法 |
|---|---|---|
| `NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:mysql` | 驱动没装或 URL 方言写错 | `pip install pymysql`；URL 写 `mysql+pymysql://` |
| `OperationalError: no such table: books` | 连错了库/路径，或 SQLite 相对路径随 cwd 漂移 | 打印 `engine.url` 核对；SQLite 建议绝对路径（四斜杠） |
| `ArgumentError`：text() 有冒号但没传 params | 占位符与参数字典不匹配 | 每个冒号名都要在 params 里有键；无参数时不要写冒号 |
| 改了属性但库里没变 | 忘记 `session.commit()` | flush 只生成 SQL，commit 才落库 |
| `InvalidRequestError: This session is provisioning a new connection` | 跨线程共用 Session | Session 非线程安全，一线程一 Session |
| 修改对象后重查仍是旧值 | 对象已过期/在另一 Session 中 | 用同一 Session 的 `refresh(obj)`，或重新查询 |
| 模型加字段后查询报 no such column | ORM 模型与真实表结构不同步 | 模型只映射真实存在的列；改表用迁移工具（Alembic，进阶） |
| 大批量 `add()` 循环巨慢 | 逐行对象化 + 逐行 flush | 改 `bulk_insert_mappings` 或直接 DBAPI `executemany` |
| 密码含 `@#` 等字符连不上 | 手拼 URL 未转义 | 用 `URL.create()` 构造，由它负责转义 |
| `detach` 后连接泄漏、文件被占用 | SQLite 连接未释放 | 引擎用完 `engine.dispose()`；连接用 `with` |

## 动手练习

（在 `projects/data-analysis-lab/data/lab02.db` 副本上完成，跑一遍 `02_sqlalchemy_orm.py` 即生成）

1. **查询改写**：把第 1 章练习 1 的 SQL（库存 <3 且 5 星）改写成 ORM：`select(Book).where(...)`。（验收：与 SQL 版行数一致，均为 22 行）
2. **聚合**：用 `func` 统计每个评分档的书目数与平均价格，按评分排序。（验收：5 档计数之和为 1000）
3. **事务**：add 一个新 Book 对象 → flush → rollback，再查询确认不存在；然后再 add → flush → commit，确认 id 已占用（自增不复用）。
4. **参数绑定抽查**：把 `pd.read_sql` 的条件换成「分类由变量 `cat` 决定」，用 `:name` 绑定实现，并对 `cat` 传入含引号的恶意字符串验证不会报错也不会查出多余数据。

<details>
<summary>练习 1 提示</summary>

`stmt = select(Book).where(Book.availability < 3, Book.rating == 5).order_by(Book.availability)`，用 `len(session.scalars(stmt).all())` 验证行数。注意 where 里两个条件用逗号分隔即 AND，不需要写 `and_`。
</details>

## 小结与自检清单

- [ ] 能对着场景说出「这里用 ORM / 这里用原生 SQL」并给出理由；
- [ ] 能画出 Engine → Connection → Session 的层次图，知道连接池在谁手里；
- [ ] 能用 2.0 风格写出一个与真实表对齐的模型（`DeclarativeBase` + `Mapped` + `mapped_column`）；
- [ ] 能完成 add/flush/commit、属性修改、delete 三类写操作并验证落库；
- [ ] 能解释 rollback 撤销了什么、refresh 重新加载了什么；
- [ ] MySQL 连接串的密码从环境变量读取，知道 `URL.create()` 的意义；
- [ ] `text()` 原生 SQL 全部用 `:name` 绑定，能一眼指出拼接式写法的错误；
- [ ] 知道 `pd.read_sql(text(...), conn, params={...})` 是第 07 章的标准抽取姿势。

## 延伸阅读

- [SQLAlchemy 2.0 官方教程](https://docs.sqlalchemy.org/en/20/tutorial/) —— 本章节结构与术语（Core/ORM、Unit of Work）的权威出处；
- [SQLAlchemy: Declarative Mapping](https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html) —— `Mapped`/`mapped_column` 完整规则与各列类型；
- [SQLAlchemy: Working with Engines and Connections](https://docs.sqlalchemy.org/en/20/core/connections.html) —— 连接池、事务边界与 `text()` 绑定参数细节；
- [python-dotenv 文档](https://saurabh-kumar.com/python-dotenv/) —— `.env` 方案的标准实现；
- 前后章节：[第 1 章 SQL](01-SQL从入门到进阶(MySQL).md)（ORM 生成的 SQL 要能看懂）、[第 3 章 pandas 入门](03-pandas入门(核心数据结构).md)（read_sql 正式展开）。
