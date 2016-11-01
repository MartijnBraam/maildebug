"""
This code does horrible things. It guesses config locations and tries to work out where stuff is located
"""
import glob


def find_mail_log():
    logs = glob.glob('/var/log/mail.log*')
    logs.sort()
    logs.sort(key=len)
    return logs


def find_postfix_config():
    return '/etc/postfix/main.cf'


def find_user_maildir(domain, user):
    return '/var/mail/vhosts/{domain}/{user}'.format(domain=domain, user=user)
