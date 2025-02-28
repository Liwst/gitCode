import sqlite3
from pathlib import Path
from typing import List, Dict


class WeatherDatabase:
    def __init__(self, db_path: Path):
        # 标准化路径并创建目录
        db_path = db_path.absolute()
        db_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.conn = sqlite3.connect(str(db_path))
        except sqlite3.OperationalError as e:
            raise RuntimeError(
                f"无法创建数据库文件：{db_path}\n"
                f"请检查：\n"
                f"1. 路径是否存在\n"
                f"2. 是否具有写入权限\n"
                f"3. 防病毒软件是否拦截"
            ) from e

        self._create_tables()

    def _create_tables(self):
        """初始化数据库表结构"""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS query_history(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                query_type TEXT CHECK(query_type IN ('current', 'forecast')),
                query_time DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def save_query(self, city: str, query_type: str):
        """保存查询记录"""
        self.conn.execute(
            "INSERT INTO query_history (city, query_type) VALUES (?, ?)",
            (city, query_type)
        )
        self.conn.commit()

    def get_history(self, limit: int = 5) -> List[Dict]:
        """获取查询历史"""
        cursor = self.conn.execute(
            "SELECT city, query_type, query_time "
            "FROM query_history ORDER BY query_time DESC LIMIT ?",
            (limit,)
        )
        return [
            {
                "city": row[0],
                "type": row[1],
                "time": row[2]
            } for row in cursor
        ]

    def close(self):
        self.conn.close()
