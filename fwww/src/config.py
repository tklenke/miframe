#rename this file to config.py and update with your information

flip_after_millisecs = 2400
pillow_image_buffer_size = 24000000

server_name = "raspberry"
server_ip = "10.0.0.33"

#photo library (end with /)
photo_root_path = "/media/sf_Our_Pictures/"
photo_fallback_path = "/home/admin/Pictures/fallback/"
dupes_directory = "zz_dupes"

#fully qualified path for these two
image_records_file_read = "/home/admin/projects/img_recs.csv"
image_records_file_write = "/home/admin/projects/img_recs.csv"

#will recursively dig into your photo directory looking for photos
recursive_dirs = True

#add additional directories to skip by adding in quotes
skip_directories =['.','..','klen_our_pictures_catalog']
# ~ skip_directories =['.','..','klen_our_pictures_catalog','002','019','004'\
		# ~ ,'006','007','008','010','011','012','013','014','015','016','017','018','019']

