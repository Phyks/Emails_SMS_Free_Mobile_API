#!/usr/bin/env python

from builtins import input #pour rendre input python2 and 3 compatible
import emails_sms_free 


if __name__ == '__main__':
	url = "https://smsapi.free-mobile.fr/sendmsg"
	user= input("Please enter usr: ")
	print("you entered" + str(user))
	password= input("Please enter password: ")
	print("you entered"+ str(password))
	msg = input("Please enter msg: ")
	print("you entered"+ str(msg))
	end = emails_sms_free.send(url, user, password, msg)
