"""Nghiệp vụ thư viện. Chỉ dùng thư viện chuẩn Python; không cần pip."""
import re
import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path


class RuleError(ValueError):
    pass


def today():
    return date.today()


@contextmanager
def connect(path):
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    try:
        with db:
            yield db
    finally:
        db.close()


def init_db(path, seed=True):
    with connect(path) as db:
        db.executescript(Path(__file__).with_name('schema.sql').read_text(encoding='utf-8'))
        if db.execute('PRAGMA user_version').fetchone()[0] == 0:
            if seed:
                seed_data(db)
            db.execute('PRAGMA user_version = 1')


def seed_data(db):
    books = [
        ('Lập trình Python cơ bản', 'Nguyễn Minh An', 'Công nghệ', 'NXB Học tập', 2024, 'DEMO-001'),
        ('Cơ sở dữ liệu quan hệ', 'Trần Hoài Nam', 'Công nghệ', 'NXB Học tập', 2023, 'DEMO-002'),
        ('Nhập môn kinh tế học', 'Lê Thanh Mai', 'Kinh tế', 'NXB Tri thức', 2022, 'DEMO-003'),
        ('Hành trình đọc sách', 'Phạm Thu Hà', 'Văn học', 'NXB Tri thức', 2024, 'DEMO-004'),
        ('Tiếng Anh mỗi ngày', 'Đỗ Minh Châu', 'Ngoại ngữ', 'NXB Học tập', 2025, 'DEMO-005'),
        ('Tư duy thiết kế hệ thống', 'Võ Gia Bảo', 'Công nghệ', 'NXB Học tập', 2025, 'DEMO-006'),
        ('Xác suất và thống kê', 'Bùi Khánh Linh', 'Khoa học', 'NXB Tri thức', 2023, 'DEMO-007'),
        ('Kỹ năng học tập hiệu quả', 'Hoàng Anh Tú', 'Kỹ năng', 'NXB Tri thức', 2024, 'DEMO-008'),
    ]
    db.executemany('INSERT INTO books(title,author,category,publisher,year,isbn) VALUES(?,?,?,?,?,?)', books)
    for book_id in range(1, 9):
        for n in range(1, 4):
            db.execute('INSERT INTO copies(book_id,code,shelf) VALUES(?,?,?)',
                       (book_id, f'S{book_id:03}-{n:02}', f'{chr(64 + (book_id+1)//2)}-{book_id:02}'))
    for i, name in enumerate(['Nguyễn An (mẫu)', 'Trần Bình (mẫu)', 'Lê Chi (mẫu)', 'Phạm Dũng (mẫu)'], 1):
        db.execute('INSERT INTO readers(code,name,email,phone,expires) VALUES(?,?,?,?,?)',
                   (f'DG{i:03}', name, f'docgia{i}@example.com', '', (today()+timedelta(days=365)).isoformat()))
    for reader, copy, age, length, returned in [(1, 1, 20, 14, None), (2, 4, 3, 14, None), (3, 7, 10, 14, 5)]:
        borrowed = today()-timedelta(days=age)
        db.execute('INSERT INTO loans(reader_id,copy_id,borrowed,due,returned,return_condition) VALUES(?,?,?,?,?,?)',
                   (reader, copy, borrowed.isoformat(), (borrowed+timedelta(days=length)).isoformat(),
                    (today()-timedelta(days=returned)).isoformat() if returned else None,
                    'available' if returned else None))
    db.execute("UPDATE copies SET condition='damaged' WHERE id=24")


def required(data, key, limit=200):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
        raise RuleError(f'{key}: bắt buộc nhập, tối đa {limit} ký tự.')
    return value.strip()


def optional(data, key, limit=200):
    value = data.get(key, '')
    if not isinstance(value, str) or len(value.strip()) > limit:
        raise RuleError(f'{key}: tối đa {limit} ký tự.')
    return value.strip()


def integer(value, label, minimum=1, maximum=2147483647):
    if isinstance(value, bool) or not re.fullmatch(r'\d+', str(value)):
        raise RuleError(f'{label}: phải là số nguyên.')
    number = int(value)
    if not minimum <= number <= maximum:
        raise RuleError(f'{label}: từ {minimum} đến {maximum}.')
    return number


