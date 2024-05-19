from celery import Celery

app = Celery('tasks', broker='음.. json으로 땜빵하기는 힘들어 보이는데')