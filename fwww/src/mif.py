from PIL import Image, ImageTk
from PIL.ExifTags import TAGS
import logging

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
	def __init__(self, path=None, file_sz=None, file_date=None,aAttr=None):
		def GetAttrSafe(aAttributes, n, szType):
			try:
				val = aAttr[n]
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
					return (float(val))
				except:
					return (None)
			else:
				return (val)

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
		if aAttr is None:
			self.path = path
			if file_sz is not None:
				self.file_sz = int(file_sz)
			if file_date is not None:
				self.dt = float(file_date)
		else:
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
		try:
			self.make = dTags['make'].replace("\x00","")
			self.model = dTags['model'].replace("\x00","")
			self.width = dTags['exifimagewidth']
			self.height = dTags['exifimageheight']
			self.exif_ver = dTags['exifversion'].decode('utf-8')
			self.orientation = dTags['orientation']
		except:
			pass



