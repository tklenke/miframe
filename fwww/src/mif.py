from PIL import Image, ImageTk
from PIL.ExifTags import TAGS
import json
import logging
import datetime

#image record
IR_PATH = 0
#path
IR_FILE_SZ = 1
#filesz
IR_FILE_DATE = 2
#filedate
IR_DATETIME_ORIG = 3
#datetimeoriginal
IR_DATETIME_DIG = 4
#datetimedigitized
IR_DATETIME = 5
#datetime
IR_MAKE = 6
#make
IR_MODEL = 7
#model
IR_EXIF_WIDTH = 8
#exifimagewidth
IR_EXIF_HEIGHT = 9
#exifimageheight
IR_EXIF_VER = 10
#exifversion
IR_ORIENTATION = 11
#orientation
#epoch Day
IR_EPOCH_DAY = 12
#year_day
IR_YEAR_DAY = 13
IR_NUM_FIELDS = 14


class ImageRecord:
	def __init__(self, path=None, file_sz=None, file_date=None,aAttr=None, dAttr=None):
		def GetAttrSafe(aAttributes, n, szType):
			try:
				val = aAttributes[n]
			except:
				return (None)
				
			if szType == 'str':
				return (val)
			elif szType == 'int':
				try:
					return (int(val))
				except:
					return (None)
			elif szType == 'datetime':
				try:
					return (datetime.datetime.fromtimestamp(int(val)))
				except:
					return (None)
			elif szType == 'bool':
				try:
					return (bool(val))
				except:
					return (False)
			else:
				return (val)
		#set all attributes to None
		self.path = None
		self.file_sz = None
		self.dt = None
		self.make = None
		self.model = None
		self.exif_ver = None
		self.width = None
		self.height = None
		self.orientation = None
		self.epoch_day = None
		self.year_day = None
		self.likes = None
		self.favorite = False
		self.last_played = None

		if aAttr is not None:
			self.path = GetAttrSafe(aAttr,0,'str')
			self.file_sz = GetAttrSafe(aAttr,1,'int')
			self.dt = GetAttrSafe(aAttr,2,'datetime')
			self.make = GetAttrSafe(aAttr,3,'str')
			self.model = GetAttrSafe(aAttr,4,'str')
			self.exif_ver = GetAttrSafe(aAttr,5,'int')
			self.width = GetAttrSafe(aAttr,6,'int')
			self.height = GetAttrSafe(aAttr,7,'int')
			self.orientation = GetAttrSafe(aAttr,8,'int')
			self.epoch_day = GetAttrSafe(aAttr,9,'int')
			self.year_day = GetAttrSafe(aAttr,10,'int')
			self.likes = GetAttrSafe(aAttr,11,'int')
			self.favorite = GetAttrSafe(aAttr,12,'bool')
			self.last_played = GetAttrSafe(aAttr,13,'datetime')
		elif dAttr is not None:
			self.path = GetAttrSafe(dAttr,'path','str')
			self.file_sz = GetAttrSafe(dAttr,'file_sz','int')
			self.dt = GetAttrSafe(dAttr,'dt','datetime')
			self.make = GetAttrSafe(dAttr,'make','str')
			self.model = GetAttrSafe(dAttr,'model','str')
			self.exif_ver = GetAttrSafe(dAttr,'exif_ver','int')
			self.width = GetAttrSafe(dAttr,'width','int')
			self.height = GetAttrSafe(dAttr,'height','int')
			self.orientation = GetAttrSafe(dAttr,'orientation','int')
			self.epoch_day = GetAttrSafe(dAttr,'epoch_day','int')
			self.year_day = GetAttrSafe(dAttr,'year_day','int')			
			self.likes = GetAttrSafe(dAttr,'likes','int')
			self.favorite = GetAttrSafe(dAttr,'favorite','bool')
			self.last_played = GetAttrSafe(dAttr,'last_played','datetime')
		else:
			self.path = path
			if file_sz is not None:
				self.file_sz = int(file_sz)
			if file_date is not None:
				self.dt = float(file_date)
		
		if self.dt is not None:
			if self.epoch_day is None or self.year_day is None:
				self.PopStdDays()
				
		if self.likes is None:
			self.likes = 0
			
	def __repr__(self):
		return(f"{self.path, self.file_sz,self.dt,self.make,self.model,self.exif_ver,self.width,self.height,self.orientation,self.epoch_day,self.year_day}")
		
	def __iter__(self):
		return iter([ self.path , \
						self.file_sz , \
						self.dt , \
						self.make , \
						self.model , \
						self.exif_ver , \
						self.width , \
						self.height , \
						self.orientation , \
						self.epoch_day , \
						self.year_day ])
						
	def PopStdDays(self):
		if self.dt is None:
			return()
		(self.year_day,self.epoch_day) = GetStandardDays(self.dt)
		return()
		

	def PopAttr(self,rootDir=''):
		#Populate Object Attributes from Image File
		photoPath = rootDir + self.path
		#open image file
		#get EXIF information
		#get width, height from image
		#validate
		img = Image.open(photoPath)

		try:
			info = img._getexif()
		except AttributeError:
			logging.warn(f"no EXIF: {photoPath}")
			return
		dTags = {}
		if info is not None:
			for tag, value in info.items():
				decoded = TAGS.get(tag, tag)
				dTags[str(decoded).lower()] = value
				
		#populate attributes
		try:
			self.make = dTags['make'].replace("\x00","")
		except:
			pass
		try:
			self.model = dTags['model'].replace("\x00","")
		except:
			pass
		try:			
			self.width = dTags['exifimagewidth']
		except:
			pass
		try:			
			self.height = dTags['exifimageheight']
		except:
			pass
		try:			
			self.exif_ver = dTags['exifversion'].decode('utf-8')
		except:
			pass
		try:			
			self.orientation = dTags['orientation']
		except:
			pass
			

	#add id as set at runtime
	def GetJsonId(self,nId):
		dDict = self.__dict__
		if dDict['dt'] is not None:
			dDict['dt'] = dDict['dt'].timestamp()
		dDict['id'] = nId
		return(json.dumps(dDict,skipkeys=True))

def GetStandardDays(dt):
	if dt is None:
		return()
	#given datetime return number of days from 1 Jan, 1990 and day of year 
	SECS_IN_DAY = 86400
	dtEPOCH_DAY = datetime.datetime.strptime('1990-01-01 00:00:00', "%Y-%m-%d %H:%M:%S")
	epoch_day = int( (dt-dtEPOCH_DAY).total_seconds()/SECS_IN_DAY )

	#get day of year 
	year_day = dt.timetuple().tm_yday 
	if (dt.year % 100 == 0) & (year_day > 59):
		year_day -= 1
	return(year_day,epoch_day)
	
def DictInc(d,k):
	if k in d:
		d[k]+=1
	else:
		d[k]=1
