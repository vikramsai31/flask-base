import MySQLdb
import datetime 
from datetime import timedelta
import time
import logging
import config
import sys

class Service():

	def __init__(self,dbname="oil5k",user="adminpBzTcXM",host='127.8.18.2',password="FG1HyeKHUqAD"):
		self.db=dbname
		self.host=host
		self.user=user
		self.passwd=password
		try:	
			self.conn = MySQLdb.connect(host =self.host,user = self.user, passwd = self.passwd, db = self.db)
			self.cursor = self.conn.cursor()
		except MySQLdb.Error, e:
			logging.info(e.args)
			sys.exit(1)


	def check_if_car_exists(self,car_dict):
		self.cursor.execute("""select count(*) from car_list  where make_year= %s 
			and (lower(concat(make,' ',model)) = '%s' or lower(concat(%s)) = 'pontiac g6' )""",(car_array['make_year'],car_array['make'],car_array['make']))
		result=self.cursor.fetchone()
		if result == 0:
			return False
		else:
			return True


	def build_user_dict(self,car_dict):
		user_dict={}
		self.cursor.execute("""select make,mode,make_year from car_list  where make_year= %s 
			and (lower(concat(make,' ',model)) = '%s' or lower(concat(%s)) = '%s' )""",(car_array['make_year'],car_array['make'],car_array['make']))
		results=self.cursor.fetchall()
		num_records = len(cursor.fetchall())
		if self.check_if_car_exists(car_dict)==True:
			if num_records == 1:
				user_dict['make']=result[0]
				user_dict['model']=result[1]
				user_dict['year']=result[2]
			elif num_records > 1:
				results=cursor.fetchone()
				user_dict['make']=result[0]
				user_dict['model']=result[1]
				user_dict['year']=result[2]
		self.db.close()
		return user_dict

        def get_current_state(self,user_dict):
		self.cursor.execute("""select ifnull(status,0) from session_track where sender_id = %s and recipient_id= %s order by creation_time desc limit 1""",(user_dict['sender_id'],user_dict['recipient_id'],))
		result = self.cursor.fetchone()
                if result:
		    return result[0]

       	def check_active_session(self,user_dict):
		if self.get_current_state(user_dict) is None:
			return False
                elif self.get_current_state(user_dict) in ('COMPLETE','INCOMPLETE'):
                        return False
                else:
		    self.cursor.execute("""select count(*) from session_track where creation_time=(select max(creation_time) from session_track where sender_id = %s  and recipient_id= %s  and status not in ('COMPLETE','INCOMPLETE') and creation_time > (now() - INTERVAL 10 MINUTE))""",(user_dict['sender_id'],user_dict['recipient_id'],))
                    result=self.cursor.fetchone()
                    if result[0] == 0:
                        return False
                    else:
                        return True


	def record_session(self,user_dict):		
		timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
		self.cursor.execute("""insert into session_track (sender_id,recipient_id,counter,status,creation_time)
				              values (%s,%s,%s,%s,%s)""",(user_dict['sender_id'],user_dict['recipient_id'],user_dict['counter'],user_dict['status'],timestamp))
		self.conn.commit()
			#self.conn.close()

	def get_information(self,recipient_id):
		dealer_array = []
		self.cursor.execute("""select id,businessname,address,city,state, phone from dealers where facebook_id = %s """,(recipient_id,))
		for deal in self.cursor.fetchall():
			businessname = deal[1]
			address =deal[2]
			dealer_append=(str(deal[1])+' \n '+str(deal[2]) + ' \n '+ str(deal[3]) + ',' + str(deal[4])+'\n Ph:'+str(deal[5]))
			dealer_array.append(dealer_append)
			self.cursor.execute("""select day_of_week,open_at,close_at from dealer_timings where dealer_id = %s """,(deal[0],))
			for timing in self.cursor.fetchall():
		            line = (str(timing[0])+' '+str(timing[1])+ '-' +str(timing[2]))
			    dealer_array.append(line)
		return '\n'.join(dealer_array)

	def get_service_category(self,recipient_id):
		dealer_array = []
		dealer_dict = {}
		self.cursor.execute("""select id from dealers where facebook_id = %s """,(recipient_id,))
		for deal in self.cursor.fetchall():
			self.cursor.execute("""select distinct categories from dealer_services where dealer_id = %s""",(deal[0],))
			for category in self.cursor.fetchall():
				dealer_dict={
				"content_type":"text",
				"title": category[0],
				"payload": "DEVELOPER_DEFINED_CATEGORY",
				}
				dealer_array.append(dealer_dict)

		return dealer_array

	def get_service_list(self,recipient_id,service_name):
		service_array = []
		dealer_dict = {}
                
		self.cursor.execute("""select id from dealers where facebook_id = %s """,(recipient_id,))
		for deal in self.cursor.fetchall():
                        
			self.cursor.execute("""select  concat(service_type,' ',ifnull(service_price,'Price Unavailable')) from dealer_services where dealer_id = %s and lower(categories) = lower(%s)""",(deal[0],service_name,))
			for category in self.cursor.fetchall():
				dealer_dict={
				"content_type":"text",
				"title": category[0],
				"payload": "DEVELOPER_DEFINED_SERVICE",
				}
				service_array.append(dealer_dict)

		return service_array
	
	def get_dealer_info(self,recipient_id):
		self.cursor.execute("""select id from dealers where facebook_id = %s """,(recipient_id,))
		dealer = self.cursor.fetchone()
		if dealer:
			return dealer[0]
		
		
		
	def insert_appt(self,user_dict):
		dealer_id=self.get_dealer_info(user_dict['recipient_id'])
		timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')
		self.cursor.execute("""insert into appointments (dealer_id,sender_id,recipient_id,customer_name,day_of_appt,creation_date) values (%s,%s,%s,%s,%s,%s)""",(dealer_id,user_dict['sender_id'],user_dict['recipient_id'],user_dict['name'],user_dict['day_of_appt'],timestamp))
		self.conn.commit()
	
	def update_appt_window(self,user_dict):
		dealer_id=self.get_dealer_info(user_dict['recipient_id'])
		self.cursor.execute("""update appointments set time_window=%s where sender_id=%s and  recipient_id=%s and creation_date=CURDATE() """,(user_dict['day_of_appt'],user_dict['sender_id'],user_dict['recipient_id']))
		self.conn.commit()
	
	def update_phone_number(self,user_dict):
		dealer_id=self.get_dealer_info(user_dict['recipient_id'])
		self.cursor.execute("""update appointments set phone_number=%s where sender_id=%s and  recipient_id=%s and creation_date=CURDATE() """,(user_dict['phone_number'],user_dict['sender_id'],user_dict['recipient_id']))
		self.conn.commit()
	
	def update_service_category(self,user_dict):
		dealer_id=self.get_dealer_info(user_dict['recipient_id'])
		self.cursor.execute("""update appointments set service_category=%s where sender_id=%s and  recipient_id=%s and creation_date=CURDATE() """,(user_dict['service_category'],user_dict['sender_id'],user_dict['recipient_id']))
		self.conn.commit()

	def update_service_type(self,user_dict):
		dealer_id=self.get_dealer_info(user_dict['recipient_id'])
		self.cursor.execute("""update appointments set service_type=%s where sender_id=%s and  recipient_id=%s and creation_date=CURDATE() """,(user_dict['service_type'],user_dict['sender_id'],user_dict['recipient_id']))
		self.conn.commit()
		
		
	
	def check_if_appt_exists(self,sender_id,day_of_appt):
		dealer_id=self.get_dealer_info(sender_id)
		self.cursor.execute("""select count(*) from appointments where dealer_id = %s and day_of_appt =%s""",(dealer_id,day_of_appt,))
		result = self.cursor.fetchone()
		if result[0] == 0:
			return False
		else:
			return True
	
	def check_appt_today(self,sender_id,recipient_id):
		dealer_id=self.get_dealer_info(sender_id)
		self.cursor.execute("""select count(*) from appointments where sender_id = %s and recipient_id=%s and creation_date =currdate()""",(sender_id,recipient_id,))
		result = self.cursor.fetchone()
		if result[0] == 0:
			return False
		else:
			return True	
		
  

	def get_appt_day(self):
		now = datetime.date.today()
		service_appt_day =[
				{
				"content_type":"text",
				"title": (now + datetime.timedelta(days=1)).strftime("%m-%d-%Y"),
				"payload": "DEVELOPER_DEFINED_APPT_DAY",
				},
				{
				"content_type":"text",
				"title": (now + datetime.timedelta(days=2)).strftime("%m-%d-%Y"),
				"payload": "DEVELOPER_DEFINED_APPT_DAY",
				},
				{
				"content_type":"text",
				"title": (now + datetime.timedelta(days=3)).strftime("%m-%d-%Y"),
				"payload": "DEVELOPER_DEFINED_APPT_DAY",
				}
				]
		return service_appt_day

	def get_time_slot(self):
		time_slot = [
				{
				"content_type":"text",
				"title": "9AM-11AM",
				"payload": "DEVELOPER_DEFINED_TIME_SLOT",
				},
				{
				"content_type":"text",
				"title": "11AM-1PM",
				"payload": "DEVELOPER_DEFINED_TIME_SLOT",
				},
				{
				"content_type":"text",
				"title": "1PM-3PM",
				"payload": "DEVELOPER_DEFINED_TIME_SLOT",
				},
				{
				"content_type":"text",
				"title": "3PM-5PM",
				"payload": "DEVELOPER_DEFINED_TIME_SLOT",
				}
				]
		return time_slot




















			


			












    
