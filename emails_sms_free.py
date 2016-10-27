#!/usr/bin/env python
# -*- coding:utf-8-*-

from __future__ import print_function

import email
import hashlib
import imaplib
import os.path
import requests
import sys
import time

try:
    # For python 3
    import json
except ImportError:
    # For python 2
    import simplejson as json
    print('Error importing lib as python3, switching to python 2 libraries')

msg_ids = {}


def get_subject(subject_header):
    tmp = email.header.decode_header(subject_header)[0]
    if tmp[1] is None:
        return str(tmp[0])
    else:
        try:
            return tmp[0].decode(tmp[1])
        except LookupError:
            return "--Unable to fetch subject--"


def send(url, user, password, msg, i=0):
    try:
        r = requests.get(url, params={'user': user, 'pass': password, 'msg': msg}, verify=False)
        if r.status_code == 200:
            return True
        elif r.status_code == 400:
            print('Un paramètre obligatoire est manquant.')
            return False
        elif r.status_code == 402:
            if i < 3:
                print('Trop de SMS ont été envoyés en trop peu de temps, ' +
                      'le script réessayera dans 30 secondes.')
                time.sleep(30)
                send(url, user, password, msg, i+1)
            else:
                print('Impossible d\'envoyer le message dans la dernière minute ' +
                      'et demie.')
                return False
        elif r.status_code == 403:
            print('Identifiants incorrects ou service non activé.')
            return False
        elif r.status_code == 500:
            print('Erreur côté serveur.')
            return False
    except requests.exceptions.RequestException:
        return False


def get_emails(imap_server, imap_user, imap_password, inbox, uid):
    global msg_ids

    print('Connecting to '+imap_server+'… ', end='')
    conn = imaplib.IMAP4_SSL(imap_server)
    print('Connected')
    to_send = []

    try:
        print('Logging as '+imap_user+'… ', end='')
        retcode, capabilities = conn.login(imap_user, imap_password)
    except:
        print('Failed')
        print(sys.exc_info()[1])
        sys.exit(1)
    print('Logged in')

    try:
        conn.select(inbox, readonly=True)
        typ, tmp_msg_ids = conn.uid('search', None, 'ALL')
        tmp_msg_ids = [i.decode('utf-8')
                       for i in tmp_msg_ids[0].split()]
        if uid in msg_ids:
            diff_msg_ids = [i
                            for i in tmp_msg_ids
                            if i not in msg_ids[uid]]
        else:
            diff_msg_ids = tmp_msg_ids
        msg_ids[uid] = tmp_msg_ids
        if len(diff_msg_ids) == 0:
            print("\tNo new emails")
        else:
            for i in diff_msg_ids:
                typ, msg_data = conn.uid('fetch', i, '(RFC822)')
                msg_parsed = email.message_from_bytes(msg_data[0][1])
                text = ""
                for part in msg_parsed.walk():
                    charset = charset = part.get_content_charset()
                    if note charset:
                        # We cannot know the character set, so return decoded "something"
                        text = part.get_payload(decode=True)
                        continue

                    if part.get_content_type() == 'text/plain':
                        text = part.get_payload(decode=True).decode(str(charset))
                        break
                subject = get_subject(msg_parsed['Subject'])
                print("\tNew email from "+msg_parsed['From'] +
                      " : "+subject)
                to_send.append({'server_uid': uid,
                                'id': i,
                                'from': msg_parsed['From'],
                                'subject': subject,
                                'content': text})
        return to_send
    finally:
        try:
            conn.close()
        except:
            pass
        conn.logout()


if __name__ == '__main__':
    # EDIT BELOW ACCORDING TO YOUR NEEDS
    imap_servers = [{'server': 'SERVER',
                     'login': 'LOGIN',
                     'password': 'PASS',
                     'inbox': 'INBOX'}]
    save_path = os.path.expanduser('~/.emails_sms_free.json')
    debug = False
    url = "https://smsapi.free-mobile.fr/sendmsg"
    user = 'IDENT'
    password = 'PASS'
    # YOU SHOULD NOT HAVE TO EDIT BELOW

    url = url.replace('{$user}', user)
    url = url.replace('{$pass}', password)

    if os.path.isfile(save_path):
        with open(save_path, 'r') as fh:
            msg_ids = json.load(fh)

    to_send = []
    for imap_server in imap_servers:
        to_send.extend(get_emails(imap_server['server'],
                                  imap_server['login'],
                                  imap_server['password'],
                                  imap_server['inbox'],
                                  hashlib.md5((imap_server['server']+imap_server['login']).encode('utf-8')).hexdigest()))

    if debug:
        print("\nNew emails to send via SMS:")
        print("\t", to_send)

    i = 1
    for data in to_send:
        msg = ('New email from '+data['from']+'\n' +
               data['subject']+'\n' +
               str(data['content'][:700])+'...')
        if send(url, user, password, msg):
            print('Sent '+str(i)+'/'+str(len(to_send)))
        else:
            msg_ids[data['server_uid']].remove(data['id'])
            print('Email '+str(i)+'/'+str(len(to_send))+' : Unable to send the text ' +
                  'message, remove this email from parsed list.')
        i += 1

    with open(save_path, 'w') as fh:
        json.dump(msg_ids, fh)