def parse_date(value):
    try:
        if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            raise ValueError()
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        raise RuleError('Ngày phải hợp lệ và có định dạng YYYY-MM-DD.') from None


def get(db, table, identifier):
    # table chỉ đến từ hằng số nội bộ, không đến từ request.
    row = db.execute(f'SELECT * FROM {table} WHERE id=?', (integer(identifier, 'ID'),)).fetchone()
    if row is None:
        raise RuleError('Không tìm thấy bản ghi.')
    return row


def reader_eligible(db, reader_id):
    reader = get(db, 'readers', reader_id)
    if not reader['active'] or parse_date(reader['expires']) < today():
        raise RuleError('Thẻ độc giả bị khóa hoặc hết hạn.')
    if db.execute('SELECT 1 FROM loans WHERE reader_id=? AND returned IS NULL AND due<?',
                  (reader['id'], today().isoformat())).fetchone():
        raise RuleError('Độc giả còn sách quá hạn; cần trả trước khi mượn/gia hạn.')
    return reader


def snapshot(db):
    books = [dict(r) for r in db.execute('SELECT * FROM books ORDER BY id DESC')]
    copies = [dict(r) for r in db.execute('''SELECT c.*, b.title,b.author,b.category,
       CASE WHEN l.id IS NOT NULL THEN 'borrowed' ELSE c.condition END AS status
       FROM copies c JOIN books b ON b.id=c.book_id
       LEFT JOIN loans l ON l.copy_id=c.id AND l.returned IS NULL ORDER BY c.id''')]
    readers = [dict(r) for r in db.execute('SELECT * FROM readers ORDER BY id DESC')]
    loans = [dict(r) for r in db.execute('''SELECT l.*,r.name,r.code AS reader_code,
       c.code AS copy_code,b.title FROM loans l JOIN readers r ON r.id=l.reader_id
       JOIN copies c ON c.id=l.copy_id JOIN books b ON b.id=c.book_id ORDER BY l.id DESC''')]
    for loan in loans:
        end = parse_date(loan['returned']) if loan['returned'] else today()
        loan['overdue_days'] = max(0, (end - parse_date(loan['due'])).days)
    return dict(books=books,copies=copies,readers=readers,loans=loans,today=today().isoformat())


