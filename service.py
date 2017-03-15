import MySQLdb
import datetime
import time
import logging
import config
app.config.from_pyfile('config.py')

class AutoService():

	def _init_(self,dbname="oil5k",host="DBUSER",user="DBHOST",password="DBPASS"):
		self.dbname=dbname
		self.host=host
		self.user=user
		self.password=password
		try:	
			db = MySQLdb.connect (host =self.host,user = self.user, passwd = self.passwd, db = self.db)
			cursor = db.cursor()
		except MySQLdb.Error, e:
			logging.info(e.args)
			sys.exit(1)


	def check_if_car_exists(self,car_dict):
		self.cursor.execute("""select count(*) from car_list  where make_year= %s 
			and (lower(concat(make,' ',model)) = '%s' or lower(concat(%s)) = 'pontiac g6' )""",(car_array[:make_year],car_array[:make],car_array[:make]))
		result=self.cursor.fetchone()
		if result == 0:
			return False
		else:
			return True


	def build_user_dict(self,car_dict):
		user_dict={}
		self.cursor.execute("""select make,mode,make_year from car_list  where make_year= %s 
			and (lower(concat(make,' ',model)) = '%s' or lower(concat(%s)) = 'pontiac g6' )""",(car_array[:make_year],car_array[:make],car_array[:make]))
		results=self.cursor.fetchall()
		num_records = len(cursor.fetchall())
		if self.check_if_car_exists(car_dict)==True:
			if num_records == 1:
				user_dict[:make]=result[0]
				user_dict[:model]=result[1]
				user_dict[:year]=result[2]
			elif num_records > 1:
				results=cursor.fetchone()
				user_dict[:make]=result[0]
				user_dict[:model]=result[1]
				user_dict[:year]=result[2]
		self.db.close()
		return user_dict

	def check_active_session(self,sender_id):
		self.cursor.execute("""select count(*) from session_track where sender_id = %s and status is null""",user_dict[:sender_id])
		timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
		result = self.cursor.fetchone()
		if result == 0:
			return True
		else:
			return False


	def record_session(self,user_dict):		
		timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
		
		if self.check_active_session(user_dict[:sender_id]) is True:
			self.cursor.execute("""insert into session_track (sender_id,recipient_id,seq_id,status,creation_time)
				              values (%s,%s,%s,%s,%s)""",(user_dict[:sender_id],user_dict[:recipient_id],user_dict[:seq_id],user_dict[:status],timestamp))
		else:
			self.cursor.execute("""update session_track set status=%s ,updated_time=%s,seq_id=%s where sender_id=%s""",
				(user_dict[:status],timestamp,user_dict[:seq_id]))

		self.db.commit()
		self.db.close()

	def get_service():
		pass

	def book_appt():
		pass




			


			












    