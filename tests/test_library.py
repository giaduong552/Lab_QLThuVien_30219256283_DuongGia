"""Kiểm thử trên SQLite tạm, không thay đổi dữ liệu demo."""
import concurrent.futures
import json
import io
import email.parser
import sqlite3
import sys
import tempfile
import threading
import unittest
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from core import RuleError, connect, init_db, mutate, snapshot
from app import ThreadingHTTPServer, make_handler


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)/'test.db'
        init_db(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def act(self,action,**data):
        with connect(self.path) as db:
            db.execute('BEGIN IMMEDIATE')
            return mutate(db,action,data)

    def state(self):
        with connect(self.path) as db:
            return snapshot(db)

    def test_01_seed_and_stock(self):
        s=self.state()
        self.assertEqual([len(s[k]) for k in ('books','copies','readers','loans')],[8,24,4,3])
        self.assertEqual(sum(c['status']=='available' for c in s['copies']),21)

    def test_02_create_book_and_copy(self):
        identifier=self.act('books/create',title='Sách mới',author='Tác giả',category='Khoa học',year=2024,isbn='TEST')
        self.act('copies/create',book_id=identifier,code='NEW-01',shelf='A1')
        self.assertEqual(len(self.state()['copies']),25)

    def test_03_duplicate_isbn_rolls_back(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.act('books/create',title='Sách',author='A',category='B',year=2024,isbn='DEMO-001')
        self.assertEqual(len(self.state()['books']),8)

    def test_04_blank_and_future_year_rejected(self):
        for title,year in [(' ',2024),('Sách',date.today().year+1)]:
            with self.subTest(title=title,year=year),self.assertRaises(RuleError):
                self.act('books/create',title=title,author='A',category='B',year=year,isbn='X')

    def test_05_borrow_and_due_date(self):
        identifier=self.act('loans/create',reader_id=4,copy_id=2)
        loan=next(l for l in self.state()['loans'] if l['id']==identifier)
        self.assertEqual(loan['due'],(date.today()+timedelta(days=14)).isoformat())
        self.assertEqual(next(c for c in self.state()['copies'] if c['id']==2)['status'],'borrowed')

    def test_06_double_borrow_rejected(self):
        with self.assertRaises(RuleError):
            self.act('loans/create',reader_id=4,copy_id=1)

    def test_07_three_book_limit(self):
        for copy in (2,3,5):
            self.act('loans/create',reader_id=4,copy_id=copy)
        with self.assertRaises(RuleError):
            self.act('loans/create',reader_id=4,copy_id=6)

    def test_08_overdue_reader_blocked(self):
        with self.assertRaises(RuleError):
            self.act('loans/create',reader_id=1,copy_id=2)

    def test_09_expired_or_locked_reader_blocked(self):
        for active,expires in [(0,date.today()),(1,date.today()-timedelta(days=1))]:
            with connect(self.path) as db:
                db.execute('UPDATE readers SET active=?,expires=? WHERE id=4',(active,expires.isoformat()))
            with self.subTest(active=active),self.assertRaises(RuleError):
                self.act('loans/create',reader_id=4,copy_id=2)

    def test_10_card_valid_on_expiration_day(self):
        with connect(self.path) as db:
            db.execute('UPDATE readers SET expires=? WHERE id=4',(date.today().isoformat(),))
        self.assertIsInstance(self.act('loans/create',reader_id=4,copy_id=2),int)

    def test_11_damaged_or_lost_copy_blocked(self):
        for condition in ('damaged','lost'):
            with connect(self.path) as db:
                db.execute('UPDATE copies SET condition=? WHERE id=2',(condition,))
            with self.subTest(condition=condition),self.assertRaises(RuleError):
                self.act('loans/create',reader_id=4,copy_id=2)

    def test_12_renew_once(self):
        before=next(l for l in self.state()['loans'] if l['id']==2)['due']
        self.act('loans/renew',id=2)
        after=next(l for l in self.state()['loans'] if l['id']==2)
        self.assertEqual(after['due'],(date.fromisoformat(before)+timedelta(days=7)).isoformat())
        with self.assertRaises(RuleError):
            self.act('loans/renew',id=2)

    def test_13_overdue_renew_blocked(self):
        with self.assertRaises(RuleError):
            self.act('loans/renew',id=1)

    def test_14_return_damaged_and_no_repeat(self):
        self.act('loans/return',id=2,condition='damaged')
        self.assertEqual(next(c for c in self.state()['copies'] if c['id']==4)['status'],'damaged')
        with self.assertRaises(RuleError):
            self.act('loans/return',id=2,condition='available')
        with self.assertRaises(RuleError):
            self.act('loans/renew',id=2)

    def test_15_return_available_can_reborrow(self):
        self.act('loans/return',id=2,condition='available')
        self.act('loans/create',reader_id=4,copy_id=4)

    def test_16_protect_history(self):
        for action,data in [('readers/delete',{'id':1}),('copies/delete',{'id':1}),('books/delete',{'id':1})]:
            with self.subTest(action=action),self.assertRaises(RuleError):
                self.act(action,**data)

    def test_17_invalid_contact_and_date(self):
        for changes in [dict(email='invalid'),dict(expires='2026-02-30'),dict(phone='abc123')]:
            data=dict(code='R5',name='Mẫu',email='',phone='',expires='2027-12-31')
            data.update(changes)
            with self.subTest(changes=changes),self.assertRaises(RuleError):
                self.act('readers/create',**data)

    def test_18_copy_in_loan_cannot_be_edited(self):
        with self.assertRaises(RuleError):
            self.act('copies/update',id=1,code='EDIT',shelf='A',condition='available')

    def test_19_seed_not_repeated_and_persistence(self):
        self.act('loans/return',id=2,condition='lost')
        init_db(self.path)
        self.assertEqual(len(self.state()['loans']),3)
        self.assertEqual(next(c for c in self.state()['copies'] if c['id']==4)['status'],'lost')

    def test_20_concurrent_borrow_exactly_one_success(self):
        def attempt():
            try:
                self.act('loans/create',reader_id=4,copy_id=2)
                return True
            except RuleError:
                return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results=list(pool.map(lambda _:attempt(),range(2)))
        self.assertEqual(sum(results),1)

    def test_21_update_and_delete_unused_records(self):
        r=self.act('readers/create',code='X',name='Tên',expires='2027-12-31')
        self.act('readers/update',id=r,code='X',name='Tên mới',expires='2027-12-31',active=0)
        self.assertEqual(next(x for x in self.state()['readers'] if x['id']==r)['name'],'Tên mới')
        self.act('readers/delete',id=r)
        self.act('copies/delete',id=2)
        self.assertEqual(len(self.state()['copies']),23)

    def test_22_due_today_is_not_overdue(self):
        with connect(self.path) as db:
            db.execute('UPDATE loans SET due=? WHERE id=1',(date.today().isoformat(),))
        self.act('loans/renew',id=1)


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        path=Path(cls.temp.name)/'http.db'
        init_db(path)
        cls.handler=make_handler(path)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def request(self,path,body=None,headers=None):
        # Gửi HTTP thô qua stream trong bộ nhớ: kiểm tra parser, header và
        # handler thật, không phụ thuộc quyền mở kết nối mạng của môi trường.
        headers=dict(headers or {})
        headers['Host']='127.0.0.1:8000'
        if body is not None:
            headers['Content-Length']=str(len(body))
        method='POST' if body is not None else 'GET'
        raw=(f'{method} {path} HTTP/1.0\r\n'+''.join(f'{k}: {v}\r\n' for k,v in headers.items())+'\r\n').encode()+(body or b'')
        class StreamSocket:
            def __init__(self):
                self.output=io.BytesIO()
            def makefile(self,*args,**kwargs):
                return io.BytesIO(raw)
            def sendall(self,data):
                self.output.write(data)
        sock=StreamSocket()
        self.handler(sock,('127.0.0.1',12345),None)
        head,content=sock.output.getvalue().split(b'\r\n\r\n',1)
        result=io.BytesIO(content)
        result.status=int(head.split(b' ',2)[1])
        result.headers=email.parser.Parser().parsestr(head.decode().split('\r\n',1)[1])
        return result

    def test_23_static_and_snapshot(self):
        for path in ('/','/app.js','/style.css','/api/state'):
            with self.subTest(path=path),self.request(path) as result:
                self.assertEqual(result.status,200)
                self.assertIn('Content-Security-Policy',result.headers)
                self.assertGreater(len(result.read()),100)

    def test_24_bad_json_and_type(self):
        for body,headers,code in [(b'{',{'Content-Type':'application/json'},400),
                                  (b'[]',{'Content-Type':'application/json'},400),
                                  (b'{}',{},415)]:
            with self.subTest(body=body,headers=headers),self.request('/api/loans/create',body,headers) as result:
                self.assertEqual(result.status,code)

    def test_25_real_borrow_and_return(self):
        with self.request('/api/loans/create',json.dumps(dict(reader_id=4,copy_id=2)).encode(),{'Content-Type':'application/json'}) as result:
            self.assertEqual(result.status,200)
            identifier=json.load(result)['id']
        with self.request('/api/loans/return',json.dumps(dict(id=identifier,condition='available')).encode(),{'Content-Type':'application/json'}) as result:
            self.assertEqual(result.status,200)

    def test_26_path_traversal_and_foreign_origin(self):
        with self.request('/../schema.sql') as result:
            self.assertEqual(result.status,404)
        with self.request('/api/loans/create',b'{}',{'Content-Type':'application/json','Origin':'https://other.example'}) as result:
            self.assertEqual(result.status,403)


if __name__=='__main__':
    unittest.main(verbosity=2)