def mutate(db, action, data):
    """Được gọi bên trong một giao dịch BEGIN IMMEDIATE để tránh mượn trùng."""
    if action in ('books/create', 'books/update'):
        args = (required(data,'title'), required(data,'author'), required(data,'category',80),
                optional(data,'publisher'), integer(data.get('year'),'Năm xuất bản',1000,today().year),
                required(data,'isbn',40))
        if action.endswith('create'):
            return db.execute('INSERT INTO books(title,author,category,publisher,year,isbn) VALUES(?,?,?,?,?,?)',args).lastrowid
        row = get(db,'books',data.get('id'))
        db.execute('UPDATE books SET title=?,author=?,category=?,publisher=?,year=?,isbn=? WHERE id=?',args+(row['id'],))
    elif action == 'books/delete':
        row = get(db,'books',data.get('id'))
        if db.execute('SELECT 1 FROM copies WHERE book_id=?',(row['id'],)).fetchone():
            raise RuleError('Hãy xóa các bản sao chưa có lịch sử trước; đầu sách có bản sao không thể xóa.')
        db.execute('DELETE FROM books WHERE id=?',(row['id'],))
    elif action == 'copies/create':
        book = get(db,'books',data.get('book_id'))
        return db.execute('INSERT INTO copies(book_id,code,shelf) VALUES(?,?,?)',
                          (book['id'],required(data,'code',40),required(data,'shelf',40))).lastrowid
    elif action in ('copies/update','copies/delete'):
        row = get(db,'copies',data.get('id'))
        if action.endswith('delete'):
            if db.execute('SELECT 1 FROM loans WHERE copy_id=?',(row['id'],)).fetchone():
                raise RuleError('Không thể xóa bản sao đã có lịch sử mượn.')
            db.execute('DELETE FROM copies WHERE id=?',(row['id'],))
        else:
            condition = required(data,'condition',20)
            if condition not in ('available','damaged','lost'):
                raise RuleError('Tình trạng bản sao không hợp lệ.')
            if db.execute('SELECT 1 FROM loans WHERE copy_id=? AND returned IS NULL',(row['id'],)).fetchone():
                raise RuleError('Bản sao đang được mượn; hãy xử lý tại Trả sách.')
            db.execute('UPDATE copies SET code=?,shelf=?,condition=? WHERE id=?',
                       (required(data,'code',40),required(data,'shelf',40),condition,row['id']))
    elif action in ('readers/create','readers/update'):
        expires = parse_date(data.get('expires')).isoformat()
        email = optional(data,'email',120)
        if email and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):
            raise RuleError('Email không hợp lệ.')
        phone = optional(data,'phone',20)
        if phone and not re.fullmatch(r'[+\d ()-]{7,20}',phone):
            raise RuleError('Số điện thoại không hợp lệ.')
        args = (required(data,'code',40),required(data,'name',120),email,phone,expires,
                integer(data.get('active',1),'Trạng thái',0,1))
        if action.endswith('create'):
            return db.execute('INSERT INTO readers(code,name,email,phone,expires,active) VALUES(?,?,?,?,?,?)',args).lastrowid
        row = get(db,'readers',data.get('id'))
        db.execute('UPDATE readers SET code=?,name=?,email=?,phone=?,expires=?,active=? WHERE id=?',args+(row['id'],))
    elif action == 'readers/delete':
        row = get(db,'readers',data.get('id'))
        if db.execute('SELECT 1 FROM loans WHERE reader_id=?',(row['id'],)).fetchone():
            raise RuleError('Không thể xóa độc giả có lịch sử mượn; có thể khóa thẻ.')
        db.execute('DELETE FROM readers WHERE id=?',(row['id'],))
    elif action == 'loans/create':
        reader = reader_eligible(db,data.get('reader_id'))
        if db.execute('SELECT COUNT(*) FROM loans WHERE reader_id=? AND returned IS NULL',(reader['id'],)).fetchone()[0] >= 3:
            raise RuleError('Mỗi độc giả chỉ được mượn đồng thời tối đa 3 bản sao.')
        copy = get(db,'copies',data.get('copy_id'))
        if copy['condition'] != 'available' or db.execute('SELECT 1 FROM loans WHERE copy_id=? AND returned IS NULL',(copy['id'],)).fetchone():
            raise RuleError('Bản sao không sẵn sàng cho mượn.')
        return db.execute('INSERT INTO loans(reader_id,copy_id,borrowed,due) VALUES(?,?,?,?)',
                          (reader['id'],copy['id'],today().isoformat(),(today()+timedelta(days=14)).isoformat())).lastrowid
    elif action in ('loans/return','loans/renew'):
        loan = get(db,'loans',data.get('id'))
        if loan['returned']:
            raise RuleError('Phiếu đã trả; không thể thao tác lại.')
        if action.endswith('renew'):
            reader_eligible(db,loan['reader_id'])
            if loan['renewals'] >= 1:
                raise RuleError('Mỗi phiếu chỉ được gia hạn 1 lần.')
            db.execute('UPDATE loans SET due=?,renewals=renewals+1 WHERE id=?',
                       ((parse_date(loan['due'])+timedelta(days=7)).isoformat(),loan['id']))
        else:
            condition = required(data,'condition',20)
            if condition not in ('available','damaged','lost'):
                raise RuleError('Tình trạng trả không hợp lệ.')
            db.execute('UPDATE loans SET returned=?,return_condition=? WHERE id=?',
                       (today().isoformat(),condition,loan['id']))
            db.execute('UPDATE copies SET condition=? WHERE id=?',(condition,loan['copy_id']))
    else:
        raise RuleError('Thao tác không được hỗ trợ.')
    return None
