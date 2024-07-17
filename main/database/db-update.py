import sqlite3

conn = sqlite3.connect('./images.db')
cursor = conn.cursor()

# 이미지 이름별로 origianl_alt가 있는 행과 없는 행 찾기
sql = """
    SELECT image_name, origianl_alt
    FROM images
    WHERE origianl_alt IS NOT NULL
"""
cursor.execute(sql)
rows_with_origianl_alt = cursor.fetchall()

sql = """
    SELECT image_name, origianl_alt
    FROM images
    WHERE origianl_alt IS NULL
"""
cursor.execute(sql)
rows_without_origianl_alt = cursor.fetchall()

# 이미지 이름별로 origianl_alt 복사
for image_name, origianl_alt in rows_with_origianl_alt:
    for row in rows_without_origianl_alt:
        if row[0] == image_name:
            sql = """
                UPDATE images
                SET origianl_alt = %s
                WHERE image_name = %s AND origianl_alt IS NULL
            """
            cursor.execute(sql, (origianl_alt, image_name))
            conn.commit()

# 데이터베이스 연결 종료
conn.close()

