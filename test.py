#!/usr/bin/env python3
import emails_sms_free 

if __name__ == '__main__':
	url = "https://smsapi.free-mobile.fr/sendmsg"
	user= raw_input("Please enter usr: ")
	print "you entered", user
	password= raw_input("Please enter password: ")
	print "you entered", password
	msg = raw_input("Please enter msg: ")
	print "you entered", msg
	send(url, user, password, msg, 1)
